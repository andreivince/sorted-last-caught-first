"""Run every pre-specified analysis and write out/results.json plus figures.

Usage: uv run python -m breadcrumbs.run
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import analysis as A  # noqa: E402
from .data import load  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    c = load(ROOT / "raw")
    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "pages": len(c.pages), "deletions": len(c.deletions)}
    res["q5_workload"] = A.q5_workload(c)
    res["q1_order"] = {str(g): A.q1_order(c, gap=g) for g in (30, 10, 60)}
    res["q2_survival"] = {
        "late_active": A.q2_survival(c, A.late, True),
        "zz_active": A.q2_survival(c, A.zz, True),
        "late_after_placebo": A.q2_survival(c, A.late, False),
    }
    res["q3_breadcrumbs"] = [A.q3_breadcrumbs(c, w, adj) for w in (30, 10, 60) for adj in (False, True)]
    res["q4_response"] = A.q4_response(c)
    res["case_timeline_jun19"] = A.case_timeline(c, datetime(2026, 6, 19, 13, 30, tzinfo=timezone.utc),
                                                 datetime(2026, 6, 19, 17, 30, tzinfo=timezone.utc))
    res["runtime_seconds"] = round(time.time() - t0, 1)
    (OUT / "results.json").write_text(json.dumps(res, indent=2, default=str))
    figures(res)
    print(json.dumps({k: v for k, v in res.items() if k not in ("q5_workload", "q1_order", "case_timeline_jun19")},
                     indent=1, default=str)[:6000])


def figures(res: dict) -> None:
    plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans"})
    daily = res["q5_workload"]["daily"]
    days = [d for d in daily if "2026-06-14" <= d <= "2026-07-14"]
    x = [datetime.fromisoformat(d) for d in days]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    ax.bar(x, [daily[d]["created"] for d in days], width=0.45, align="edge", color="#c85a1e", label="agent pages created")
    ax.bar(x, [-daily[d]["deleted"] for d in days], width=0.45, align="edge", color="#2f5d8a", label="pages deleted by moderator")
    ax.axvline(datetime(2026, 6, 19, 14, 4), color="black", lw=0.8, ls="--")
    ax.text(datetime(2026, 6, 19, 18), max(daily[d]["created"] for d in days) * 0.92,
            "agent notice:\n\"sweep appears active\nalphabetically\"", fontsize=7.5, va="top")
    ax.axhline(0, color="grey", lw=0.5)
    ax.set_ylabel("pages per day (deletions shown below 0)")
    ax.set_title("A  One moderator against a swarm, DSE wiki, June to July 2026", loc="left", fontsize=9)
    ax.legend(fontsize=7.5, loc="lower right", frameon=False)
    ax.tick_params(axis="x", rotation=30)
    ax = axes[1]
    s = res["q1_order"]["30"]["sessions"]
    xs = [datetime.fromisoformat(r["start"]) for r in s]
    ax.scatter(xs, [r["ascending_share"] for r in s], s=[max(8, r["n"] / 3) for r in s],
               c=["#c85a1e" if r["active"] else "#2f5d8a" for r in s], alpha=0.8, edgecolor="none")
    ax.axhline(0.5, color="grey", lw=0.8, ls=":")
    ax.text(xs[-1], 0.51, "random order", fontsize=7, ha="right", va="bottom", color="grey")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("share of consecutive deletions in A-Z order")
    ax.set_title("B  How alphabetical was each deletion session?", loc="left", fontsize=9)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(OUT / "figure1.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()
