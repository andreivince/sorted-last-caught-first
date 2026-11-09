import json, sys, collections, datetime as dt
from pathlib import Path
raw = Path(sys.argv[1])
ev = [json.loads(l) for l in open(raw / 'events.jsonl')]
T = lambda s: dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
dels = sorted([e for e in ev if e['event_type'] == 'delete'], key=lambda e: e['time'])
print('deletions', len(dels), 'actors', collections.Counter(e.get('actor_label') for e in dels).most_common(5))
print('wikis', collections.Counter(e['wiki'] for e in dels))
# sessions: gap > 30 min
sess, cur = [], [dels[0]]
for a, b in zip(dels, dels[1:]):
    if (T(b['time']) - T(a['time'])).total_seconds() > 1800: sess.append(cur); cur = []
    cur.append(b)
sess.append(cur)
def rank(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0]*len(xs)
    for k, i in enumerate(o): r[i] = k
    return r
def spearman(a, b):
    n = len(a); ra, rb = rank(a), rank(b)
    ma, mb = sum(ra)/n, sum(rb)/n
    num = sum((x-ma)*(y-mb) for x, y in zip(ra, rb))
    den = (sum((x-ma)**2 for x in ra) * sum((y-mb)**2 for y in rb)) ** .5
    return num/den if den else float('nan')
print('sessions', len(sess))
rows = []
for s in sess:
    if len(s) < 10: continue
    names = [e['page'].lower() for e in s]
    rho = spearman(list(range(len(s))), names)
    rows.append((s[0]['time'][:16], len(s), round(rho, 3), names[0][:18], names[-1][:18]))
for r in rows: print(r)
big = [r for r in rows if r[1] >= 20]
print('sessions>=20:', len(big), 'rho>0.9:', sum(r[2] > 0.9 for r in big), 'rho>0.5:', sum(r[2] > 0.5 for r in big))
# ZZZ / late-alphabet titles among saves
saves = [e for e in ev if e['event_type'] == 'save']
first = {}
for e in sorted(saves, key=lambda e: e['time']):
    first.setdefault(e['page_key'], e)
zz = [e for e in first.values() if e['page'].lower().startswith('zz') or 'zzz' in e['page'].lower()]
print('pages with zz prefix or zzz in name:', len(zz))
byday = collections.Counter(e['time'][:10] for e in zz); print(sorted(byday.items())[:30])
print('save days range', min(e['time'] for e in saves)[:10], max(e['time'] for e in saves)[:10])
