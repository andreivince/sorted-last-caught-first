"""Post hoc confound checks added after the planned run (Nov 8, 2026).

Usage: uv run python -m breadcrumbs.confounds  -> out/confounds.json
"""
"""Read-only review checks of the Q3 breadcrumb effect. Run from the repo root:
cd /Users/andreivince/Developer/apart-deleted-last && uv run python <this file>
Writes nothing into the repo; pickles candidate rows into the scratch dir."""
import json
from pathlib import Path
from collections import defaultdict, Counter
from bisect import bisect_right
from datetime import datetime, timezone

import numpy as np

ROOT = str(Path(__file__).resolve().parent.parent)
from .data import load, extract_links, sessions, LINK_BRACKET, ts  # noqa: E402
from .analysis import ACTIVE_END  # noqa: E402

c = load(Path(ROOT) / "raw")
meta = {}
for line in open(f"{ROOT}/raw/pages.jsonl"):
    p = json.loads(line)
    if p["wiki"] == "dse":
        meta[p["page_key"]] = p
rev_lab = defaultdict(list)  # page_key -> [(ts, label, ip16)]
for line in open(f"{ROOT}/raw/revisions.jsonl"):
    r = json.loads(line)
    if r.get("wiki") != "dse":
        continue
    rev_lab[r["page_key"]].append((ts(r["time"]).timestamp(), r.get("label") or "", r.get("ip16") or ""))
for v in rev_lab.values():
    v.sort()

titles = {p.title: k for k, p in c.pages.items()}
title_set = set(titles)
pages = list(c.pages.values())
N = len(pages)
created = np.array([p.created.timestamp() for p in pages])
deleted = np.array([p.deleted.timestamp() if p.deleted else np.inf for p in pages])
index = {p.key: i for i, p in enumerate(pages)}
day = np.array([p.created.date().toordinal() for p in pages])
initial = np.array([p.title[:1].lower() for p in pages])
low = [p.title.lower() for p in pages]
sort_rank = np.argsort(np.argsort(low))
family = np.array([meta.get(p.key, {}).get("page_family", "unknown") for p in pages])
creator_label = np.array([rev_lab[p.key][0][1] if rev_lab[p.key] else "" for p in pages])
creator_ip = np.array([rev_lab[p.key][0][2] if rev_lab[p.key] else "" for p in pages])
labels_all = [set(x[1] for x in rev_lab[p.key]) for p in pages]
save_times = [np.array([b[0].timestamp() for b in p.bodies]) for p in pages]


def last_save_before(i, t):
    st = save_times[i]
    j = bisect_right(st, t) - 1
    return st[j] if j >= 0 else created[i]


def lab_before(i, t):
    return {x[1] for x in rev_lab[pages[i].key] if x[0] <= t}


