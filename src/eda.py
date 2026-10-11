"""Create EDA figures from the frozen training split only."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.features import CONTINUOUS_COLUMNS, load_config

ROOT = Path(__file__).resolve().parents[1]


def create_train_eda() -> list[Path]:
    train_path = ROOT / "data" / "processed" / "train.csv"
    if not train_path.exists():
        raise FileNotFoundError("Frozen train split is absent. Run `python -m src.data prepare` first.")
    train = pd.read_csv(train_path)
    target = load_config()["target_column"]
    figures = ROOT / "reports" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    outputs = []

    counts = train[target].value_counts().sort_index()
    labels = ["non-default (0)", "default (1)"]
    ax = counts.plot.bar(color=["#4c78a8", "#e45756"], rot=0)
    ax.set_title("Target distribution — train split only")
    ax.set_xlabel("Target")
    ax.set_ylabel("Account count")
    for index, value in enumerate(counts):
        ax.text(index, value, f"{value:,} ({value / len(train):.1%})", ha="center", va="bottom")
    path = figures / "train_target_distribution.png"
    ax.figure.tight_layout(); ax.figure.savefig(path, dpi=150); plt.close(ax.figure)
    outputs.append(path)

    # Descriptive EDA only: calculated exclusively from the frozen training split.
    correlation = train.loc[:, CONTINUOUS_COLUMNS].corr(method="pearson")
    fig, axis = plt.subplots(figsize=(11, 9))
    image = axis.imshow(correlation, cmap="RdYlGn", vmin=-1, vmax=1)
    names = [name.replace("BILL_AMT", "BILL").replace("PAY_AMT", "PAY") for name in CONTINUOUS_COLUMNS]
    axis.set_xticks(range(len(names)), names, rotation=45, ha="right")
    axis.set_yticks(range(len(names)), names)
    fig.colorbar(image, ax=axis, label="Pearson r")
    axis.set_title("Correlation of continuous features — train split only")
    fig.tight_layout()
    path = figures / "train_continuous_feature_correlation.png"
    fig.savefig(path, dpi=150); plt.close(fig)
    outputs.append(path)

    pay_default_rate = train.groupby("PAY_0", dropna=False)[target].agg(["count", "mean"]).sort_index()
    ax = pay_default_rate["mean"].plot.bar(color="#72b7b2", rot=0)
    ax.set_title("Default rate by most recent repayment status PAY_0 — train only")
    ax.set_xlabel("PAY_0 code (kept as source value)")
    ax.set_ylabel("Default rate")
    ax.yaxis.set_major_formatter("{x:.0%}")
    path = figures / "train_default_rate_by_pay_0.png"
    ax.figure.tight_layout(); ax.figure.savefig(path, dpi=150); plt.close(ax.figure)
    outputs.append(path)
    return outputs


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    for output in create_train_eda():
        print(f"Created {output.relative_to(ROOT)}")
