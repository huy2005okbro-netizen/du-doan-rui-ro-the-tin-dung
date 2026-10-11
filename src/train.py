"""Train and persist the phase-1 logistic-regression baseline using only train data."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.features import build_preprocessor, feature_columns, load_config, split_xy

ROOT = Path(__file__).resolve().parents[1]


def train_logistic_baseline() -> Path:
    config = load_config()
    train_path = ROOT / "data" / "processed" / "train.csv"
    if not train_path.exists():
        raise FileNotFoundError("Frozen train split is absent. Run `python -m src.data prepare` first.")
    train = pd.read_csv(train_path)
    x_train, y_train = split_xy(train)
    pipeline = Pipeline([
        ("preprocess", build_preprocessor()),
        ("model", LogisticRegression(max_iter=2000, random_state=config["random_state"], class_weight=None)),
    ])
    pipeline.fit(x_train, y_train)

    models_dir = ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    model_path = models_dir / "logistic_baseline.joblib"
    joblib.dump(pipeline, model_path)
    metadata = {
        "model": "LogisticRegression",
        "class_weight": None,
        "random_state": config["random_state"],
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "training_split": "train",
        "training_rows": int(len(train)),
        "target_column": config["target_column"],
        "excluded_identifier": config["id_column"],
        "feature_columns": feature_columns(),
        "scikit_learn_version": sklearn.__version__,
        "selection_note": "This is a phase-1 baseline. It has not used the frozen test split.",
    }
    (models_dir / "logistic_baseline_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return model_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(f"Saved logistic baseline to {train_logistic_baseline().relative_to(ROOT)}")


if __name__ == "__main__":
    main()
