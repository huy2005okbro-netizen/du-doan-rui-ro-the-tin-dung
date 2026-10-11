"""Freeze Phase-2 selection then perform a single guarded final test evaluation."""
from __future__ import annotations

import argparse
import hashlib
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
from sklearn.metrics import ConfusionMatrixDisplay, PrecisionRecallDisplay, RocCurveDisplay

from src.experiments import FIGURES, MODELS, REPORTS, group_audit, markdown_table, probability_metrics, threshold_rows
from src.features import feature_columns, load_config, split_xy

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = MODELS / "final_selection_freeze.json"
FINAL_RESULT_PATH = REPORTS / "final_test_evaluation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def candidate_validation_costs(config: dict[str, Any]) -> pd.DataFrame:
    """Compare candidates at their own validation cost-minimum thresholds."""
    validation = pd.read_csv(ROOT / "data" / "processed" / "validation.csv")
    x_validation, y_validation = split_xy(validation)
    rows = []
    for name in ["logistic_unweighted", "logistic_balanced"]:
        probabilities = joblib.load(MODELS / f"{name}_phase2.joblib").predict_proba(x_validation)[:, 1]
        table, threshold, _ = threshold_rows(y_validation, probabilities, config)
        row = table.loc[table["threshold_role"] == "validation_cost_minimum"].iloc[0].to_dict()
        row.update({"model": name, "validation_cost_minimum_threshold": threshold})
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["total_assumed_cost", "brier_score"])


