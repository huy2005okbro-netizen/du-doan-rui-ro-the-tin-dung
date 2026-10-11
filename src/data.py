"""Download, validate, document, and split the UCI credit-card-default data.

This module intentionally does not recode values or remove records.  It reports
unexpected codes and duplicates so that any later policy decision is explicit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import date, timezone, datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = ROOT / "reports"
CONFIG_PATH = ROOT / "config.json"

UCI_PAGE_URL = "https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients"
UCI_ARCHIVE_URL = "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"
UCI_LICENSE = "CC BY 4.0"
EXPECTED_COLUMNS = [
    "ID", "LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE",
    "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6",
    "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
    "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",
    "default_payment_next_month",
]
PAY_COLUMNS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_data(force: bool = False) -> Path:
    """Download the official UCI archive and extract only its supplied data file."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    archive = RAW_DIR / "uci_default_of_credit_card_clients.zip"
    metadata_path = RAW_DIR / "source_metadata.json"
    if archive.exists() and not force:
        return extract_official_file(archive)

    request = Request(UCI_ARCHIVE_URL, headers={"User-Agent": "phase-1-credit-risk-project/1.0"})
    with urlopen(request, timeout=60) as response, archive.open("wb") as handle:
        shutil.copyfileobj(response, handle)

    extracted = extract_official_file(archive)
    metadata = {
        "source_page": UCI_PAGE_URL,
        "download_url": UCI_ARCHIVE_URL,
        "license": UCI_LICENSE,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_filename": archive.name,
        "archive_sha256": sha256(archive),
        "data_filename": extracted.name,
        "data_sha256": sha256(extracted),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return extracted


def extract_official_file(archive: Path) -> Path:
    with zipfile.ZipFile(archive) as zipped:
        members = [member for member in zipped.namelist() if member.lower().endswith((".xls", ".xlsx", ".csv"))]
        if len(members) != 1:
            raise ValueError(f"Expected one tabular data file in {archive.name}; found {members}")
        member = members[0]
        destination = RAW_DIR / Path(member).name
        if not destination.exists():
            with zipped.open(member) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
    return destination


def find_local_data_file() -> Path:
    candidates = sorted(path for path in RAW_DIR.glob("*") if path.suffix.lower() in {".xls", ".xlsx", ".csv"})
    if len(candidates) != 1:
        raise FileNotFoundError(
            "Expected exactly one .xls, .xlsx, or .csv file in data/raw/. "
            "Run `python -m src.data download`, or place the official UCI file there."
        )
    return candidates[0]


def read_dataset(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
    else:
        # The official XLS has a title row followed by a header row.
        frame = pd.read_excel(path, header=1)
    frame.columns = [str(column).strip() for column in frame.columns]
    # UCI's XLS labels the target "default payment next month".
    frame = frame.rename(columns={"default payment next month": "default_payment_next_month"})
    return frame


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def validate_dataset(frame: pd.DataFrame) -> dict[str, Any]:
    """Return an audit; do not mutate the provided frame."""
    config = load_config()
    target = config["target_column"]
    unexpected_columns = sorted(set(frame.columns) - set(EXPECTED_COLUMNS))
    missing_columns = sorted(set(EXPECTED_COLUMNS) - set(frame.columns))
    code_rules = {
        "SEX": {1, 2},
        "EDUCATION": {1, 2, 3, 4},
        "MARRIAGE": {1, 2, 3},
        target: {0, 1},
    }
    unusual_codes: dict[str, dict[str, Any]] = {}
    for column, allowed in code_rules.items():
        if column in frame:
            values = set(frame[column].dropna().unique())
            unexpected = sorted(values - allowed)
            unusual_codes[column] = {
                "allowed_codes_documented": sorted(allowed),
                "observed_codes": sorted(_json_value(item) for item in values),
                "unexpected_codes": [_json_value(item) for item in unexpected],
                "unexpected_count": int(frame[column].isin(unexpected).sum()),
            }
    pay_ranges = {}
    for column in PAY_COLUMNS:
        if column in frame:
            observed = frame[column].dropna()
            pay_ranges[column] = {
                "min": _json_value(observed.min()),
                "max": _json_value(observed.max()),
                "observed_codes": sorted(_json_value(item) for item in observed.unique()),
            }
    return {
        "row_count": int(len(frame)),
        "column_count": int(frame.shape[1]),
        "columns": list(frame.columns),
        "missing_expected_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "missing_values": {column: int(count) for column, count in frame.isna().sum().items()},
        "duplicate_id_count": int(frame["ID"].duplicated().sum()) if "ID" in frame else None,
        "duplicate_full_record_count": int(frame.duplicated().sum()),
        "target_distribution": (
            {str(_json_value(key)): int(value) for key, value in frame[target].value_counts(dropna=False).sort_index().items()}
            if target in frame else {}
        ),
        "unusual_codes": unusual_codes,
        "pay_status_observed_ranges": pay_ranges,
        "handling_policy": "No records are deleted and no category codes are recoded in phase 1. "
                           "Undocumented codes are retained and reported; modelling encodes categories without assuming a replacement value.",
    }


def write_validation_report(frame: pd.DataFrame) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    destination = REPORTS_DIR / "data_quality.json"
    destination.write_text(json.dumps(validate_dataset(frame), ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def create_splits(frame: pd.DataFrame) -> dict[str, Path]:
    config = load_config()
    target = config["target_column"]
    if set(frame[target].dropna().unique()) - {0, 1}:
        raise ValueError("Target must contain only 0 and 1 before creating stratified splits.")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    train_and_validation, test = train_test_split(
        frame, test_size=config["split"]["test_size"], stratify=frame[target], random_state=config["random_state"]
    )
    validation_fraction_of_remaining = config["split"]["validation_size"] / (
        config["split"]["train_size"] + config["split"]["validation_size"]
    )
    train, validation = train_test_split(
        train_and_validation,
        test_size=validation_fraction_of_remaining,
        stratify=train_and_validation[target],
        random_state=config["random_state"],
    )
    outputs: dict[str, Path] = {}
    for name, split in {"train": train, "validation": validation, "test": test}.items():
        split_path = PROCESSED_DIR / f"{name}.csv"
        split.sort_values("ID").to_csv(split_path, index=False)
        outputs[name] = split_path
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_state": config["random_state"],
        "target_column": target,
        "id_column": config["id_column"],
        "split_proportions": config["split"],
        "source_rows": int(len(frame)),
        "splits": {
            name: {"rows": int(len(split)), "ids": [int(value) for value in sorted(split["ID"].tolist())],
                   "target_distribution": {str(key): int(value) for key, value in split[target].value_counts().sort_index().items()}}
            for name, split in {"train": train, "validation": validation, "test": test}.items()
        },
        "note": "The test split is created and frozen here. Do not use it for model, parameter, or threshold selection in phase 1.",
    }
    manifest_path = PROCESSED_DIR / "split_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    outputs["manifest"] = manifest_path
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download", "validate", "split", "prepare"])
    parser.add_argument("--force", action="store_true", help="Re-download the UCI archive.")
    arguments = parser.parse_args()
    if arguments.command == "download":
        path = download_data(force=arguments.force)
        print(f"Official UCI data available at {path.relative_to(ROOT)}")
        return
    if arguments.command == "prepare":
        path = download_data(force=arguments.force)
    else:
        path = find_local_data_file()
    frame = read_dataset(path)
    report = write_validation_report(frame)
    print(f"Validation report written to {report.relative_to(ROOT)}")
    if arguments.command in {"split", "prepare"}:
        outputs = create_splits(frame)
        print("Frozen split files:")
        for name, output in outputs.items():
            print(f"  {name}: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
