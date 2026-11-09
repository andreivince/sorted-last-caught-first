"""Loading and normalising the collusion.wiki export (DSE wiki only)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

WIKI = "dse"
LINK_BRACKET = re.compile(r"\[\[([^\]|#]+)")
CAMEL = re.compile(r"(?<![A-Za-z0-9])([A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]*)+)(?![A-Za-z0-9])")


def ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass
class Page:
    key: str
    title: str
    created: datetime
    deleted: datetime | None = None
    body_bytes: int = 0
    family: str = "unknown"
    last_body: str = ""
    bodies: list[tuple[datetime, str, str]] = field(default_factory=list)  # (time, sha256, body)


@dataclass
class Corpus:
    pages: dict[str, Page]
    deletions: list[tuple[datetime, str]]  # (time, page key), sorted
    saves: list[tuple[datetime, str]]


def extract_links(body: str, titles: set[str]) -> set[str]:
    """Agent page titles referenced from a wiki body, by [[link]] or bare CamelCase word."""
    found = {m.strip() for m in LINK_BRACKET.findall(body or "")}
    found |= set(CAMEL.findall(body or ""))
    return {t for t in found if t in titles}


def load(raw: Path) -> Corpus:
    events = [json.loads(line) for line in open(raw / "events.jsonl")]
    meta = {}
    for line in open(raw / "pages.jsonl"):
        p = json.loads(line)
        if p["wiki"] == WIKI:
            meta[p["page_key"]] = p
    pages: dict[str, Page] = {}
    deletions, saves = [], []
    for e in sorted(events, key=lambda e: e["time"]):
        if e.get("wiki") != WIKI:
            continue
        t = ts(e["time"])
        if e["event_type"] == "save":
            saves.append((t, e["page_key"]))
            if e["page_key"] not in pages:
                m = meta.get(e["page_key"], {})
                pages[e["page_key"]] = Page(e["page_key"], e["page"], t, body_bytes=m.get("body_bytes", 0),
                                            family=m.get("page_family") or "unknown")
        elif e["event_type"] == "delete":
            deletions.append((t, e["page_key"]))
            if e["page_key"] in pages and pages[e["page_key"]].deleted is None:
                pages[e["page_key"]].deleted = t
    for line in open(raw / "revisions.jsonl"):
        r = json.loads(line)
        if r.get("wiki") != WIKI or r["page_key"] not in pages:
            continue
        pages[r["page_key"]].bodies.append((ts(r["time"]), r.get("body_sha256") or "", r.get("body") or ""))
    for p in pages.values():
        p.bodies.sort(key=lambda b: b[0])
        if p.bodies:
            p.last_body = p.bodies[-1][2]
    return Corpus(pages, deletions, saves)


def sessions(times: list[datetime], gap_minutes: float = 30) -> list[tuple[int, int]]:
    """Index ranges [start, end) of runs whose consecutive gaps are at most gap_minutes."""
    out, start = [], 0
    for i in range(1, len(times)):
        if (times[i] - times[i - 1]).total_seconds() > gap_minutes * 60:
            out.append((start, i))
            start = i
    if times:
        out.append((start, len(times)))
    return out