def freeze_selection() -> dict[str, Any]:
    """Write a pre-test record. This function deliberately never opens test.csv."""
    if FINAL_RESULT_PATH.exists():
        raise FileExistsError("Final test results already exist; refusing a new freeze.")
    config = load_config()
    selection_path, pipeline_path = MODELS / "phase2_selection_metadata.json", MODELS / "selected_phase2_pipeline.joblib"
    if not selection_path.exists() or not pipeline_path.exists():
        raise FileNotFoundError("Phase-2 selection artifacts are missing.")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if selection.get("selected_model") != "logistic_unweighted" or float(selection.get("selected_threshold", -1)) != 0.15:
        raise ValueError("Unexpected Phase-2 selection; refusing to freeze.")
    if selection.get("random_state") != config["random_state"] or selection.get("test_used") is not False:
        raise ValueError("Phase-2 state is not valid for a pre-test freeze.")
    candidates = candidate_validation_costs(config)
    chosen = candidates.loc[candidates["model"] == selection["selected_model"]].iloc[0]
    if float(chosen["validation_cost_minimum_threshold"]) != float(selection["selected_threshold"]):
        raise ValueError("Recorded threshold is not the validation cost minimum.")
    freeze = {
        "freeze_version": "phase3-final-v1", "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "test_used_at_freeze": False,
        "selected_model": selection["selected_model"], "pipeline_path": "models/selected_phase2_pipeline.joblib", "pipeline_sha256": sha256(pipeline_path), "pipeline_bytes": pipeline_path.stat().st_size,
        "selected_C": 1.0, "calibration": "none; raw probabilities retained", "threshold": selection["selected_threshold"], "cost_matrix_assumed": config["phase2"]["cost_matrix_assumed"], "random_state": config["random_state"],
        "preprocessing": {"continuous": "median imputation then StandardScaler", "categorical": "most_frequent imputation then OneHotEncoder(handle_unknown=ignore)", "feature_columns": feature_columns(), "excluded_columns": [config["id_column"], config["target_column"]]},
        "library_versions": {"python": sys.version, "platform": platform.platform(), "scikit_learn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
        "phase2_selection_sha256": sha256(selection_path), "config_sha256": sha256(ROOT / "config.json"), "validation_candidate_costs": candidates.to_dict(orient="records"),
    }
    FREEZE_PATH.write_text(json.dumps(freeze, ensure_ascii=False, indent=2), encoding="utf-8")
    report = f"""# Rà soát và đóng băng trước test

- Pipeline chứa toàn bộ preprocessing, vì vậy imputer/scaler/encoder chỉ fit trong train hoặc fold CV.
- CV Phase 2 là Stratified 5-fold trên train với `random_state=42`; validation chỉ dùng sau CV.
- Ngưỡng 0.150 đúng là chi phí validation tối thiểu theo kịch bản giả định FP=1, FN=5, TP=TN=0 trên lưới 0.001.
- Chênh lệch AP khoảng 0.0004 không là bằng chứng vượt trội rõ rệt. Mô hình không trọng số được giữ vì chi phí validation tốt hơn và Brier thấp hơn trong lựa chọn đã ghi.

## Chi phí validation tại ngưỡng tốt nhất của từng ứng viên

{markdown_table(candidates, ["model", "validation_cost_minimum_threshold", "total_assumed_cost", "assumed_cost_per_customer", "pr_auc_average_precision", "brier_score", "recall_default", "precision_default"])}

Pipeline đóng băng: `models/selected_phase2_pipeline.joblib`; SHA-256: `{freeze["pipeline_sha256"]}`. Test chưa được mở khi tạo freeze.
"""
    (REPORTS / "pretest_freeze_review.md").write_text(report, encoding="utf-8")
    return freeze


def save_figures(y_true: pd.Series, probabilities: np.ndarray, predictions: np.ndarray, bins: int) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    display = ConfusionMatrixDisplay.from_predictions(y_true, predictions, display_labels=["non-default", "default"], cmap="Blues")
    display.ax_.set_title("Final test confusion matrix — frozen threshold")
    display.figure_.tight_layout(); display.figure_.savefig(FIGURES / "final_test_confusion_matrix.png", dpi=150); plt.close(display.figure_)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    PrecisionRecallDisplay.from_predictions(y_true, probabilities, ax=axes[0], name="frozen model"); axes[0].set_title("Final test precision-recall curve")
    RocCurveDisplay.from_predictions(y_true, probabilities, ax=axes[1], name="frozen model"); axes[1].set_title("Final test ROC curve")
    fig.tight_layout(); fig.savefig(FIGURES / "final_test_pr_roc_curves.png", dpi=150); plt.close(fig)
    observed, predicted = calibration_curve(y_true, probabilities, n_bins=bins, strategy="uniform")
    fig, axis = plt.subplots(figsize=(7, 6)); axis.plot([0, 1], [0, 1], "k--", label="perfect calibration")
    axis.plot(predicted, observed, marker="o", label="frozen model"); axis.set_xlabel("Mean predicted probability"); axis.set_ylabel("Observed default frequency")
    axis.set_title("Final test reliability diagram"); axis.legend(); axis.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(FIGURES / "final_test_reliability_diagram.png", dpi=150); plt.close(fig)


def write_reports(result: dict[str, Any], audit: pd.DataFrame, freeze: dict[str, Any]) -> None:
    metrics = result["metrics"]
    report = f"""# Đánh giá test cuối cùng

Pipeline đã đóng băng trước test: SHA-256 `{freeze["pipeline_sha256"]}`. Module từ chối chạy lại hoặc ghi đè kết quả test.

## Kết quả test

{markdown_table(pd.DataFrame([metrics]), ["threshold", "accuracy", "precision_default", "recall_default", "f1_default", "pr_auc_average_precision", "pr_auc_trapezoidal", "roc_auc", "brier_score", "tn", "fp", "fn", "tp", "total_assumed_cost", "assumed_cost_per_customer"])}

AP là `average_precision_score`; PR-AUC hình thang báo riêng. Chi phí là kịch bản giả định FP=1, FN=5, TP=TN=0; không phải chi phí ngân hàng. Model, calibration và threshold không thay đổi theo test.

## Audit nhóm trên test

{markdown_table(audit, ["group_column", "group_value", "sample_count", "default_count", "recall_tpr", "fnr", "fpr", "precision", "brier_score", "note"])}

Nhóm ít mẫu hoặc metric không xác định cần được diễn giải thận trọng; audit không chứng minh công bằng hay nhân quả.
"""
    (REPORTS / "final_test_report.md").write_text(report, encoding="utf-8")
    card = f"""# Model card

## Mục đích và giới hạn sử dụng
Mô hình chỉ phục vụ học tập và hỗ trợ ưu tiên nhắc thanh toán/tư vấn tài chính. Không dùng để tự động từ chối tín dụng, xử phạt, định giá cá nhân hoặc suy luận nguyên nhân cá nhân.

## Dữ liệu và target
Dữ liệu lịch sử UCI Default of Credit Card Clients; target `default_payment_next_month=1` là default tháng sau trong dữ liệu gốc.

## Pipeline đã đóng băng
Logistic Regression không `class_weight`, C=1.0; imputation/scaling/one-hot trong pipeline; không hiệu chỉnh xác suất. Ngưỡng `{freeze["threshold"]:.3f}` lấy từ validation, không từ test. Chi phí giả định FP=1, FN=5, TP=TN=0.

## Hiệu năng test
Accuracy {metrics["accuracy"]:.4f}; precision {metrics["precision_default"]:.4f}; recall {metrics["recall_default"]:.4f}; F1 {metrics["f1_default"]:.4f}; AP {metrics["pr_auc_average_precision"]:.4f}; ROC-AUC {metrics["roc_auc"]:.4f}; Brier {metrics["brier_score"]:.4f}. Chi phí giả định {metrics["total_assumed_cost"]}, hay {metrics["assumed_cost_per_customer"]:.4f}/khách hàng.

## Hạn chế
Dữ liệu lịch sử có thể không đại diện cho nơi/thời kỳ khác. Các mã EDUCATION/MARRIAGE chưa rõ nghĩa được giữ nguyên. Calibration và sai số theo nhóm có thể thay đổi ngoài dữ liệu này; không kết luận công bằng từ một chỉ số.
"""
    (REPORTS / "model_card.md").write_text(card, encoding="utf-8")


def evaluate_test_once() -> dict[str, Any]:
    """The sole test-read path. It rejects repeats and a changed pipeline checksum."""
    if FINAL_RESULT_PATH.exists():
        raise FileExistsError("Final test evaluation already exists and will not be overwritten.")
    if not FREEZE_PATH.exists():
        raise FileNotFoundError("Run `python -m src.final_evaluation freeze` before opening test.")
    config, freeze = load_config(), json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    pipeline_path = ROOT / freeze["pipeline_path"]
    if sha256(pipeline_path) != freeze["pipeline_sha256"]:
        raise ValueError("Frozen pipeline checksum changed; refusing test evaluation.")
    test_path = ROOT / "data" / "processed" / "test.csv"
    test = pd.read_csv(test_path); x_test, y_test = split_xy(test)
    probabilities = joblib.load(pipeline_path).predict_proba(x_test)[:, 1]
    metrics = probability_metrics(y_test, probabilities, float(freeze["threshold"]))
    costs = freeze["cost_matrix_assumed"]
    metrics["total_assumed_cost"] = int(metrics["fp"]) * costs["false_positive"] + int(metrics["fn"]) * costs["false_negative"]
    metrics["assumed_cost_per_customer"] = metrics["total_assumed_cost"] / len(test)
    predictions = (probabilities >= float(freeze["threshold"])).astype(int)
    audit = group_audit(test, probabilities, float(freeze["threshold"]), config)
    save_figures(y_test, probabilities, predictions, config["phase2"]["reliability_bins"])
    audit.to_csv(REPORTS / "final_test_group_audit.csv", index=False); pd.DataFrame([metrics]).to_csv(REPORTS / "final_test_metrics.csv", index=False)
    result = {"evaluation_version": "phase3-final-test-v1", "evaluated_at_utc": datetime.now(timezone.utc).isoformat(), "test_evaluation_count": 1, "test_split_sha256": sha256(test_path), "pipeline_sha256": freeze["pipeline_sha256"], "freeze_sha256": sha256(FREEZE_PATH), "model": freeze["selected_model"], "threshold": freeze["threshold"], "cost_matrix_assumed": costs, "metrics": metrics, "group_audit": audit.to_dict(orient="records")}
    FINAL_RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_reports(result, audit, freeze)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("command", choices=["freeze", "evaluate"]); args = parser.parse_args()
    if args.command == "freeze":
        freeze = freeze_selection(); print(f"Selection frozen. Pipeline SHA-256: {freeze['pipeline_sha256']}")
    else:
        result = evaluate_test_once(); print(pd.DataFrame([result["metrics"]]).to_string(index=False)); print("Final test evaluation saved once; future runs refuse to overwrite it.")


if __name__ == "__main__":
    main()
