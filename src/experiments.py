"""Phase-2 model comparison using frozen train/validation data only.

The test split is deliberately never opened in this module.  Hyperparameters are
selected with stratified CV inside train; the held-out validation split supports
the model, calibration, and threshold decisions documented in the report.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    auc,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline

from src.features import build_preprocessor, feature_columns, load_config, split_xy

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
MODELS = ROOT / "models"


def metric_or_none(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def probability_metrics(y_true: pd.Series, probabilities: np.ndarray, threshold: float) -> dict[str, float | int | None]:
    """Metrics for the default class; undefined rates are represented by None."""
    predicted = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    precision_curve, recall_curve, _ = precision_recall_curve(y_true, probabilities)
    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, predicted)),
        "precision_default": metric_or_none(int(tp), int(tp + fp)),
        "recall_default": metric_or_none(int(tp), int(tp + fn)),
        "f1_default": float(f1_score(y_true, predicted, pos_label=1, zero_division=0)),
        "pr_auc_average_precision": float(average_precision_score(y_true, probabilities)),
        # This is recorded separately because it is a trapezoidal PR-curve integral, not AP.
        "pr_auc_trapezoidal": float(auc(recall_curve[::-1], precision_curve[::-1])),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def assumed_cost(metrics: dict[str, float | int | None], cost_matrix: dict[str, int]) -> tuple[int, float]:
    total = int(metrics["tn"]) * cost_matrix["true_negative"] + int(metrics["fp"]) * cost_matrix["false_positive"]
    total += int(metrics["fn"]) * cost_matrix["false_negative"] + int(metrics["tp"]) * cost_matrix["true_positive"]
    count = int(metrics["tn"]) + int(metrics["fp"]) + int(metrics["fn"]) + int(metrics["tp"])
    return total, total / count


def build_pipeline(class_weight: str | None, random_state: int) -> Pipeline:
    return Pipeline([
        ("preprocess", build_preprocessor()),
        # liblinear is deterministic for this binary, modest-width design matrix and keeps CV practical.
        ("model", LogisticRegression(max_iter=1000, random_state=random_state, class_weight=class_weight, solver="liblinear")),
    ])


def fit_cv_models(x_train: pd.DataFrame, y_train: pd.Series, config: dict[str, Any]) -> tuple[dict[str, GridSearchCV], pd.DataFrame]:
    phase2 = config["phase2"]
    # A single splitter object gives the same deterministic folds to both candidate models.
    splitter = StratifiedKFold(n_splits=phase2["cv_folds"], shuffle=True, random_state=config["random_state"])
    fitted: dict[str, GridSearchCV] = {}
    rows: list[dict[str, Any]] = []
    for name, class_weight in [("logistic_unweighted", None), ("logistic_balanced", "balanced")]:
        search = GridSearchCV(
            estimator=build_pipeline(class_weight, config["random_state"]),
            param_grid={"model__C": phase2["c_grid"]},
            scoring=phase2["cv_scoring"],
            cv=splitter,
            refit=True,
            n_jobs=1,
            return_train_score=False,
        )
        search.fit(x_train, y_train)
        fitted[name] = search
        for index, candidate_c in enumerate(search.cv_results_["param_model__C"]):
            rows.append({
                "model": name,
                "class_weight": "balanced" if class_weight else "none",
                "C": float(candidate_c),
                "cv_scoring": phase2["cv_scoring"],
                "mean_cv_average_precision": float(search.cv_results_["mean_test_score"][index]),
                "std_cv_average_precision": float(search.cv_results_["std_test_score"][index]),
                "rank": int(search.cv_results_["rank_test_score"][index]),
            })
    return fitted, pd.DataFrame(rows).sort_values(["model", "rank", "C"])


def save_reliability_diagram(y_validation: pd.Series, scores: dict[str, np.ndarray], bins: int) -> pd.DataFrame:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, axis = plt.subplots(figsize=(7, 6))
    axis.plot([0, 1], [0, 1], "k--", label="perfect calibration")
    rows: list[dict[str, Any]] = []
    for name, probabilities in scores.items():
        observed, predicted = calibration_curve(y_validation, probabilities, n_bins=bins, strategy="uniform")
        axis.plot(predicted, observed, marker="o", label=name)
        rows.extend({"model": name, "mean_predicted_probability": float(p), "fraction_default": float(o)} for p, o in zip(predicted, observed))
    axis.set_xlabel("Mean predicted probability")
    axis.set_ylabel("Observed default frequency")
    axis.set_title("Validation reliability diagram — raw model probabilities")
    axis.legend()
    axis.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "validation_reliability_diagram.png", dpi=150)
    plt.close(fig)
    return pd.DataFrame(rows)


def threshold_rows(y_validation: pd.Series, probabilities: np.ndarray, config: dict[str, Any]) -> tuple[pd.DataFrame, float, float]:
    phase2 = config["phase2"]
    costs = phase2["cost_matrix_assumed"]
    theoretical = costs["false_positive"] / (costs["false_positive"] + costs["false_negative"])
    grid = np.arange(0.0, 1.0 + phase2["threshold_grid_step"] / 2, phase2["threshold_grid_step"])
    candidates = []
    for threshold in grid:
        metrics = probability_metrics(y_validation, probabilities, float(threshold))
        total_cost, average_cost = assumed_cost(metrics, costs)
        candidates.append((float(threshold), total_cost, average_cost))
    candidate_table = pd.DataFrame(candidates, columns=["threshold", "total_assumed_cost", "assumed_cost_per_customer"])
    chosen = float(candidate_table.sort_values(["total_assumed_cost", "threshold"], ascending=[True, False]).iloc[0]["threshold"])
    display_thresholds = [0.5, theoretical, chosen]
    if len({round(item, 10) for item in display_thresholds}) < 3:
        display_thresholds.append(0.3 if all(abs(item - 0.3) > 1e-10 for item in display_thresholds) else 0.7)
    output_rows: list[dict[str, Any]] = []
    for threshold in dict.fromkeys(display_thresholds):
        metrics = probability_metrics(y_validation, probabilities, float(threshold))
        total_cost, average_cost = assumed_cost(metrics, costs)
        metrics.update({"threshold_role": (
            "fixed_0.5" if threshold == 0.5 else "cost_theoretical" if threshold == theoretical else "validation_cost_minimum" if threshold == chosen else "additional_comparator"
        ), "total_assumed_cost": total_cost, "assumed_cost_per_customer": average_cost})
        output_rows.append(metrics)
    return pd.DataFrame(output_rows), chosen, theoretical


def save_threshold_confusion_matrices(y_validation: pd.Series, probabilities: np.ndarray, thresholds: pd.DataFrame) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    for row in thresholds.itertuples(index=False):
        predicted = (probabilities >= row.threshold).astype(int)
        display = ConfusionMatrixDisplay.from_predictions(y_validation, predicted, display_labels=["non-default", "default"], cmap="Blues")
        display.ax_.set_title(f"Validation confusion matrix — threshold {row.threshold:.3f}")
        display.figure_.tight_layout()
        display.figure_.savefig(FIGURES / f"validation_confusion_matrix_threshold_{row.threshold:.3f}.png", dpi=150)
        plt.close(display.figure_)


def group_audit(validation: pd.DataFrame, probabilities: np.ndarray, threshold: float, config: dict[str, Any]) -> pd.DataFrame:
    target = config["target_column"]
    evaluated = validation.copy()
    evaluated["_prediction"] = (probabilities >= threshold).astype(int)
    evaluated["_probability"] = probabilities
    rows: list[dict[str, Any]] = []
    for group_column in ["SEX", "EDUCATION", "MARRIAGE"]:
        for value, group in evaluated.groupby(group_column, dropna=False, sort=True):
            y_true, y_pred = group[target].astype(int), group["_prediction"].astype(int)
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
            positives, negatives, predicted_positive = int(tp + fn), int(tn + fp), int(tp + fp)
            rows.append({
                "group_column": group_column,
                "group_value": str(value),
                "sample_count": int(len(group)),
                "default_count": int(y_true.sum()),
                "recall_tpr": metric_or_none(int(tp), positives),
                "fnr": metric_or_none(int(fn), positives),
                "fpr": metric_or_none(int(fp), negatives),
                "precision": metric_or_none(int(tp), predicted_positive),
                "brier_score": float(brier_score_loss(y_true, group["_probability"])),
                "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
                "note": "Small group; interpret with caution." if len(group) < 100 else "",
            })
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, columns: list[str], digits: int = 4) -> str:
    view = frame.loc[:, columns].copy()
    for column in view.columns:
        view[column] = view[column].map(lambda value: "undefined" if pd.isna(value) else f"{value:.{digits}f}" if isinstance(value, (float, np.floating)) else str(value))
    return "| " + " | ".join(view.columns) + " |\n| " + " | ".join(["---"] * len(view.columns)) + " |\n" + "\n".join("| " + " | ".join(row) + " |" for row in view.to_numpy())


def write_reports(
    cv_results: pd.DataFrame, comparison: pd.DataFrame, thresholds: pd.DataFrame, audit: pd.DataFrame,
    chosen_model: str, chosen_threshold: float, theoretical_threshold: float, config: dict[str, Any],
) -> None:
    REPORTS.mkdir(exist_ok=True)
    phase2 = config["phase2"]
    cost = phase2["cost_matrix_assumed"]
    report = f"""# Báo cáo thí nghiệm Giai đoạn 2

