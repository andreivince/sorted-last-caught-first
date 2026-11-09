import json, sys, collections, statistics as st, datetime as dt
from pathlib import Path
raw = Path(sys.argv[1])
ev = [json.loads(l) for l in open(raw / 'events.jsonl')]
T = lambda s: dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
END = T('2026-07-15T00:00:00Z')
dse = [e for e in ev if e.get('wiki') == 'dse']
first, firstdel = {}, {}
for e in sorted(dse, key=lambda e: e['time']):
    if e['event_type'] == 'save': first.setdefault(e['page_key'], e)
    if e['event_type'] == 'delete': firstdel.setdefault(e['page_key'], e['time'])
def late(name):
    n = name.lower()
    return n.startswith('zz') or n.startswith('zzz')
def grp(name):
    c = name.lower()[:1]
    return 'zz' if late(name) else ('y-z' if c in 'yz' else ('a-c' if c in 'abc' else 'd-x'))
def summarize(label, keys):
    rows = collections.defaultdict(list); cens = collections.Counter()
    for k in keys:
        f = first[k]; t0 = T(f['time'])
        if k in firstdel: rows[grp(f['page'])].append((T(firstdel[k]) - t0).total_seconds() / 86400)
        else: cens[grp(f['page'])] += 1
    print(label)
    for g in ('a-c', 'd-x', 'y-z', 'zz'):
        xs = rows[g]
        if xs or cens[g]:
            print(f'  {g:4} deleted {len(xs):5}  never deleted {cens[g]:4}  median days to delete {st.median(xs):.2f}' if xs else f'  {g:4} deleted 0 never {cens[g]}')
# pages alive at the start of the first big sweep (Jun 19 13:30Z), created before it
cut = T('2026-06-19T13:30:00Z')
alive = [k for k, f in first.items() if T(f['time']) < cut and (k not in firstdel or T(firstdel[k]) >= cut)]
summarize('Pages alive at Jun 19 13:30 UTC (created before):', alive)
# among those, time from cut to deletion vs alphabetical position
pos = []
for k in alive:
    name = first[k]['page'].lower()
    d = (T(firstdel[k]) - cut).total_seconds() / 86400 if k in firstdel else None
    pos.append((name, d))
deleted = [(n, d) for n, d in pos if d is not None]
def rank(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0]*len(xs)
    for j, i in enumerate(o): r[i] = j
    return r
a = rank([n for n, _ in deleted]); b = rank([d for _, d in deleted]); n = len(a)
ma, mb = sum(a)/n, sum(b)/n
rho = sum((x-ma)*(y-mb) for x, y in zip(a, b)) / (sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b))**.5
print(f'  alive pages {len(alive)}, deleted later {n}; spearman(alphabet rank, time to deletion) = {rho:.3f}')
first3 = [d for nme, d in deleted if d < 3]
print('  deleted within 3 days of cut:', len(first3))
# by first letter: share deleted within 1 day of cut
byl = collections.defaultdict(lambda: [0, 0])
for nme, d in pos:
    g = grp(nme); byl[g][1] += 1
    if d is not None and d < 1: byl[g][0] += 1
print('  share deleted within 24h of cut:', {g: f'{v[0]}/{v[1]}' for g, v in byl.items()})
# pages created Jun 19 13:30 to Jun 22 (the fight window), zz vs others
win = [k for k, f in first.items() if cut <= T(f['time']) < T('2026-06-23T00:00:00Z')]
summarize('Pages created Jun 19 13:30 to Jun 22 UTC:', win)
zzs = sorted((first[k]['time'], first[k]['page'], firstdel.get(k)) for k in first if late(first[k]['page']))
print('ZZ pages created on or after Jun 18:', [(t[:16], p, (d or 'never')[:16]) for t, p, d in zzs if t >= '2026-06-18'])
