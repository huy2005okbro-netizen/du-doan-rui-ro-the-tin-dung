"""Build non-sensitive dashboard aggregates and validation ranges for the web app."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.experiments import probability_metrics
from src.features import CATEGORICAL_COLUMNS, CONTINUOUS_COLUMNS, load_config, split_xy

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
STATIC = APP / "static"


def build_web_data() -> None:
    config = load_config()
    STATIC.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(ROOT / "data" / "processed" / "train.csv")
    validation = pd.read_csv(ROOT / "data" / "processed" / "validation.csv")
    ranges = {
        "continuous": {column: {"min": int(train[column].min()), "max": int(train[column].max())} for column in CONTINUOUS_COLUMNS},
        "categorical_observed": {column: sorted(int(value) for value in train[column].dropna().unique()) for column in CATEGORICAL_COLUMNS},
    }
    (APP / "training_ranges.json").write_text(json.dumps(ranges, ensure_ascii=False, indent=2), encoding="utf-8")

    pipeline = joblib.load(ROOT / "models" / "selected_phase2_pipeline.joblib")
    x_validation, y_validation = split_xy(validation)
    probabilities = pipeline.predict_proba(x_validation)[:, 1]
    costs = config["phase2"]["cost_matrix_assumed"]
    tradeoff = []
    for threshold in np.arange(0.05, 0.701, 0.01):
        metrics = probability_metrics(y_validation, probabilities, float(round(threshold, 2)))
        total_cost = int(metrics["fp"]) * costs["false_positive"] + int(metrics["fn"]) * costs["false_negative"]
        tradeoff.append({"threshold": metrics["threshold"], "precision": metrics["precision_default"], "recall": metrics["recall_default"], "f1": metrics["f1_default"], "total_cost": total_cost, "cost_per_customer": total_cost / len(validation)})
    final = json.loads((ROOT / "reports" / "final_test_evaluation.json").read_text(encoding="utf-8"))
    comparison = pd.read_csv(ROOT / "reports" / "phase2_validation_model_comparison.csv").to_dict(orient="records")
    audit = pd.read_csv(ROOT / "reports" / "final_test_group_audit.csv").replace({np.nan: None}).to_dict(orient="records")
    freeze = json.loads((ROOT / "models" / "final_selection_freeze.json").read_text(encoding="utf-8"))
    dashboard = {
        "official_threshold": freeze["threshold"], "cost_matrix_assumed": freeze["cost_matrix_assumed"],
        "validation_models": comparison, "test_metrics": final["metrics"], "test_audit": audit,
        "validation_tradeoff": tradeoff, "model_version": freeze["pipeline_sha256"][:12],
        "note": "Dashboard trade-off is calculated only from validation aggregates. It does not modify the frozen model or final test decision.",
    }
    (STATIC / "dashboard_data.json").write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    build_web_data()
    print("Web dashboard data and training ranges created.")
