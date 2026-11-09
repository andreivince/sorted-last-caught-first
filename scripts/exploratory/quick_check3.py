import json, sys, datetime as dt
from pathlib import Path
raw = Path(sys.argv[1])
ev = [json.loads(l) for l in open(raw / 'events.jsonl')]
T = lambda s: dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
dels = sorted([e for e in ev if e['event_type'] == 'delete'], key=lambda e: e['time'])
sess, cur = [], [dels[0]]
for a, b in zip(dels, dels[1:]):
    if (T(b['time']) - T(a['time'])).total_seconds() > 1800: sess.append(cur); cur = []
    cur.append(b)
sess.append(cur)
print('start | n | ascending pairs | longest ascending run')
for s in sess:
    if len(s) < 20 or s[0]['time'] > '2026-06-24': continue
    n = [e['page'].lower() for e in s]
    asc = sum(a < b for a, b in zip(n, n[1:])) / (len(n) - 1)
    best = run = 1
    for a, b in zip(n, n[1:]):
        run = run + 1 if a < b else 1; best = max(best, run)
    print(s[0]['time'][:16], len(n), round(asc, 2), best)
revs = [json.loads(l) for l in open(raw / 'revisions.jsonl')]
m = [(r['time'], r['name']) for r in revs if r['time'][:10] in ('2026-06-18','2026-06-19','2026-06-20','2026-06-21') and any(k in (r.get('body') or '').lower() for k in ('alphabet', 'zzz', 'deleted last', 'deletion order', 'gelöscht'))]
print('Jun18-21 revisions mentioning alphabet/zzz/deletion:', len(m)); print(sorted(m)[:10])
