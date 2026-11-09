import json, sys, random, collections, statistics as st, datetime as dt
from pathlib import Path
raw = Path(sys.argv[1]); random.seed(7)
ev = [json.loads(l) for l in open(raw / 'events.jsonl')]
pages = {p['page_key']: p for p in map(json.loads, open(raw / 'pages.jsonl'))}
revs = [json.loads(l) for l in open(raw / 'revisions.jsonl')]
T = lambda s: dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
dse = sorted([e for e in ev if e.get('wiki') == 'dse'], key=lambda e: e['time'])
first, firstdel = {}, {}
for e in dse:
    if e['event_type'] == 'save': first.setdefault(e['page_key'], e)
    if e['event_type'] == 'delete': firstdel.setdefault(e['page_key'], e['time'])
late = lambda n: n.lower()[:1] in 'yz'
print('== 1. Daily creations vs deletions (dse)')
cr = collections.Counter(f['time'][:10] for f in first.values()); de = collections.Counter(t[:10] for t in firstdel.values())
for d in sorted(set(cr) | set(de)):
    if '2026-06-15' <= d <= '2026-06-27': print(' ', d, 'created', cr[d], 'deleted', de[d])
print('== 2. Permutation test: 24h deletion share, late (y/z) vs rest, pages alive at cut')
def test(cut_s, hours, label):
    cut = T(cut_s)
    alive = [k for k, f in first.items() if T(f['time']) < cut and (k not in firstdel or T(firstdel[k]) >= cut)]
    y = [1 if (k in firstdel and (T(firstdel[k]) - cut).total_seconds() < hours * 3600) else 0 for k in alive]
    g = [late(first[k]['page']) for k in alive]
    def diff(g):
        L = [a for a, b in zip(y, g) if b]; R = [a for a, b in zip(y, g) if not b]
        return (sum(R)/len(R) - sum(L)/len(L)) if L and R else 0
    obs = diff(g); cnt = 0
    for _ in range(5000):
        h = g[:]; random.shuffle(h); cnt += diff(h) >= obs
    L = sum(g); print(f'  {label}: alive {len(alive)}, late {L}, late deleted {sum(a for a,b in zip(y,g) if b)}, rest rate {sum(a for a,b in zip(y,g) if not b)/(len(g)-L):.3f}, diff {obs:.3f}, p = {cnt/5000:.4f}')
test('2026-06-19T13:30:00Z', 24, 'Jun 19 cut, 24h')
test('2026-06-19T13:30:00Z', 72, 'Jun 19 cut, 72h')
print('== 3. Placebo cuts (should show little or no late-alphabet advantage if it is the active-fight pattern)')
for c in ('2026-06-26T00:00:00Z', '2026-07-02T00:00:00Z', '2026-07-08T00:00:00Z'):
    test(c, 24, 'placebo ' + c[:10])
print('== 4. Confound: are late-alphabet pages different? (alive at Jun 19 cut)')
cut = T('2026-06-19T13:30:00Z')
alive = [k for k, f in first.items() if T(f['time']) < cut and (k not in firstdel or T(firstdel[k]) >= cut)]
for name, sel in (('late y/z', lambda k: late(first[k]['page'])), ('rest', lambda k: not late(first[k]['page']))):
    ks = [k for k in alive if sel(k)]
    bb = [pages[k]['body_bytes'] for k in ks if k in pages]; nr = [pages[k]['n_revs'] for k in ks if k in pages]
    age = [(cut - T(first[k]['time'])).total_seconds()/86400 for k in ks]
    fam = collections.Counter(pages[k]['page_family'] for k in ks if k in pages).most_common(3)
    print(f'  {name}: n {len(ks)}, median bytes {st.median(bb)}, median revs {st.median(nr)}, median age days {st.median(age):.1f}, top families {fam}')
print('== 5. Do zz pages created Jun 18 survive because of the name? Same-day matched comparison')
d18 = [k for k, f in first.items() if f['time'][:10] == '2026-06-18']
for name, sel in (('zz', lambda n: n.lower().startswith('zz')), ('other', lambda n: not n.lower().startswith('zz'))):
    ks = [k for k in d18 if sel(first[k]['page'])]
    xs = [(T(firstdel[k]) - T(first[k]['time'])).total_seconds()/86400 for k in ks if k in firstdel]
    print(f'  created Jun 18, {name}: n {len(ks)}, deleted {len(xs)}, median days to delete {st.median(xs):.2f}' if xs else f'  {name}: n {len(ks)}')
print('== 6. When did agents write about the sweep? First revisions mentioning alphabet + delet/lösch')
hits = sorted((r['time'], r['name'], (r.get('body') or '')) for r in revs if r.get('wiki') == 'dse' and 'alphabet' in (r.get('body') or '').lower() and any(w in (r.get('body') or '').lower() for w in ('delet', 'lösch', 'admin', 'sweep', 'remov')))
print('  count', len(hits))
for t, n, b in hits[:6]:
    i = b.lower().find('alphabet'); print('  ', t[:16], n, '|', b[max(0, i-120):i+120].replace('\n', ' '))
print('== 7. Re-creation: deleted pages whose exact body reappears on another page within 72h')
bodyfirst = collections.defaultdict(list)
for r in revs:
    if r.get('wiki') == 'dse' and r.get('body_sha256'): bodyfirst[r['body_sha256']].append((r['time'], r['page_key']))
rec = tot = 0
for k, td in firstdel.items():
    if k not in first: continue
    shas = {r['body_sha256'] for r in revs if r.get('page_key') == k} if False else None
recs = collections.defaultdict(set)
for r in revs:
    if r.get('wiki') == 'dse': recs[r['page_key']].add(r.get('body_sha256'))
for k, td in firstdel.items():
    if td > '2026-06-23': continue
    tot += 1; t0 = T(td)
    found = any(pk != k and 0 <= (T(t) - t0).total_seconds() <= 72*3600 for s in recs[k] if s for t, pk in bodyfirst[s])
    rec += found
print(f'  deletions Jun 4 to 22: {tot}, with exact body re-posted elsewhere within 72h: {rec}')
samename = sum(1 for k, p in pages.items() if p['wiki'] == 'dse' and p['n_recreations'] > 0)
print('  dse pages with n_recreations > 0:', samename)
print('== 8. Did the moderator adapt? Position of ZZZ pages in the Jun 19 15:44 session')
dels = [e for e in dse if e['event_type'] == 'delete' and '2026-06-19T15:44' <= e['time'] <= '2026-06-19T17:30']
for i, e in enumerate(dels):
    if e['page'].lower().startswith('zz'): print(f'  {i+1} of {len(dels)}: {e["page"]} at {e["time"][11:16]}')