Ngày chạy (UTC): {datetime.now(timezone.utc).isoformat()}

## Thiết kế không rò rỉ

Tập train đóng băng được dùng cho Stratified 5-fold CV (`random_state=42`, shuffle). Mỗi candidate là một Pipeline gồm imputer, scaler/one-hot encoder và Logistic Regression; do đó mọi bước học dữ liệu được fit lại trong từng fold train. Validation chỉ dùng sau CV để so sánh mô hình, xác suất và ngưỡng. Tệp test không được mở bởi module này.

## Chọn C bằng CV trên train

{markdown_table(cv_results, ["model", "class_weight", "C", "mean_cv_average_precision", "std_cv_average_precision", "rank"])}

CV tối đa hóa `average_precision` của scikit-learn, không phải tích phân hình thang của đường precision-recall.

## Kết quả validation ở ngưỡng 0.5

{markdown_table(comparison, ["model", "selected_C", "accuracy", "precision_default", "recall_default", "f1_default", "pr_auc_average_precision", "pr_auc_trapezoidal", "roc_auc", "brier_score"])}

`pr_auc_average_precision` là Average Precision (`average_precision_score`). `pr_auc_trapezoidal` chỉ được ghi riêng để tránh đồng nhất nó với AP. Accuracy có thể cao khi lớp non-default chiếm đa số và mô hình bỏ sót nhiều default; vì vậy lựa chọn không dựa vào accuracy đơn lẻ.