def common_prefix(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


times = [t for t, _ in c.deletions]
sess = sessions(times, 30)
sess_of = np.empty(len(times), dtype=int)
for si, (s, e) in enumerate(sess):
    sess_of[s:e] = si

W = 30 * 60
rows = []  # per candidate row
ev_id = 0
for di, (t, k) in enumerate(c.deletions):
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
    bracket = {m.strip() for m in LINK_BRACKET.findall(body or "")} & title_set
    tt = t.timestamp()
    alive = (created < tt) & (deleted > tt)
    linked = np.zeros(N, dtype=bool)
    for title in links:
        linked[index[titles[title]]] = True
    linked &= alive
    if not linked.any():
        continue
    hit = (deleted > tt) & (deleted <= tt + W)
    i_self = index[k]
    cand = np.zeros(N, dtype=bool)
    li = np.flatnonzero(linked)
    for j in li:
        cand |= alive & (day == day[j]) & (initial == initial[j])
    cand[i_self] = False
    control = cand & ~linked
    p_last = last_save_before(i_self, tt)
    for j in np.concatenate([li, np.flatnonzero(control)]):
        is_l = bool(linked[j])
        rows.append(dict(
            ev=ev_id, sess=int(sess_of[di]), t=tt, active=tt <= ACTIVE_END.timestamp(), P=i_self, Q=int(j),
            linked=is_l, hit=bool(hit[j]),
            bracket=is_l and pages[j].title in bracket,
            same_label=creator_label[j] != "" and creator_label[j] == creator_label[i_self],
            any_label=len(lab_before(j, tt) & lab_before(i_self, tt) - {""}) > 0,
            same_ip=creator_ip[j] != "" and creator_ip[j] == creator_ip[i_self],
            same_family=family[j] == family[i_self],
            prefix=common_prefix(low[j], low[i_self]),
            rankdist=int(abs(sort_rank[j] - sort_rank[i_self])),
            d_create=abs(created[j] - created[i_self]),
            d_lastsave=abs(last_save_before(j, tt) - p_last),
            q_lastsave_age=tt - last_save_before(j, tt),
        ))
    ev_id += 1

print("events", ev_id, "rows", len(rows))
L = [r for r in rows if r["linked"]]
C = [r for r in rows if not r["linked"]]
print("linked", len(L), sum(r["hit"] for r in L), "control", len(C), sum(r["hit"] for r in C))
OUTJ = {"events": ev_id, "linked_rows": len(L), "linked_hits": sum(r["hit"] for r in L), "control_rows": len(C), "control_hits": sum(r["hit"] for r in C), "distinct_linked_pages": len({r["Q"] for r in L})}


# ---- 1. session-cluster bootstrap of the MH RR, for several adjustment sets
bins = [0, 120, 600, 1800, 3 * 3600, 24 * 3600, 1e18]


def b(x):
    for i in range(len(bins) - 1):
        if bins[i] <= x < bins[i + 1]:
            return i


pb = lambda r: 0 if r["prefix"] <= 2 else 1 if r["prefix"] <= 5 else 2 if r["prefix"] <= 9 else 3
keys = {
    "event": lambda r: (r["ev"],),
    "event+label": lambda r: (r["ev"], r["any_label"]),
    "event+lastsave": lambda r: (r["ev"], b(r["d_lastsave"])),
    "event+label+lastsave": lambda r: (r["ev"], r["any_label"], b(r["d_lastsave"])),
    "event+label+lastsave+prefix+family": lambda r: (r["ev"], r["any_label"], b(r["d_lastsave"]), pb(r), r["same_family"]),
}
rng = np.random.default_rng(1)
for name, key in keys.items():
    st = defaultdict(lambda: [0, 0, 0, 0, None])
    for r in rows:
        s = st[key(r)]
        s[4] = r["sess"]
        if r["linked"]:
            s[0] += r["hit"]; s[1] += 1
        else:
            s[2] += r["hit"]; s[3] += 1
    num_s, den_s = defaultdict(float), defaultdict(float)
    for a, n1, cc, n0, ss in st.values():
        if n1 and n0:
            n = n1 + n0
            num_s[ss] += a * n0 / n
            den_s[ss] += cc * n1 / n
    S = sorted(set(num_s) | set(den_s))
    num = np.array([num_s[s] for s in S]); den = np.array([den_s[s] for s in S])
    est = num.sum() / den.sum()
    # resample all 58 sessions that carry events
    all_s = sorted(set(r["sess"] for r in rows))
    pos = {s: i for i, s in enumerate(S)}
    vec_n = np.array([num_s.get(s, 0.0) for s in all_s]); vec_d = np.array([den_s.get(s, 0.0) for s in all_s])
    bs = []
    for _ in range(4000):
        k = np.bincount(rng.integers(0, len(all_s), len(all_s)), minlength=len(all_s))
        dd = (k * vec_d).sum()
        if dd > 0:
            bs.append((k * vec_n).sum() / dd)
    OUTJ.setdefault("mh", {})[name] = {"rr": round(float(est), 2), "lo": round(float(np.percentile(bs, 2.5)), 2), "hi": round(float(np.percentile(bs, 97.5)), 2)}
    print(f"{name:40s} MH RR {est:.2f}  session bootstrap 95% {np.percentile(bs, 2.5):.2f}-{np.percentile(bs, 97.5):.2f}")

# ---- 2. direction test vs creation order (recency confound)
titles = {p.title: k for k, p in c.pages.items()}
tset = set(titles)
dp = [p for p in c.pages.values() if p.deleted is not None]
dt = np.array([p.deleted.timestamp() for p in dp])
ct = np.array([p.created.timestamp() for p in dp])
idx = {p.key: i for i, p in enumerate(dp)}
W = 1800
cells = Counter()
for p in dp:
    if not p.bodies:
        continue
    body = ""
    for bt, _, bb in p.bodies:
        if bt <= p.deleted:
            body = bb
    linked = {idx[titles[t]] for t in extract_links(body, tset) - {p.title} if titles[t] in idx}
    i = idx[p.key]
    near = np.flatnonzero((np.abs(dt - dt[i]) <= W) & (dt != dt[i]))
    for j in near:
        older = ct[j] < ct[i]
        after = dt[j] > dt[i]
        cells[(j in linked, older, after)] += 1
print("\ndirection cells (linked, Q older than P, Q deleted after P): count")
for lk in (True, False):
    for older in (True, False):
        a, bf = cells[(lk, older, True)], cells[(lk, older, False)]
        OUTJ.setdefault("direction_cells", []).append({"linked": lk, "target_older": older, "after": a, "before": bf})
        print(f"linked={lk} Q_older={older}: after {a}, before {bf}, share after {a / max(1, a + bf):.3f}")

# ---- 3. moderator order: share of consecutive deletions newest-first by last save (Recent Changes)
times = [t for t, _ in c.deletions]
def last_save(k, t):
    p = c.pages.get(k)
    if not p or not p.bodies:
        return None
    st = [bt for bt, _, _ in p.bodies if bt <= t]
    return st[-1] if st else None
res = []
for s, e in sessions(times, 30):
    if e - s < 20:
        continue
    ls = [last_save(k, t) for t, k in c.deletions[s:e]]
    pairs = [(a, bb) for a, bb in zip(ls, ls[1:]) if a and bb and a != bb]
    if len(pairs) < 10:
        continue
    desc = sum(a > bb for a, bb in pairs) / len(pairs)
    res.append((times[s], e - s, round(desc, 2)))
print("\nsessions >=20: share of consecutive pairs newest-first by last save")
print("active:", [(str(t)[:16], n, d) for t, n, d in res if t <= ACTIVE_END])
aft = [d for t, n, d in res if t > ACTIVE_END]
OUTJ["recency_sessions"] = [{"start": t.isoformat(), "n": n, "newest_first_share": d} for t, n, d in res]
print("after: n", len(aft), "median", np.median(aft), ">=0.65:", sum(d >= 0.65 for d in aft), "<=0.35:", sum(d <= 0.35 for d in aft))

# ---- 4. the 15:44 session: is it just the top of Recent Changes?
T0 = datetime(2026, 6, 19, 15, 44, tzinfo=timezone.utc)
alive = [p for p in c.pages.values() if p.created < T0 and (p.deleted is None or p.deleted >= T0)]
def ls_before(p, t):
    st = [bt for bt, _, _ in p.bodies if bt < t]
    return st[-1] if st else p.created
top = sorted(alive, key=lambda p: ls_before(p, T0), reverse=True)[:14]
print("\nalive at 15:44 by last save (newest first): last save | deleted | title")
for p in top:
    print(ls_before(p, T0).strftime("%H:%M:%S"), p.deleted.strftime("%m-%d %H:%M:%S") if p.deleted else None, p.title)

(Path(ROOT) / "out" / "confounds.json").write_text(json.dumps(OUTJ, indent=2, default=str))

# ---- 5. edit-proximity predictor in the same candidate pool (within-event MH, session bootstrap)
def mh_by(pred, key=lambda r: (r["ev"],)):
    st = defaultdict(lambda: [0, 0, 0, 0, None])
    for r in rows:
        s = st[key(r)]
        s[4] = r["sess"]
        if pred(r):
            s[0] += r["hit"]; s[1] += 1
        else:
            s[2] += r["hit"]; s[3] += 1
    num_s, den_s = defaultdict(float), defaultdict(float)
    for a_, n1, cc, n0, ss in st.values():
        if n1 and n0:
            n = n1 + n0
            num_s[ss] += a_ * n0 / n
            den_s[ss] += cc * n1 / n
    all_s = sorted(set(r["sess"] for r in rows))
    vn = np.array([num_s.get(s, 0.0) for s in all_s]); vd = np.array([den_s.get(s, 0.0) for s in all_s])
    rng2 = np.random.default_rng(5)
    bs = []
    for _ in range(4000):
        k = np.bincount(rng2.integers(0, len(all_s), len(all_s)), minlength=len(all_s))
        if (k * vd).sum() > 0:
            bs.append((k * vn).sum() / (k * vd).sum())
    return {"rr": round(float(vn.sum() / vd.sum()), 2), "lo": round(float(np.percentile(bs, 2.5)), 2),
            "hi": round(float(np.percentile(bs, 97.5)), 2), "pred_rows": sum(pred(r) for r in rows),
            "pred_hits": sum(r["hit"] for r in rows if pred(r))}


OUTJ["edited_within_10min"] = mh_by(lambda r: r["d_lastsave"] <= 600)
OUTJ["linked_active_only_event_mh"] = None
act_rows = [r for r in rows if r["active"]]
if act_rows:
    saved = rows
    rows = act_rows
    OUTJ["linked_active_only_event_mh"] = mh_by(lambda r: r["linked"])
    rows = saved
print("edit within 10 min:", OUTJ["edited_within_10min"], "active-only linked:", OUTJ["linked_active_only_event_mh"])

# ---- 6. ZZ naming before/after the notice, late-alphabet risk ratio interval, re-creations, page accounting
from scipy import stats as _st  # noqa: E402
res_json = json.loads((Path(ROOT) / "out" / "results.json").read_text())
q4 = res_json["q4_response"]
zz_tab = [[q4["zz_after"], q4["new_pages_after_notice_to_jun22"] - q4["zz_after"]],
          [q4["zz_before"], q4["new_pages_3d_before_notice"] - q4["zz_before"]]]
f = _st.fisher_exact(zz_tab, alternative="greater")
OUTJ["zz_naming"] = {"odds_ratio": round(float(f.statistic), 2), "p_one_sided": round(float(f.pvalue), 3)}
la = res_json["q2_survival"]["late_active"]
a1, n1, a0, n0 = la["exposed_deleted"], la["exposed_rows"], la["unexposed_deleted"], la["unexposed_rows"]
rr = (a1 / n1) / (a0 / n0)
se = (1 / a1 - 1 / n1 + 1 / a0 - 1 / n0) ** 0.5
OUTJ["late_alphabet_rr"] = {"rr": round(rr, 2), "lo": round(float(np.exp(np.log(rr) - 1.96 * se)), 2),
                            "hi": round(float(np.exp(np.log(rr) + 1.96 * se)), 2)}
recre = [(p["page_key"], p["n_recreations"]) for p in meta.values() if p.get("n_recreations")]
OUTJ["recreations"] = {"pages": len(recre), "total": int(sum(n for _, n in recre))}
dk = [k for _, k in c.deletions]
OUTJ["deletion_accounting"] = {"deletions": len(dk), "distinct_pages_deleted": len(set(dk)),
                               "deletions_on_pages_never_captured": sum(k not in c.pages for k in dk),
                               "distinct_uncaptured_pages": len({k for k in dk if k not in c.pages}),
                               "repeat_deletions": len(dk) - len(set(dk))}
# ---- 7. the June 19 sweep that was running when the notice went up
j19 = [(t.isoformat(), c.pages[k].title if k in c.pages else k.split("~", 1)[1]) for t, k in c.deletions
       if datetime(2026, 6, 19, 13, 30, tzinfo=timezone.utc) <= t <= datetime(2026, 6, 19, 14, 40, tzinfo=timezone.utc)]
OUTJ["jun19_1330_session_tail"] = j19[-12:]
print(OUTJ["zz_naming"], OUTJ["late_alphabet_rr"], OUTJ["recreations"], OUTJ["deletion_accounting"])
print(OUTJ["jun19_1330_session_tail"])
(Path(ROOT) / "out" / "confounds.json").write_text(json.dumps(OUTJ, indent=2, default=str))
