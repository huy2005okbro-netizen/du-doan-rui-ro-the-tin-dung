"""Feature definitions and leakage-safe preprocessing for phase 1."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]

CONTINUOUS_COLUMNS = [
    "LIMIT_BAL", "AGE", "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
    "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",
]
CATEGORICAL_COLUMNS = ["SEX", "EDUCATION", "MARRIAGE", "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]


def load_config() -> dict:
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def feature_columns() -> list[str]:
    return CONTINUOUS_COLUMNS + CATEGORICAL_COLUMNS


def split_xy(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    config = load_config()
    required = set(feature_columns() + [config["target_column"], config["id_column"]])
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    # ID is deliberately excluded: it is an identifier, not an available credit-risk feature.
    return frame.loc[:, feature_columns()].copy(), frame[config["target_column"]].astype(int).copy()


def build_preprocessor() -> ColumnTransformer:
    """Return an unfitted transformer; `fit` happens only inside model training on train."""
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("one_hot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("continuous", numeric_pipeline, CONTINUOUS_COLUMNS),
        ("categorical", categorical_pipeline, CATEGORICAL_COLUMNS),
    ], remainder="drop")
