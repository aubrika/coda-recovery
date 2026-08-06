"""M3 figures (spec 8): the accuracy ladder and the token-budget power curve.
Static PNG via matplotlib Agg. Reads the committed result CSVs."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
FIG = REPO / "figures"


def fig_ladder():
    d = pd.read_csv(RES / "ladder.csv")
    x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    # QAP with CI on the *difference* re-centred on the QAP mean for display
    yerr = np.vstack([d.qap_mean - (d.base_mean + d.diff_lo),
                      (d.base_mean + d.diff_hi) - d.qap_mean])
    ax.errorbar(x, d.qap_mean, yerr=yerr, fmt="o", ms=9, capsize=5,
                color="#1b6ca8", label="QAP (position only)", zorder=3)
    ax.plot(x, d.base_mean, "s--", color="#b8860b", label="frequency baseline")
    ax.plot(x, d.null_mean, "^:", color="#999999", label="strong null (shuffled)")
    for xi, row in zip(x, d.itertuples()):
        ax.annotate(f"{row.trans_per_cell:.1f}/cell", (xi, 0.02),
                    ha="center", fontsize=8, color="#555")
    ax.set_xticks(x)
    ax.set_xticklabels(d.split_type, fontsize=10)
    ax.set_ylabel("accuracy@1 (of 21 types)")
    ax.set_ylim(0, 0.6)
    ax.set_title("Recovery ladder — harder splits share less between halves\n"
                 "(error bars: 95% bootstrap CI of QAP − baseline)")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "ladder.png", dpi=140)
    plt.close(fig)


def fig_token_budget():
    d = pd.read_csv(RES / "token_budget.csv")
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.fill_between(d.budget, d.qap_lo, d.qap_hi, alpha=0.2, color="#1b6ca8")
    ax.plot(d.budget, d.qap_mean, "o-", color="#1b6ca8", label="QAP (position only)")
    ax.plot(d.budget, d.base_mean, "s--", color="#b8860b", label="frequency baseline")
    ax.set_xlabel("token budget (adjacent coda pairs, before split)")
    ax.set_ylabel("accuracy@1 (of 21 types)")
    ax.set_title("Power curve — recovery is data-limited and the gap over\n"
                 "frequency widens with sample size")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "token_budget.png", dpi=140)
    plt.close(fig)


def main():
    fig_ladder()
    fig_token_budget()
    print(f"wrote {FIG/'ladder.png'}")
    print(f"wrote {FIG/'token_budget.png'}")


if __name__ == "__main__":
    main()
