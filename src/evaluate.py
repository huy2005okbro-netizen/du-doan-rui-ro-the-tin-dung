"""Evaluate phase-1 baselines on validation only; never read the test split."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay, accuracy_score, average_precision_score, brier_score_loss,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
)

from src.features import load_config, split_xy

ROOT = Path(__file__).resolve().parents[1]


def safe_metric(metric: Callable, y_true: pd.Series, y_score: np.ndarray, **kwargs: object) -> float | None:
    """Return null instead of silently inventing a metric when it is undefined."""
    try:
        return float(metric(y_true, y_score, **kwargs))
    except ValueError:
        return None


def classification_metrics(y_true: pd.Series, y_pred: np.ndarray, probabilities: np.ndarray) -> dict[str, float | int | None]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_default": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall_default": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "f1_default": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        # average_precision_score is the area under the step-wise precision-recall curve (AP / PR-AUC).
        "pr_auc_average_precision": safe_metric(average_precision_score, y_true, probabilities),
        "roc_auc": safe_metric(roc_auc_score, y_true, probabilities),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "tn": int(confusion_matrix(y_true, y_pred, labels=[0, 1])[0, 0]),
        "fp": int(confusion_matrix(y_true, y_pred, labels=[0, 1])[0, 1]),
        "fn": int(confusion_matrix(y_true, y_pred, labels=[0, 1])[1, 0]),
        "tp": int(confusion_matrix(y_true, y_pred, labels=[0, 1])[1, 1]),
    }


def save_confusion_matrix(y_true: pd.Series, y_pred: np.ndarray, model_name: str) -> Path:
    figures = ROOT / "reports" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    display = ConfusionMatrixDisplay.from_predictions(y_true, y_pred, display_labels=["non-default", "default"], cmap="Blues")
    display.ax_.set_title(f"Validation confusion matrix — {model_name}")
    output = figures / f"validation_confusion_matrix_{model_name}.png"
    display.figure_.tight_layout()
    display.figure_.savefig(output, dpi=150)
    plt.close(display.figure_)
    return output


def evaluate_validation() -> pd.DataFrame:
    config = load_config()
    validation_path = ROOT / "data" / "processed" / "validation.csv"
    model_path = ROOT / "models" / "logistic_baseline.joblib"
    if not validation_path.exists() or not model_path.exists():
        raise FileNotFoundError("Validation split or saved model absent. Run prepare and train first.")
    validation = pd.read_csv(validation_path)
    x_validation, y_validation = split_xy(validation)
    threshold = config["decision_threshold"]
    predictions: dict[str, tuple[np.ndarray, np.ndarray]] = {
        "always_non_default": (np.zeros(len(y_validation), dtype=int), np.zeros(len(y_validation), dtype=float)),
    }
    pipeline = joblib.load(model_path)
    logistic_probabilities = pipeline.predict_proba(x_validation)[:, 1]
    predictions["logistic_regression_unweighted"] = ((logistic_probabilities >= threshold).astype(int), logistic_probabilities)

    rows = []
    for name, (predicted, probabilities) in predictions.items():
        row = {"model": name, "evaluation_split": "validation", "threshold": threshold if name != "always_non_default" else None}
        row.update(classification_metrics(y_validation, predicted, probabilities))
        rows.append(row)
        save_confusion_matrix(y_validation, predicted, name)
    results = pd.DataFrame(rows)
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    results.to_csv(reports / "validation_baseline_metrics.csv", index=False)
    (reports / "validation_baseline_metrics.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(evaluate_validation().to_string(index=False))


if __name__ == "__main__":
    main()
