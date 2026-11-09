"""Pre-specified analyses (see ANALYSIS_PLAN.md). Every function returns plain dicts for results.json."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import numpy as np
from scipy import stats

from .data import Corpus, extract_links, sessions

ACTIVE_END = datetime(2026, 6, 22, 23, 59, 59, tzinfo=timezone.utc)
NOTICE_TIME = datetime(2026, 6, 19, 14, 4, tzinfo=timezone.utc)
SWEEP_WORDS = re.compile(r"delet|lösch|losch|sweep|admin|remov|cleanup|clean-up", re.I)


def late(title: str) -> bool:
    return title[:1].lower() in "yz"


def zz(title: str) -> bool:
    return title.lower().startswith("zz")


# Q1 ------------------------------------------------------------------------------------------
def ascending_share(titles: list[str]) -> float:
    t = [x.lower() for x in titles]
    return sum(a < b for a, b in zip(t, t[1:])) / (len(t) - 1)


def longest_run(titles: list[str]) -> int:
    t = [x.lower() for x in titles]
    best = run = 1
    for a, b in zip(t, t[1:]):
        run = run + 1 if a < b else 1
        best = max(best, run)
    return best


def q1_order(c: Corpus, gap: float = 30, min_n: int = 20, n_perm: int = 10000, seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    times = [t for t, _ in c.deletions]
    rows = []
    for s, e in sessions(times, gap):
        if e - s < min_n:
            continue
        keys = [k for _, k in c.deletions[s:e]]
        titles = [c.pages[k].title if k in c.pages else k.split("~", 1)[1] for k in keys]
        obs = ascending_share(titles)
        ranks = np.argsort(np.argsort([x.lower() for x in titles]))
        null = np.empty(n_perm)
        for i in range(0, n_perm, 1000):
            m = min(1000, n_perm - i)
            perm = np.array([rng.permutation(ranks) for _ in range(m)])
            null[i:i + m] = (np.diff(perm, axis=1) > 0).mean(axis=1)
        rows.append({"start": times[s].isoformat(), "n": e - s, "active": times[s] <= ACTIVE_END,
                     "ascending_share": round(obs, 4), "longest_run": longest_run(titles),
                     "null_mean": round(float(null.mean()), 4),
                     "p_one_sided": float((np.sum(null >= obs) + 1) / (n_perm + 1))})
    out = {"gap_minutes": gap, "sessions": rows}
    for label, sel in (("active", True), ("after", False)):
        r = [x for x in rows if x["active"] == sel]
        if r:
            pairs = sum(x["n"] - 1 for x in r)
            asc = sum(x["ascending_share"] * (x["n"] - 1) for x in r)
            out[label] = {"sessions": len(r), "deletions": sum(x["n"] for x in r),
                          "pooled_ascending_share": round(asc / pairs, 4),
                          "sessions_p_below_0.01": sum(x["p_one_sided"] < 0.01 for x in r)}
    return out


# Q2 ------------------------------------------------------------------------------------------
def _quartile(values: np.ndarray) -> np.ndarray:
    qs = np.quantile(values, [0.25, 0.5, 0.75]) if len(values) else []
    return np.searchsorted(qs, values, side="right")


def q2_survival(c: Corpus, exposure=late, active: bool = True, gap: float = 30, n_perm: int = 5000,
                seed: int = 2) -> dict:
    rng = np.random.default_rng(seed)
    times = [t for t, _ in c.deletions]
    rows_g, rows_e, rows_y, rows_meta = [], [], [], []
    gid = 0
    for s, e in sessions(times, gap):
        start, end = times[s], times[e - 1]
        if (start <= ACTIVE_END) != active or e - s < 5:
            continue
        alive = [p for p in c.pages.values() if p.created < start and (p.deleted is None or p.deleted >= start)]
        if not alive:
            continue
        age = np.array([(start - p.created).total_seconds() for p in alive])
        size = np.array([p.body_bytes for p in alive], dtype=float)
        aq, sq = _quartile(age), _quartile(size)
        strata = {}
        for p, a, z in zip(alive, aq, sq):
            key = (a, z, p.family)
            if key not in strata:
                strata[key] = gid
                gid += 1
            rows_g.append(strata[key])
            rows_e.append(exposure(p.title))
            rows_y.append(p.deleted is not None and p.deleted <= end)
        rows_meta.append((start, len(alive)))
    g, ex, y = np.array(rows_g), np.array(rows_e, dtype=bool), np.array(rows_y, dtype=bool)
    order = np.argsort(g, kind="stable")
    g, ex, y = g[order], ex[order], y[order]

    def stat(e):
        return y[~e].mean() - y[e].mean() if e.any() and (~e).any() else 0.0

    obs = stat(ex)
    null = np.empty(n_perm)
    for i in range(n_perm):
        idx = np.lexsort((rng.random(len(g)), g))
        null[i] = stat(ex[idx])
    # only strata that contain both exposed and unexposed rows carry information
    informative = 0
    for k in np.unique(g):
        m = g == k
        if ex[m].any() and (~ex[m]).any():
            informative += int(m.sum())
    return {"active_period": active, "exposure": exposure.__name__, "sessions": len(rows_meta),
            "page_session_rows": int(len(y)), "exposed_rows": int(ex.sum()),
            "exposed_deleted": int(y[ex].sum()), "unexposed_rows": int((~ex).sum()),
            "unexposed_deleted": int(y[~ex].sum()),
            "rate_exposed": round(float(y[ex].mean()), 4) if ex.any() else None,
            "rate_unexposed": round(float(y[~ex].mean()), 4),
            "difference": round(float(obs), 4),
            "p_stratified_one_sided": float((np.sum(null >= obs) + 1) / (n_perm + 1)),
            "rows_in_informative_strata": informative}


# Q3 ------------------------------------------------------------------------------------------
def q3_breadcrumbs(c: Corpus, window_min: float = 30, exclude_adjacent: bool = False, n_perm: int = 2000,
                   seed: int = 3, created_within_min: float | None = None, direction: str = "after") -> dict:
    """direction="after" counts targets deleted in (t, t+w]; "before" is the reverse-order placebo [t-w, t).
    created_within_min, when set, restricts controls to pages created within that many minutes of the
    linked target (post hoc robustness check, not in the original plan)."""
    rng = np.random.default_rng(seed)
    titles = {p.title: k for k, p in c.pages.items()}
    title_set = set(titles)
    pages = list(c.pages.values())
    created = np.array([p.created.timestamp() for p in pages])
    deleted = np.array([p.deleted.timestamp() if p.deleted else np.inf for p in pages])
    index = {p.key: i for i, p in enumerate(pages)}
    day = np.array([p.created.date().toordinal() for p in pages])
    initial = np.array([p.title[:1].lower() for p in pages])
    sort_rank = np.argsort(np.argsort([p.title.lower() for p in pages]))
    w = window_min * 60
    events = []
    for t, k in c.deletions:
        if k not in c.pages:
            continue
        p = c.pages[k]
        body = ""
        for bt, _, b in p.bodies:
            if bt <= t:
                body = b
        links = extract_links(body, title_set) - {p.title}
        if not links:
            continue
        tt = t.timestamp()
        t_ref = tt if direction == "after" else tt - w
        alive = (created < t_ref) & (deleted > t_ref)
        linked = np.zeros(len(pages), dtype=bool)
        for title in links:
            linked[index[titles[title]]] = True
        linked &= alive
        if not linked.any():
            continue
        if direction == "after":
            hit = (deleted > tt) & (deleted <= tt + w)
        else:
            hit = (deleted >= tt - w) & (deleted < tt)
        i_self = index[k]
        if exclude_adjacent:
            near = np.abs(sort_rank - sort_rank[i_self]) <= 3
            linked &= ~near
            alive &= ~near
            if not linked.any():
                continue
        cand = np.zeros(len(pages), dtype=bool)
        li = np.flatnonzero(linked)
        for j in li:
            if created_within_min is None:
                cand |= alive & (day == day[j]) & (initial == initial[j])
            else:
                cand |= alive & (np.abs(created - created[j]) <= created_within_min * 60)
        cand[i_self] = False
        control = cand & ~linked
        events.append((li, np.flatnonzero(control), hit, tt))
    lk_n = sum(len(li) for li, _, _, _ in events)
    lk_hit = sum(int(h[li].sum()) for li, _, h, _ in events)
    ct_n = sum(len(ci) for _, ci, _, _ in events)
    ct_hit = sum(int(h[ci].sum()) for _, ci, h, _ in events)
    obs = lk_hit
    null = np.empty(n_perm)
    for i in range(n_perm):
        s = 0
        for li, ci, h, _ in events:
            pool = np.concatenate([li, ci])
            pick = rng.choice(pool, size=len(li), replace=False)
            s += int(h[pick].sum())
        null[i] = s
    r_l = lk_hit / lk_n if lk_n else float("nan")
    r_c = ct_hit / ct_n if ct_n else float("nan")
    return {"window_minutes": window_min, "exclude_alphabetical_neighbours": exclude_adjacent,
            "direction": direction, "control_created_within_minutes": created_within_min,
            "deletion_events_with_alive_links": len(events), "linked_targets": lk_n,
            "linked_deleted_in_window": lk_hit, "control_targets": ct_n, "control_deleted_in_window": ct_hit,
            "rate_linked": round(r_l, 4), "rate_control": round(r_c, 4),
            "risk_ratio": round(r_l / r_c, 2) if r_c else None,
            "null_mean_linked_hits": round(float(null.mean()), 2),
            "p_one_sided": float((np.sum(null >= obs) + 1) / (n_perm + 1)),
            "active_period_events": sum(1 for *_, tt in events if tt <= ACTIVE_END.timestamp())}


# Q4 ------------------------------------------------------------------------------------------
def q4_response(c: Corpus) -> dict:
    # (a) belief spread
    mentions = []
    for p in c.pages.values():
        for t, _, b in p.bodies:
            if "alphabet" in b.lower() and SWEEP_WORDS.search(b):
                mentions.append((t, p.key))
    mentions.sort()
    first_per_page = {}
    for t, k in mentions:
        first_per_page.setdefault(k, t)
    spread = sorted(first_per_page.values())
    # (b) title initials of new pages, active window, before/after the first notice
    before = [p for p in c.pages.values() if p.created < NOTICE_TIME and p.created >= NOTICE_TIME - timedelta(days=3)]
    after = [p for p in c.pages.values() if NOTICE_TIME <= p.created <= ACTIVE_END]

    def share(ps, f):
        return sum(f(p.title) for p in ps), len(ps)

    b_l, b_n = share(before, late)
    a_l, a_n = share(after, late)
    fisher = stats.fisher_exact([[a_l, a_n - a_l], [b_l, b_n - b_l]], alternative="greater")
    b_z, _ = share(before, zz)
    a_z, _ = share(after, zz)
    # (c) re-posting within 72h of a deletion
    def shingles(text):
        w = re.findall(r"\w+", text.lower())
        return {" ".join(w[i:i + 5]) for i in range(max(0, len(w) - 4))}

    created_sorted = sorted(c.pages.values(), key=lambda p: p.created)
    exact = near = total = 0
    for p in c.pages.values():
        if p.deleted is None or p.deleted > ACTIVE_END or not p.bodies:
            continue
        total += 1
        shas = {s for _, s, _ in p.bodies if s}
        sh = shingles(p.last_body)
        lo, hi = p.deleted, p.deleted + timedelta(hours=72)
        found_exact = found_near = False
        for q in created_sorted:
            if q.created < lo:
                continue
            if q.created > hi:
                break
            if q.key == p.key or not q.bodies:
                continue
            if q.bodies[0][1] in shas:
                found_exact = True
                break
            if len(sh) >= 5:
                s2 = shingles(q.bodies[0][2])
                if s2 and len(sh & s2) / len(sh | s2) >= 0.8:
                    found_near = True
        exact += found_exact
        near += found_exact or found_near
    return {"sweep_belief_mentions": len(mentions), "pages_mentioning": len(first_per_page),
            "first_mention": spread[0].isoformat() if spread else None,
            "pages_mentioning_by_end_of_jun19": sum(t <= datetime(2026, 6, 19, 23, 59, tzinfo=timezone.utc) for t in spread),
            "new_pages_3d_before_notice": b_n, "late_initial_before": b_l, "zz_before": b_z,
            "new_pages_after_notice_to_jun22": a_n, "late_initial_after": a_l, "zz_after": a_z,
            "fisher_late_after_gt_before_p": float(fisher.pvalue), "odds_ratio": float(fisher.statistic),
            "deletions_to_jun22": total, "reposted_exact_72h": exact, "reposted_exact_or_near_72h": near}


# Q5 ------------------------------------------------------------------------------------------
def q5_workload(c: Corpus) -> dict:
    created = Counter(p.created.date().isoformat() for p in c.pages.values())
    deleted = Counter(t.date().isoformat() for t, _ in c.deletions)
    times = [t for t, _ in c.deletions]
    active_seconds = sum(max((times[e - 1] - times[s]).total_seconds(), 60) for s, e in sessions(times, 30))
    return {"daily": {d: {"created": created.get(d, 0), "deleted": deleted.get(d, 0)}
                      for d in sorted(set(created) | set(deleted))},
            "deletions_total": len(times), "deletion_sessions": len(sessions(times, 30)),
            "deletions_per_active_hour": round(len(times) / (active_seconds / 3600), 1),
            "first_deletion": times[0].isoformat(), "last_deletion": times[-1].isoformat()}


def case_timeline(c: Corpus, start: datetime, end: datetime) -> list[dict]:
    rows = []
    for p in c.pages.values():
        for t, _, b in p.bodies:
            if start <= t <= end and "alphabet" in b.lower() and SWEEP_WORDS.search(b):
                rows.append({"time": t.isoformat(), "event": "notice saved", "page": p.title})
                break
        if start <= p.created <= end and zz(p.title):
            rows.append({"time": p.created.isoformat(), "event": "ZZ page created", "page": p.title})
    for t, k in c.deletions:
        if start <= t <= end and k in c.pages:
            p = c.pages[k]
            if zz(p.title) or any("alphabet" in b.lower() for _, _, b in p.bodies):
                rows.append({"time": t.isoformat(), "event": "deleted", "page": p.title})
    return sorted(rows, key=lambda r: r["time"])