## Calibration

Đã đánh giá reliability diagram và Brier score của **xác suất gốc** cho cả hai mô hình. Không áp dụng hiệu chỉnh xác suất ở giai đoạn này: không có phương án calibrated nào được dùng để chọn ngưỡng hay phục vụ. Xác suất từ `class_weight=balanced` không được mặc định là đã calibrated.

## Kịch bản chi phí và ngưỡng

Kịch bản giả định phục vụ bài tập, **không phải chi phí thực của ngân hàng**: TN={cost["true_negative"]}, FP={cost["false_positive"]}, FN={cost["false_negative"]}, TP={cost["true_positive"]}. Nếu xác suất được calibrated, ngưỡng lý thuyết là FP / (FP + FN) = {theoretical_threshold:.6f}. Ngưỡng validation được chọn bằng cách tối thiểu hóa tổng chi phí giả định trên lưới 0.001, chỉ cho mô hình đã chọn.

{markdown_table(thresholds, ["threshold_role", "threshold", "tn", "fp", "fn", "tp", "precision_default", "recall_default", "f1_default", "total_assumed_cost", "assumed_cost_per_customer"])}

Giảm ngưỡng thường tăng recall và giảm FN, nhưng có thể tăng FP, số cảnh báo nhầm và chi phí FP. Ngưỡng được chọn là {chosen_threshold:.3f}; kết quả này chỉ hợp lệ cho validation hiện tại và phải được đóng băng trước khi dùng test.

## Audit theo nhóm trên validation

{markdown_table(audit, ["group_column", "group_value", "sample_count", "default_count", "recall_tpr", "fnr", "fpr", "precision", "brier_score"])}

Các mã `EDUCATION` và `MARRIAGE` không được tài liệu nguồn diễn giải vẫn được giữ là nhóm mã riêng. `undefined` nghĩa là mẫu nhóm không có mẫu số cần thiết (ví dụ không có default hoặc không có dự đoán dương). Nhóm nhỏ cần được diễn giải thận trọng. Audit này không chứng minh công bằng, không xác lập quan hệ nhân quả và không đủ để quyết định sử dụng trên cá nhân.

## Lựa chọn đã đóng băng cho giai đoạn sau

- Model: `{chosen_model}`.
- Calibration: không áp dụng; dùng xác suất gốc và đã báo cáo Brier/reliability.
- Threshold: `{chosen_threshold:.3f}`, được chọn trên validation theo kịch bản chi phí giả định.
- Test: chưa chạy.
"""
    (REPORTS / "phase2_experiment_report.md").write_text(report, encoding="utf-8")
    card = f"""# Model card nháp

## Mục đích và phạm vi

Mô hình hỗ trợ học tập cho việc ưu tiên nhắc thanh toán hoặc tư vấn tài chính. Nó không dùng để tự động từ chối tín dụng, xử phạt, định giá cá nhân hay đưa ra quyết định tín dụng.

## Dữ liệu

Huấn luyện từ `data/raw/default of credit card clients.xls`, tải từ UCI Default of Credit Card Clients. Tệp CSV Kaggle do người dùng cung cấp đã được đối chiếu nội dung và chỉ dùng để đối chiếu; không phải nguồn huấn luyện. Target là `default_payment_next_month`.

## Mô hình và quyết định hiện tại

