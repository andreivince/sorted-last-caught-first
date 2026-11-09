"""Figure 2 (breadcrumb effect) and Figure 3 (June 19 case timeline) from out/*.json."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
ORANGE, BLUE, GREY = "#c85a1e", "#2f5d8a", "#9a9a9a"


def main() -> None:
    res = json.loads((OUT / "results.json").read_text())
    rob = json.loads((OUT / "robustness.json").read_text())
    q3 = {(r["window_minutes"], r["exclude_alphabetical_neighbours"]): r for r in res["q3_breadcrumbs"]}
    rows = [
        ("30 min, planned", q3[(30, False)]),
        ("10 min", q3[(10, False)]),
        ("60 min", q3[(60, False)]),
        ("30 min, no A-Z neighbours", q3[(30, True)]),
        ("30 min, controls created\nwithin 1 h (post hoc)", rob["created_within_60"]),
        ("30 min, active period only\n(post hoc)", rob["active_only"]),
        ("reverse order placebo\n(post hoc)", rob["reverse_placebo"]),
    ]
    plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    y = list(range(len(rows)))[::-1]
    for yi, (label, r) in zip(y, rows):
        ax.barh(yi + 0.18, r["rate_linked"] * 100, height=0.34, color=ORANGE)
        ax.barh(yi - 0.18, r["rate_control"] * 100, height=0.34, color=BLUE)
        ax.text(max(r["rate_linked"], r["rate_control"]) * 100 + 0.8, yi,
                f'x{r["risk_ratio"]}  ({r["linked_deleted_in_window"]}/{r["linked_targets"]})', va="center", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels([label for label, _ in rows], fontsize=8)
    ax.set_xlabel("percent of alive pages deleted within the window after the linking page was deleted")
    ax.barh([], [], color=ORANGE, label="pages the deleted page linked to")
    ax.barh([], [], color=BLUE, label="matched pages it did not link to")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.set_xlim(0, max(r["rate_linked"] for _, r in rows) * 100 + 12)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "figure2.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()
