"""Create report-only visual summaries from frozen artifacts.

The group-audit chart reads the already saved final-test audit. It does not
load test.csv, fit a model, calculate a new threshold, or modify the freeze.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "reports" / "figures"


def create_group_audit_chart() -> Path:
    audit_path = ROOT / "reports" / "final_test_group_audit.csv"
    if not audit_path.exists():
        raise FileNotFoundError("Frozen final test audit is required; no test evaluation will be rerun.")
    audit = pd.read_csv(audit_path)
    groups = ["SEX", "EDUCATION", "MARRIAGE"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.4), sharey=True)
    for axis, group in zip(axes, groups, strict=True):
        part = audit.loc[audit["group_column"] == group].copy()
        x = np.arange(len(part))
        width = 0.36
        axis.bar(x - width / 2, part["recall_tpr"], width, label="Recall / TPR", color="#4c78a8")
        axis.bar(x + width / 2, part["fpr"], width, label="FPR", color="#e45756")
        axis.set_xticks(x, [str(value) for value in part["group_value"]])
        axis.set_ylim(0, 1.05)
        axis.set_xlabel(f"{group} code")
        axis.set_title(f"{group} (n shown below)")
        for index, row in part.reset_index(drop=True).iterrows():
            axis.text(index, 0.02, f"n={int(row['sample_count'])}", ha="center", va="bottom", fontsize=8, rotation=90)
    axes[0].set_ylabel("Rate")
    axes[0].legend(loc="upper left")
    fig.suptitle("Final-test group audit at frozen threshold 0.150", y=1.01)
    fig.text(0.5, -0.04, "Groups with very small sample/default counts must be interpreted cautiously; missing TPR is not plotted.", ha="center", fontsize=9)
    fig.tight_layout()
    FIGURES.mkdir(parents=True, exist_ok=True)
    output = FIGURES / "final_test_group_audit_rates.png"
    fig.savefig(output, dpi=160, bbox_inches="tight"); plt.close(fig)
    return output


if __name__ == "__main__":
    print(f"Created {create_group_audit_chart().relative_to(ROOT)}")