`{chosen_model}` với Pipeline imputation, scaling/one-hot encoding và Logistic Regression. C được chọn bằng CV trên train. Không hiệu chỉnh xác suất. Ngưỡng `{chosen_threshold:.3f}` tối thiểu hóa kịch bản chi phí giả định FP=1, FN=5 trên validation; đó không phải chi phí của ngân hàng.

## Giới hạn

- Dữ liệu lịch sử, phạm vi một bộ dữ liệu học tập; có thể không đại diện cho khách hàng hoặc thời gian khác.
- Một số mã EDUCATION/MARRIAGE chưa được tài liệu nguồn giải thích và được giữ nguyên.
- Calibration, sai số theo nhóm và ngưỡng có thể dịch chuyển ngoài validation.
- Chưa dùng tập test; mọi kết quả test phải chờ lựa chọn hiện tại được khóa.
"""
    (REPORTS / "model_card_draft.md").write_text(card, encoding="utf-8")


def run_experiments() -> tuple[pd.DataFrame, pd.DataFrame, str, float]:
    config = load_config()
    train_path = ROOT / "data" / "processed" / "train.csv"
    validation_path = ROOT / "data" / "processed" / "validation.csv"
    if not train_path.exists() or not validation_path.exists():
        raise FileNotFoundError("Frozen train/validation splits are missing. Phase 2 will not recreate them.")
    train, validation = pd.read_csv(train_path), pd.read_csv(validation_path)
    x_train, y_train = split_xy(train)
    x_validation, y_validation = split_xy(validation)
    searches, cv_results = fit_cv_models(x_train, y_train, config)

    MODELS.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True); FIGURES.mkdir(parents=True, exist_ok=True)
    scores: dict[str, np.ndarray] = {}
    comparison_rows: list[dict[str, Any]] = []
    for name, search in searches.items():
        model_path = MODELS / f"{name}_phase2.joblib"
        joblib.dump(search.best_estimator_, model_path)
        probabilities = search.best_estimator_.predict_proba(x_validation)[:, 1]
        scores[name] = probabilities
        metrics = probability_metrics(y_validation, probabilities, threshold=0.5)
        metrics.update({"model": name, "class_weight": "balanced" if name.endswith("balanced") else "none", "selected_C": float(search.best_params_["model__C"])})
        comparison_rows.append(metrics)
    comparison = pd.DataFrame(comparison_rows).sort_values(["pr_auc_average_precision", "brier_score"], ascending=[False, True]).reset_index(drop=True)
    chosen_model = str(comparison.iloc[0]["model"])
    selected_probabilities = scores[chosen_model]
    joblib.dump(searches[chosen_model].best_estimator_, MODELS / "selected_phase2_pipeline.joblib")
    thresholds, chosen_threshold, theoretical_threshold = threshold_rows(y_validation, selected_probabilities, config)
    save_threshold_confusion_matrices(y_validation, selected_probabilities, thresholds)
    reliability = save_reliability_diagram(y_validation, scores, config["phase2"]["reliability_bins"])
    audit = group_audit(validation, selected_probabilities, chosen_threshold, config)

    cv_results.to_csv(REPORTS / "phase2_cv_results.csv", index=False)
    comparison.to_csv(REPORTS / "phase2_validation_model_comparison.csv", index=False)
    thresholds.to_csv(REPORTS / "phase2_validation_thresholds.csv", index=False)
    reliability.to_csv(REPORTS / "phase2_validation_reliability.csv", index=False)
    audit.to_csv(REPORTS / "phase2_validation_group_audit.csv", index=False)
    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "random_state": config["random_state"],
        "training_split": "train", "validation_split": "validation", "test_used": False,
        "selected_model": chosen_model, "selected_pipeline": "models/selected_phase2_pipeline.joblib", "selected_threshold": chosen_threshold,
        "calibration": "none (raw probabilities evaluated with reliability diagram and Brier score)",
        "cost_matrix_assumed": config["phase2"]["cost_matrix_assumed"],
        "libraries": {"python": sys.version, "platform": platform.platform(), "scikit_learn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        "feature_columns": feature_columns(),
    }
    (MODELS / "phase2_selection_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(cv_results, comparison, thresholds, audit, chosen_model, chosen_threshold, theoretical_threshold, config)
    return comparison, thresholds, chosen_model, chosen_threshold


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    comparison, thresholds, selected_model, threshold = run_experiments()
    print("Validation model comparison:")
    print(comparison[["model", "selected_C", "accuracy", "pr_auc_average_precision", "recall_default", "brier_score"]].to_string(index=False))
    print("\nThreshold analysis:")
    print(thresholds[["threshold_role", "threshold", "total_assumed_cost", "recall_default", "precision_default"]].to_string(index=False))
    print(f"\nSelected model: {selected_model}; validation threshold: {threshold:.3f}; test not used.")


if __name__ == "__main__":
    main()
