"""Post hoc robustness checks for Q3, added after the planned run (reported as post hoc).

1. Controls created within 60 minutes of the linked target instead of the same day and initial.
2. Reverse-order placebo: linked targets deleted in the window before the linking page.
3. Active period only (deletions up to June 22).
Usage: uv run python -m breadcrumbs.robustness
"""
from __future__ import annotations

import json
from pathlib import Path

from . import analysis as A
from .data import load

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    c = load(ROOT / "raw")
    out = {
        "created_within_60": A.q3_breadcrumbs(c, 30, False, created_within_min=60),
        "created_within_60_no_neighbours": A.q3_breadcrumbs(c, 30, True, created_within_min=60),
        "reverse_placebo": A.q3_breadcrumbs(c, 30, False, direction="before"),
        "reverse_placebo_created_within_60": A.q3_breadcrumbs(c, 30, False, direction="before",
                                                              created_within_min=60),
    }
    active = [t for t in c.deletions if t[0] <= A.ACTIVE_END]
    sub = A.Corpus(c.pages, active, c.saves) if hasattr(A, "Corpus") else None
    if sub is None:
        from .data import Corpus
        sub = Corpus(c.pages, active, c.saves)
    out["active_only"] = A.q3_breadcrumbs(sub, 30, False)
    out["active_only_created_within_60"] = A.q3_breadcrumbs(sub, 30, False, created_within_min=60)
    (ROOT / "out" / "robustness.json").write_text(json.dumps(out, indent=2))
    for k, v in out.items():
        print(k, {x: v[x] for x in ("deletion_events_with_alive_links", "linked_targets", "linked_deleted_in_window",
                                     "rate_linked", "rate_control", "risk_ratio", "p_one_sided")})


if __name__ == "__main__":
    main()
