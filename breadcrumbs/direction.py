"""Post hoc direction test for Q3: when a linking page and a page it links to are both deleted within
30 minutes of each other, is the linked page deleted after the linking page more often than before?
Baseline: the same question for pairs of the linking page with unlinked pages created within 60 minutes
of the linked page and also deleted within 30 minutes of the linking page.
Usage: uv run python -m breadcrumbs.direction
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

from .data import extract_links, load

ROOT = Path(__file__).resolve().parent.parent
W = 30 * 60


def main() -> None:
    c = load(ROOT / "raw")
    titles = {p.title: k for k, p in c.pages.items()}
    tset = set(titles)
    pages = [p for p in c.pages.values() if p.deleted is not None]
    dt = np.array([p.deleted.timestamp() for p in pages])
    ct = np.array([p.created.timestamp() for p in pages])
    idx = {p.key: i for i, p in enumerate(pages)}
    link_after = link_before = base_after = base_before = 0
    for p in pages:
        if not p.bodies:
            continue
        body = ""
        for bt, _, b in p.bodies:
            if bt <= p.deleted:
                body = b
        targets = [titles[t] for t in extract_links(body, tset) - {p.title}]
        tp = p.deleted.timestamp()
        linked_idx = {idx[k] for k in targets if k in idx}
        for j in linked_idx:
            d = dt[j] - tp
            if 0 < abs(d) <= W:
                link_after += d > 0
                link_before += d < 0
            near = (np.abs(ct - ct[j]) <= 3600) & (np.abs(dt - tp) <= W) & (dt != tp)
            near[list(linked_idx)] = False
            near[idx[p.key]] = False
            d2 = dt[near] - tp
            base_after += int((d2 > 0).sum())
            base_before += int((d2 < 0).sum())
    out = {"linked_after": int(link_after), "linked_before": int(link_before),
           "linked_share_after": round(link_after / max(1, link_after + link_before), 4),
           "binomial_p_vs_half": float(stats.binomtest(int(link_after), int(link_after + link_before), 0.5).pvalue),
           "baseline_after": base_after, "baseline_before": base_before,
           "baseline_share_after": round(base_after / max(1, base_after + base_before), 4)}
    tab = [[out["linked_after"], out["linked_before"]], [base_after, base_before]]
    out["fisher_p_linked_vs_baseline"] = float(stats.fisher_exact(tab).pvalue)
    (ROOT / "out" / "direction.json").write_text(json.dumps(out, indent=2))
    print(out)


if __name__ == "__main__":
    main()
