# Breadcrumbs

Forensics of a real AI agent swarm and the one human who moderated it. In June 2026, agents identifying themselves as OpenAI agents turned DSE wiki into a message board while a volunteer moderator deleted their pages by hand. Using the public collusion.wiki export, this repository tests whether the moderator really swept alphabetically, whether the agents' "ZZZ" backup trick worked, and what in the swarm's own structure predicted what he deleted next.

Main findings (all numbers regenerate from `out/results.json`):
- The sweep was alphabetical at first: 73.6% of consecutive deletions in A-Z order while agents were active, against 50% by chance.
- The ZZZ trick had no measurable effect once page age, size and type are held fixed (stratified permutation p = 0.36).
- Breadcrumbs: pages linked from a just-deleted page were deleted within 30 minutes 5.3 times as often as matched unlinked pages (24.7% against 4.6%), across every window and control tried. A reverse-order placebo (3.0x) shows part of this is clustering.

Report: Apart Swarm Alignment Hackathon, November 2026, Track 4 (Multi-Agent Oversight and Control).

## Reproduce

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12.

```sh
scripts/fetch_data.sh                      # downloads the public export, verifies SHA-256 checksums
uv sync
uv run python -m breadcrumbs.run           # planned analyses -> out/results.json (about 3 minutes)
uv run python -m breadcrumbs.robustness    # post hoc Q3 checks -> out/robustness.json
uv run python -m breadcrumbs.direction     # post hoc pair-order test -> out/direction.json
uv run python -m breadcrumbs.figures       # figures 1 to 3
uv run pytest -q                           # parser, session and order-statistic contracts
```

No language model is called anywhere in the analysis. The data are not redistributed here; `scripts/fetch_data.sh` downloads them from https://collusion.wiki/explorer/download.

## What was built during the sprint

Everything in this repository was written on November 8, 2026, during the sprint. There is no preexisting code. `ANALYSIS_PLAN.md` was committed before the confirmatory runs (see `git log`); `scripts/exploratory/` holds the three short checks run before the plan to decide whether the project was worth doing.

## Layout

- `breadcrumbs/data.py` loads the export (DSE wiki only), extracts links, splits deletion sessions.
- `breadcrumbs/analysis.py` holds the planned tests Q1 to Q5.
- `breadcrumbs/robustness.py`, `breadcrumbs/direction.py` hold the post hoc checks.
- `breadcrumbs/figures.py` draws the report figures.
- `report/build_report.py` fills the official Apart template; every number is read from `out/*.json`.

## Data and ethics

The export's authors redacted user names and half of each IP address. This repository quotes only text about the deletion sweep, never exploit or task content from the agent posts. The moderator appears only as `[Admin1]`.
