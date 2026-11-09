import json, sys, collections, datetime as dt
from pathlib import Path
raw = Path(sys.argv[1])
ev = [json.loads(l) for l in open(raw / 'events.jsonl')]
pages = {p['page_key']: p for p in map(json.loads, open(raw / 'pages.jsonl'))}
T = lambda s: dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
saves = sorted([e for e in ev if e['event_type'] == 'save'], key=lambda e: e['time'])
firstsave, lastsave = {}, {}
for e in saves:
    firstsave.setdefault(e['page_key'], e['time']); lastsave[e['page_key']] = e['time']
dels = sorted([e for e in ev if e['event_type'] == 'delete'], key=lambda e: e['time'])
sess, cur = [], [dels[0]]
for a, b in zip(dels, dels[1:]):
    if (T(b['time']) - T(a['time'])).total_seconds() > 1800: sess.append(cur); cur = []
    cur.append(b)
sess.append(cur)
def rank(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0]*len(xs)
    for k, i in enumerate(o): r[i] = k
    return r
def sp(a, b):
    n = len(a); ra, rb = rank(a), rank(b); ma, mb = sum(ra)/n, sum(rb)/n
    num = sum((x-ma)*(y-mb) for x, y in zip(ra, rb)); den = (sum((x-ma)**2 for x in ra)*sum((y-mb)**2 for y in rb))**.5
    return num/den if den else float('nan')
print('session start | n | rho_alpha | rho_firstwrite | rho_lastwrite')
agg = collections.Counter()
for s in sess:
    if len(s) < 20: continue
    idx = list(range(len(s)))
    a = sp(idx, [e['page'].lower() for e in s])
    fw = [firstsave.get(e['page_key'], '9') for e in s]; lw = [lastsave.get(e['page_key'], '9') for e in s]
    f = sp(idx, fw); l = sp(idx, lw)
    best = max((abs(a),'alpha'),(abs(f),'first'),(abs(l),'last'))[1]
    agg[(s[0]['time'][:10] <= '2026-06-22', best)] += len(s)
    print(s[0]['time'][:16], len(s), round(a,2), round(f,2), round(l,2))
print(agg)
# agent posts mentioning alphabet
revs = map(json.loads, open(raw / 'revisions.jsonl'))
hits = []
for r in revs:
    txt = json.dumps(r).lower()
    if 'alphabet' in txt or 'alphabetisch' in txt:
        hits.append((r.get('time') or r.get('timestamp') or '', r.get('page') or r.get('page_key')))
hits.sort(); print('revisions mentioning alphabet:', len(hits)); print(hits[:12])
