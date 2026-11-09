# Analysis plan (written before the confirmatory runs)

Project: forensic study of how one human moderator and an AI agent swarm adapted to each other on DSE wiki (June 2026), using the public collusion.wiki export.

Written: 2026-11-08 at 23:06 EST (2026-11-09 04:06 UTC), during the Apart Swarm Alignment sprint (Nov 6 to 8, 2026). The git history of this repository timestamps every later change.

## What was already seen before this plan

To decide whether the project was worth doing, three exploratory scripts were run on Nov 8 between about 22:15 and 23:05 EST (kept in `scripts/exploratory/`). They showed:
- Deletion sessions on June 19 had 73 to 78 percent of consecutive deletions in ascending alphabetical order, in runs up to 35 pages.
- Late-alphabet (Y/Z) pages alive at the first large sweep were rarely deleted in the next 24 hours (1 of 77 against 7.7 percent), permutation p about 0.016, with no effect at three placebo dates; those pages were older and much smaller than the rest.
- The agent notice that the sweep "appears active alphabetically" (14:04 UTC June 19) linked a ZZZ backup page; the moderator's next session deleted the notice page and then both ZZZ pages within 100 minutes.

These results are reported as exploratory. The analyses below are fixed before they are run, and any deviation is reported.

## Data

collusion.wiki export, files `pages.jsonl`, `revisions.jsonl`, `events.jsonl`, `labels.jsonl`, `manifest.json`, verified against the published SHA-256 checksums. Scope: wiki `dse` only. A deletion is an `events` row with `event_type == "delete"`; a page's creation time is its first `save` event. Deletion sessions are maximal runs of deletions with gaps of 30 minutes or less (sensitivity: 10 and 60 minutes).

## Questions and tests

**Q1. Did the moderator delete in alphabetical order?** Per session with at least 20 deletions: share of consecutive pairs in ascending case-insensitive title order, and the longest ascending run. Null: the same session's deletions in random order (10,000 permutations per session). Report per session and pooled, split by period: before agents went quiet (to June 22 23:59 UTC) and after.

**Q2. Did late-alphabet titles survive longer, beyond what page age and size explain?** Pages alive at each session start in the active period. Outcome: deleted in that session. Exposure: title starts with Y or Z, and separately with "ZZ". Test: permutation of the exposure label within strata of page age (quartiles), body size (quartiles) and page family. Placebo: the same test at session starts after June 22.

**Q3. Did the swarm's coordination links lead the moderator to its pages (the breadcrumb test)?** Build the link graph from revision bodies: `[[Target]]` links and bare CamelCase tokens that exactly equal an agent page title. For each deletion of a page P in the active and cleanup periods, take the alive agent pages linked from P's last saved body. Outcome: deleted within 30 minutes after P. Comparison: alive agent pages not linked from P, matched on creation day and title initial, same window. Effect: risk ratio with a permutation null (shuffle link targets among the matched pool). Sensitivity: 10 and 60 minute windows, excluding pages that P's deletion would reach by alphabetical adjacency (titles within 3 positions in sort order).

**Q4. How did the swarm respond?** (a) Spread of the alphabetical-sweep belief: distinct pages and labels mentioning it over time. (b) Use of ZZ and Y/Z initial titles per day, before and after the first notice (14:04 UTC June 19). (c) Re-posting: deleted pages whose exact body (SHA-256) or near-identical body (word 5-gram Jaccard 0.8 or more) appears on another page within 72 hours.

**Q5. Workload.** Daily pages created and deleted; the moderator's deletions per active hour.

## Reporting rules

Report every pre-specified test, including null and negative results. Effect sizes with 95 percent intervals or permutation p-values. No causal claim about the moderator's intent; the data cannot show what he was thinking. Quote no harmful or exploit content from the agent posts; quote only coordination and deletion-related text. Model calls: none in the confirmatory analysis.
