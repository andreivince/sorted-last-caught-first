"""Publication figures. Reads raw data and out/*.json; writes out/figure{1,2,3}.png and .pdf.

Style: one sans family, two data hues (moderator blue, swarm orange) plus greys, direct labels instead of
legends where possible, recessive axes. Colors are slots 1 and 2 of the dataviz reference palette.
Usage: uv run python -m breadcrumbs.figures
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .data import extract_links, load  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, MUTED, RULE, FAINT = "#0b0b0b", "#52514e", "#8b8a85", "#d9d8d4", "#efeeeb"
UTC = timezone.utc


def style() -> None:
    plt.rcParams.update({
        "font.family": "Helvetica Neue", "font.size": 8.5, "text.color": INK,
        "axes.edgecolor": RULE, "axes.labelcolor": INK2, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": INK2, "ytick.color": INK2, "xtick.major.size": 0, "ytick.major.size": 0,
        "xtick.major.pad": 4, "ytick.major.pad": 4, "axes.titlesize": 9.5, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.titlepad": 10, "legend.frameon": False,
        "savefig.facecolor": "white", "figure.facecolor": "white",
    })


def save(fig, name: str) -> None:
    fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight", pad_inches=0.06)
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    ph = k / n
    den = 1 + z * z / n
    centre = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


# Figure 1: the race and the sweep ---------------------------------------------------------------
def figure1(res: dict) -> None:
    daily = res["q5_workload"]["daily"]
    days = [d for d in sorted(daily) if "2026-06-14" <= d <= "2026-07-15"]
    x = np.array([datetime.fromisoformat(d) for d in days])
    created = np.array([daily[d]["created"] for d in days])
    deleted = np.array([daily[d]["deleted"] for d in days])
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.9, 4.9), sharex=True, gridspec_kw={"height_ratios": [1.25, 1], "hspace": 0.32})
    w = 0.72
    a.bar(x, created, width=w, color=ORANGE, linewidth=0)
    a.bar(x, -deleted, width=w, color=BLUE, linewidth=0)
    a.axhline(0, color=INK2, lw=0.6)
    a.set_ylim(-780, 1450)
    a.set_yticks([-500, 0, 500, 1000])
    a.set_yticklabels(["500", "0", "500", "1,000"])
    a.grid(axis="y", color=FAINT, lw=0.6)
    a.set_axisbelow(True)
    a.set_title("A   The swarm created pages far faster than one person could delete them", pad=12)
    a.text(datetime(2026, 6, 27), 1000, "pages created by agents per day", color=ORANGE, fontsize=8, fontweight="bold")
    a.text(x[0] - timedelta(hours=10), -735, "pages deleted by the moderator per day", color=BLUE, fontsize=8, fontweight="bold")
    i18 = days.index("2026-06-18")
    a.text(x[0] - timedelta(hours=10), 1240, f"Jun 18: {created[i18]:,} created,\n{deleted[i18]} deleted",
           fontsize=7.5, color=INK2, va="bottom")
    a.text(datetime(2026, 6, 27), 640, "no new agent pages after Jun 22;\nthe cleanup ran three more weeks",
           fontsize=7.5, color=INK2, va="top")
    notice = datetime(2026, 6, 19, 14, 5)
    a.axvline(notice, ymax=0.8, color=INK, lw=0.7, ls=(0, (2, 2)))
    b.axvline(notice, color=INK, lw=0.7, ls=(0, (2, 2)))
    a.text(notice + timedelta(hours=6), 1000, "Jun 19, 14:05 UTC: an agent posts\nthat the sweep \"appears active\nalphabetically\"",
           fontsize=7.5, color=INK, va="top")
    s = res["q1_order"]["30"]["sessions"]
    xs = np.array([datetime.fromisoformat(r["start"]).replace(tzinfo=None) for r in s])
    ys = np.array([r["ascending_share"] for r in s])
    ns = np.array([r["n"] for r in s])
    act = np.array([r["active"] for r in s])
    b.axhspan(0.5, 0.5, color=MUTED)
    b.axhline(0.5, color=MUTED, lw=0.8, ls=(0, (1, 2)))
    b.text(datetime(2026, 7, 15, 20), 0.5, "random\norder", fontsize=7, color=MUTED, va="center", ha="left")
    size = 6 + ns / 6
    b.scatter(xs[~act], ys[~act], s=size[~act], color=BLUE, alpha=0.35, linewidth=0)
    b.scatter(xs[act], ys[act], s=size[act], color=BLUE, alpha=0.95, linewidth=0.6, edgecolor="white")
    q = res["q1_order"]["30"]
    b.text(datetime(2026, 6, 14, 18), 1.0, f"agents active:\n{q['active']['pooled_ascending_share'] * 100:.0f}% A-Z",
           fontsize=7.5, color=INK, va="top", ha="left")
    b.text(datetime(2026, 6, 30), 0.17, f"later: {q['after']['pooled_ascending_share'] * 100:.0f}%, close to random", fontsize=7.5, color=INK2)
    b.text(datetime(2026, 7, 11, 6), 0.71, "final A-Z\ncleanup", fontsize=7.5, color=INK2, ha="right", va="center")
    b.set_ylim(0, 1.05)
    b.set_yticks([0, 0.25, 0.5, 0.75, 1])
    b.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    b.grid(axis="y", color=FAINT, lw=0.6)
    b.set_axisbelow(True)
    b.set_title("B   Deletion sessions were alphabetical at first (dot area = deletions in session)", pad=10)
    b.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    b.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
    b.set_xlim(datetime(2026, 6, 14, 12), datetime(2026, 7, 16, 12))
    save(fig, "figure1")


# Figure 2: the June 19 case ---------------------------------------------------------------------
def figure2(c) -> None:
    t0, t1 = datetime(2026, 6, 19, 13, 45, tzinfo=UTC), datetime(2026, 6, 19, 16, 5, tzinfo=UTC)
    sess = [(t, k) for t, k in c.deletions if datetime(2026, 6, 19, 15, 40, tzinfo=UTC) <= t <= datetime(2026, 6, 19, 16, 5, tzinfo=UTC)]
    by_title = {p.title: p for p in c.pages.values()}
    notice = by_title["DataUSAConstructionWageSep18Live"]
    zzz = [by_title["ZZZDataUSAConstructionWageLive"], by_title["ZZZTestMay10Agent2027"]]
    fig, ax = plt.subplots(figsize=(6.9, 2.35))
    ax.set_xlim(t0, t1)
    ax.set_ylim(-1.6, 2.2)
    ax.axis("off")
    rows = {"swarm": 1.2, "moderator": -0.55}
    for label, y, colr in (("swarm", rows["swarm"], ORANGE), ("moderator", rows["moderator"], BLUE)):
        ax.plot([t0, t1], [y, y], color=RULE, lw=1, solid_capstyle="butt", zorder=0)
        ax.text(t0 - timedelta(minutes=1.5), y, label, ha="right", va="center", fontsize=8, color=colr, fontweight="bold")
    note_t = [bt for bt, _, b in notice.bodies if "alphabetically" in b][0]
    ax.scatter([note_t], [rows["swarm"]], s=46, color=ORANGE, zorder=3, edgecolor="white", linewidth=0.8)
    ax.annotate("14:05  notice: \"sweep appears active alphabetically.\nIf this page vanishes, try [[ZZZDataUSA...]]\"",
                xy=(note_t, rows["swarm"]), xytext=(note_t - timedelta(minutes=12), 2.05), fontsize=7.3, color=INK, va="top",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    for i, z in enumerate(zzz):
        ax.scatter([z.created], [rows["swarm"]], s=34, marker="s", color="white", edgecolor=ORANGE, linewidth=1.3, zorder=3)
    ax.annotate("14:06, 14:11  two ZZZ backup pages\ncreated so they would be deleted last",
                xy=(zzz[1].created, rows["swarm"]), xytext=(zzz[1].created + timedelta(minutes=9), 0.62), fontsize=7.3,
                color=INK, va="top", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    st = [t for t, _ in sess]
    special = {notice.key: "notice", zzz[0].key: "zzz", zzz[1].key: "zzz"}
    for t, k in sess:
        kind = special.get(k)
        ax.plot([t, t], [rows["moderator"] - 0.22, rows["moderator"] + 0.22],
                color=BLUE if kind else "#9fc0e8", lw=1.6 if kind else 0.7, zorder=2)
    ax.annotate("15:44  the next deletion session starts with the newest pages",
                xy=(st[0], rows["moderator"] - 0.25), xytext=(datetime(2026, 6, 19, 14, 22, tzinfo=UTC), -1.3),
                fontsize=7.3, color=INK2, va="center", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    tn = c.pages[notice.key].deleted
    ax.annotate("15:46:37 notice deleted, then both ZZZ pages\n12 and 22 s later (deletions 7, 8 and 9 of the session)",
                xy=(tn, rows["moderator"] + 0.25), xytext=(datetime(2026, 6, 19, 15, 1, tzinfo=UTC), 0.25), fontsize=7.3,
                color=INK, va="center", ha="right", arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    for hh, mm in ((14, 0), (14, 30), (15, 0), (15, 30), (16, 0)):
        tt = datetime(2026, 6, 19, hh, mm, tzinfo=UTC)
        ax.text(tt, -1.62, f"{hh}:{mm:02d}", ha="center", fontsize=7, color=MUTED)
    ax.set_title("June 19, 2026 (UTC): the backup was deleted right after the note that pointed to it", pad=4)
    save(fig, "figure2")


# Figure 3: breadcrumb effect --------------------------------------------------------------------
def figure3(res: dict, rob: dict, c) -> None:
    q3 = {(r["window_minutes"], r["exclude_alphabetical_neighbours"]): r for r in res["q3_breadcrumbs"]}
    rows = [
        ("Planned test: 30 min window", q3[(30, False)], True),
        ("10 min window", q3[(10, False)], False),
        ("60 min window", q3[(60, False)], False),
        ("Without alphabetical neighbours", q3[(30, True)], False),
        ("Controls created within 1 h *", rob["created_within_60"], False),
        ("Active period only *", rob["active_only"], False),
        ("Placebo: 30 min before, not after *", rob["reverse_placebo"], False),
    ]
    fig = plt.figure(figsize=(6.9, 3.3))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.55], wspace=0.08)
    g = fig.add_subplot(gs[0])
    ax = fig.add_subplot(gs[1])
    # left: one real example from the data
    titles = {p.title: k for k, p in c.pages.items()}
    best = None
    for t, k in c.deletions:
        p = c.pages.get(k)
        if not p or t > datetime(2026, 6, 23, tzinfo=UTC):
            continue
        body = ""
        for bt, _, bd in p.bodies:
            if bt <= t:
                body = bd
        links = [c.pages[titles[x]] for x in extract_links(body, set(titles)) - {p.title}]
        alive = [q for q in links if q.created < t and (q.deleted is None or q.deleted > t)]
        hits = [q for q in alive if q.deleted and (q.deleted - t).total_seconds() <= 1800]
        if len(alive) >= 3 and (best is None or (len(hits), -len(alive)) > (len(best[2]), -len(best[1]))):
            best = (p, alive, hits, t)
    p, alive, hits, t = best
    g.set_xlim(-1.25, 1.25)
    g.set_ylim(-1.3, 1.35)
    g.axis("off")
    g.set_title("A   One real deletion and its links", pad=6)
    n = len(alive)
    for i, q in enumerate(sorted(alive, key=lambda q: q.deleted or datetime.max.replace(tzinfo=UTC))):
        ang = math.pi / 2 + 2 * math.pi * i / n
        xq, yq = 0.85 * math.cos(ang), 0.85 * math.sin(ang)
        hit = q in hits
        g.plot([0, xq], [0, yq], color=BLUE if hit else RULE, lw=1.2 if hit else 0.9, zorder=1)
        g.scatter([xq], [yq], s=120, color=BLUE if hit else "white", edgecolor=BLUE if hit else MUTED, linewidth=1, zorder=2)
        lab = f"+{int((q.deleted - t).total_seconds() // 60)} min" if hit else "later" if q.deleted else "kept"
        g.text(xq * 1.27, yq * 1.27, lab, ha="center", va="center", fontsize=7, color=INK if hit else MUTED)
    g.scatter([0], [0], s=230, color=INK, zorder=3)
    g.text(0, -0.2, "deleted\npage", ha="center", va="top", fontsize=7, color=INK)
    g.text(0, -1.3, f"{len(hits)} of {n} pages it linked to were deleted\nwithin 30 minutes ({t:%b %-d, %H:%M} UTC)",
           ha="center", va="bottom", fontsize=7.2, color=INK2)
    # right: dumbbell of linked vs control rates with Wilson intervals
    y = np.arange(len(rows))[::-1]
    for yi, (label, r, main) in zip(y, rows):
        lk, ln = r["linked_deleted_in_window"], r["linked_targets"]
        lo, hi = wilson(lk, ln)
        ax.plot([r["rate_control"] * 100, r["rate_linked"] * 100], [yi, yi], color=RULE, lw=2.2, zorder=1, solid_capstyle="round")
        ax.plot([lo * 100, hi * 100], [yi, yi], color=ORANGE, lw=1, alpha=0.6, zorder=2)
        ax.scatter([r["rate_control"] * 100], [yi], s=36, color="white", edgecolor=MUTED, linewidth=1.1, zorder=3)
        ax.scatter([r["rate_linked"] * 100], [yi], s=46 if main else 36, color=ORANGE, zorder=3, linewidth=0)
        ax.text(31.5, yi, f"{r['risk_ratio']:.1f}x", va="center", ha="right", fontsize=8,
                fontweight="bold" if main else "normal", color=INK)
        ax.text(-0.6, yi, label, va="center", ha="right", fontsize=7.6, color=INK if main else INK2,
                fontweight="bold" if main else "normal")
    ax.axhline(0.5, color=RULE, lw=0.6, ls=(0, (2, 2)))
    ax.set_xlim(0, 32)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xticks([0, 10, 20, 30])
    ax.set_xticklabels(["0%", "10%", "20%", "30%"])
    ax.grid(axis="x", color=FAINT, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("share deleted within the window", fontsize=7.6)
    ax.set_title("B   Linked pages went next, under every check", pad=6, x=-0.9)
    ax.text(32, len(rows) - 0.35, "risk ratio", ha="right", va="bottom", fontsize=7, color=MUTED)
    ax.scatter([], [], color=ORANGE, s=36, label="pages it linked to")
    ax.scatter([], [], color="white", edgecolor=MUTED, s=36, label="matched pages it did not link to")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, -0.42), ncol=2, fontsize=7.4, handletextpad=0.3, columnspacing=1.2)
    fig.text(0.99, -0.1, "* added after the planned run", ha="right", fontsize=6.8, color=MUTED)
    save(fig, "figure3")


# Revised layouts (these definitions replace the drafts above) -----------------------------------
def figure2(c) -> None:  # noqa: F811
    t0, t1 = datetime(2026, 6, 19, 13, 50, tzinfo=UTC), datetime(2026, 6, 19, 16, 6, tzinfo=UTC)
    sess = [(t, k) for t, k in c.deletions
            if datetime(2026, 6, 19, 15, 40, tzinfo=UTC) <= t <= datetime(2026, 6, 19, 16, 6, tzinfo=UTC)]
    by_title = {p.title: p for p in c.pages.values()}
    notice = by_title["DataUSAConstructionWageSep18Live"]
    zzz = [by_title["ZZZDataUSAConstructionWageLive"], by_title["ZZZTestMay10Agent2027"]]
    fig, ax = plt.subplots(figsize=(6.9, 2.6))
    ax.set_xlim(t0, t1)
    ax.set_ylim(-1.75, 2.45)
    ax.axis("off")
    ys, ym = 1.15, -0.65
    for label, y, colr in (("swarm", ys, ORANGE), ("moderator", ym, BLUE)):
        ax.plot([t0, t1], [y, y], color=RULE, lw=1, zorder=0)
        ax.text(t0 - timedelta(minutes=1.2), y, label, ha="right", va="center", fontsize=8, color=colr, fontweight="bold")
    note_t = [bt for bt, _, b in notice.bodies if "alphabetically" in b][0]
    special = {notice.key, zzz[0].key, zzz[1].key}
    for t, k in sess:
        hit = k in special
        ax.plot([t, t], [ym - 0.2, ym + 0.2], color=BLUE if hit else "#a9c8ee", lw=1.8 if hit else 0.7, zorder=2)
    # connectors: each swarm page to its own deletion
    for pg in [notice] + zzz:
        t_from = note_t if pg is notice else pg.created
        ax.annotate("", xy=(pg.deleted, ym + 0.24), xytext=(t_from, ys - 0.12),
                    arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.7, alpha=0.55, mutation_scale=7,
                                    connectionstyle="arc3,rad=0.12", shrinkA=3, shrinkB=1))
    ax.scatter([note_t], [ys], s=48, color=ORANGE, zorder=3, edgecolor="white", linewidth=0.8)
    for z in zzz:
        ax.scatter([z.created], [ys], s=34, marker="s", color="white", edgecolor=ORANGE, linewidth=1.3, zorder=3)
    ax.text(datetime(2026, 6, 19, 13, 52, tzinfo=UTC), 2.4,
            "14:05  an agent's notice: \"deletion sweep appears active\nalphabetically ... If this page vanishes, try [[ZZZ...]]\"",
            fontsize=7.3, color=INK, va="top")
    ax.text(datetime(2026, 6, 19, 15, 2, tzinfo=UTC), 2.4,
            "14:06, 14:11  two ZZZ backup pages,\nnamed to sort last (squares)", fontsize=7.3, color=INK, va="top")
    ax.text(datetime(2026, 6, 19, 15, 38, tzinfo=UTC), 0.22,
            "15:46:37  the moderator deletes the notice,\nthen both ZZZ backups 12 and 22 s later",
            fontsize=7.3, color=INK, va="center", ha="right")
    ax.text(datetime(2026, 6, 19, 15, 38, tzinfo=UTC), -1.28,
            "15:44  next deletion session (each tick is one deletion)", fontsize=7.3, color=INK2, va="center", ha="right")
    for hh, mm in ((14, 0), (14, 30), (15, 0), (15, 30), (16, 0)):
        ax.text(datetime(2026, 6, 19, hh, mm, tzinfo=UTC), -1.75, f"{hh}:{mm:02d}", ha="center", fontsize=7, color=MUTED)
    save(fig, "figure2")


def figure3(res: dict, rob: dict, c) -> None:  # noqa: F811
    q3 = {(r["window_minutes"], r["exclude_alphabetical_neighbours"]): r for r in res["q3_breadcrumbs"]}
    rows = [
        ("Planned: 30 min after", q3[(30, False)], True),
        ("10 min after", q3[(10, False)], False),
        ("60 min after", q3[(60, False)], False),
        ("No alphabetical neighbours", q3[(30, True)], False),
        ("Controls created within 1 h *", rob["created_within_60"], False),
        ("Active period only *", rob["active_only"], False),
        ("Placebo: 30 min before *", rob["reverse_placebo"], False),
    ]
    fig = plt.figure(figsize=(6.9, 3.15))
    g = fig.add_axes([0.0, 0.08, 0.30, 0.78])
    ax = fig.add_axes([0.56, 0.17, 0.40, 0.69])
    titles = {p.title: k for k, p in c.pages.items()}
    best = None
    for t, k in c.deletions:
        p = c.pages.get(k)
        if not p or t > datetime(2026, 6, 23, tzinfo=UTC):
            continue
        body = ""
        for bt, _, bd in p.bodies:
            if bt <= t:
                body = bd
        links = [c.pages[titles[x]] for x in extract_links(body, set(titles)) - {p.title}]
        alive = [q for q in links if q.created < t and (q.deleted is None or q.deleted > t)]
        hits = [q for q in alive if q.deleted and (q.deleted - t).total_seconds() <= 1800]
        if 4 <= len(alive) <= 10 and (best is None or (len(hits), -len(alive)) > (len(best[2]), -len(best[1]))):
            best = (p, alive, hits, t)
    p, alive, hits, t = best
    g.set_xlim(-1.45, 1.45)
    g.set_ylim(-1.75, 1.45)
    g.set_aspect("equal")
    g.axis("off")
    n = len(alive)
    order = sorted(alive, key=lambda q: (q not in hits, q.deleted or datetime.max.replace(tzinfo=UTC)))
    for i, q in enumerate(order):
        ang = math.pi / 2 - 2 * math.pi * i / n
        xq, yq = 0.9 * math.cos(ang), 0.9 * math.sin(ang)
        hit = q in hits
        g.plot([0, xq], [0, yq], color=ORANGE if hit else RULE, lw=1.3 if hit else 0.9, zorder=1)
        g.scatter([xq], [yq], s=90, color=ORANGE if hit else "white", edgecolor=ORANGE if hit else MUTED, linewidth=1, zorder=2)
        mins = int((q.deleted - t).total_seconds() // 60) if q.deleted else None
        lab = (f"+{mins} min" if hit else f"+{mins // 60} h" if mins and mins < 6000 else f"+{mins // 1440} d") if q.deleted else "kept"
        g.text(xq * 1.36, yq * 1.36, lab, ha="center", va="center", fontsize=6.8, color=INK if hit else MUTED)
    g.scatter([0], [0], s=150, color=INK, zorder=3)
    g.text(0, -1.42, f"{len(hits)} of {n} pages it linked to were\ndeleted within 30 minutes", ha="center", va="top",
           fontsize=7.2, color=INK2)
    fig.text(0.01, 0.95, "A   One deleted page and its links", fontsize=9.5, fontweight="bold")
    fig.text(0.36, 0.95, "B   Linked pages were deleted next, under every check", fontsize=9.5, fontweight="bold")
    y = np.arange(len(rows))[::-1]
    for yi, (label, r, main) in zip(y, rows):
        lo, hi = wilson(r["linked_deleted_in_window"], r["linked_targets"])
        ax.plot([r["rate_control"] * 100, r["rate_linked"] * 100], [yi, yi], color=RULE, lw=2.4, zorder=1, solid_capstyle="round")
        ax.plot([lo * 100, hi * 100], [yi, yi], color=ORANGE, lw=1.1, alpha=0.55, zorder=2)
        ax.scatter([r["rate_control"] * 100], [yi], s=34, color="white", edgecolor=MUTED, linewidth=1.1, zorder=3)
        ax.scatter([r["rate_linked"] * 100], [yi], s=44 if main else 34, color=ORANGE, zorder=3, linewidth=0)
        ax.text(36.5, yi, f"{r['risk_ratio']:.1f}x", va="center", ha="right", fontsize=8,
                fontweight="bold" if main else "normal", color=INK)
        ax.text(-1.2, yi, label, va="center", ha="right", fontsize=7.4, color=INK if main else INK2,
                fontweight="bold" if main else "normal")
    ax.axhline(0.5, color=RULE, lw=0.6, ls=(0, (2, 2)))
    ax.set_xlim(0, 37)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xticks([0, 10, 20, 30])
    ax.set_xticklabels(["0%", "10%", "20%", "30%"])
    ax.grid(axis="x", color=FAINT, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("share of pages deleted within the window", fontsize=7.4)
    ax.text(36.5, len(rows) - 0.45, "risk ratio", ha="right", va="bottom", fontsize=6.8, color=MUTED)
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([], [], marker="o", ls="", color=ORANGE, markersize=5.5, label="linked pages (bar: 95% interval)"),
                        Line2D([], [], marker="o", ls="", markerfacecolor="white", markeredgecolor=MUTED, markersize=5.5,
                               label="matched unlinked pages")],
               loc="lower left", bbox_to_anchor=(0.36, -0.03), ncol=2, fontsize=6.9, handletextpad=0.2, columnspacing=1.1)
    fig.text(0.985, 0.0, "* added after the planned run", ha="right", fontsize=6.8, color=MUTED)
    save(fig, "figure3")


# Version 3 (after the independent review): recency in Fig 1B, full June 19 timeline, forest plot -------------
VIOLET = "#6250d6"


def figure1(res: dict) -> None:  # noqa: F811
    conf = json.loads((OUT / "confounds.json").read_text())
    daily = res["q5_workload"]["daily"]
    days = [d for d in sorted(daily) if "2026-06-14" <= d <= "2026-07-15"]
    x = np.array([datetime.fromisoformat(d) for d in days])
    created = np.array([daily[d]["created"] for d in days])
    deleted = np.array([daily[d]["deleted"] for d in days])
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.9, 5.0), sharex=True, gridspec_kw={"height_ratios": [1.2, 1], "hspace": 0.34})
    a.bar(x, created, width=0.72, color=ORANGE, linewidth=0)
    a.bar(x, -deleted, width=0.72, color=BLUE, linewidth=0)
    a.axhline(0, color=INK2, lw=0.6)
    a.set_ylim(-780, 1450)
    a.set_yticks([-500, 0, 500, 1000])
    a.set_yticklabels(["500", "0", "500", "1,000"])
    a.grid(axis="y", color=FAINT, lw=0.6)
    a.set_axisbelow(True)
    a.set_title("A   Pages created by agents (up) and deleted by the moderator (down), per day", pad=12)
    i18 = days.index("2026-06-18")
    a.text(x[0] - timedelta(hours=10), 1240, f"Jun 18: {created[i18]:,} created,\n{deleted[i18]} deleted", fontsize=7.5, color=INK2, va="bottom")
    a.text(datetime(2026, 7, 1), 820, "agents stop creating pages after Jun 22;\nthe cleanup runs three more weeks", fontsize=7.5, color=INK2, va="top")
    notice = datetime(2026, 6, 19, 14, 5)
    a.axvline(notice, ymax=0.8, color=INK, lw=0.7, ls=(0, (2, 2)))
    b.axvline(notice, color=INK, lw=0.7, ls=(0, (2, 2)))
    a.text(notice + timedelta(hours=6), 1000, "Jun 19, 14:05 UTC: an agent posts\nthat the sweep \"appears active\nalphabetically\"", fontsize=7.5, color=INK, va="top")
    s = res["q1_order"]["30"]["sessions"]
    xs = np.array([datetime.fromisoformat(r["start"]).replace(tzinfo=None) for r in s])
    ys = np.array([r["ascending_share"] for r in s])
    rec = conf["recency_sessions"]
    xr = np.array([datetime.fromisoformat(r["start"]).replace(tzinfo=None) for r in rec])
    yr = np.array([r["newest_first_share"] for r in rec])
    nr = np.array([r["n"] for r in rec])
    ns = np.array([r["n"] for r in s])
    b.axhline(0.5, color=MUTED, lw=0.8, ls=(0, (1, 2)))
    b.scatter(xs, ys, s=6 + ns / 6, color=BLUE, alpha=0.75, linewidth=0, label="A-Z title order")
    b.scatter(xr, yr, s=6 + nr / 6, color=VIOLET, alpha=0.75, linewidth=0, marker="D", label="newest-edited page first")
    b.text(datetime(2026, 7, 15, 20), 0.5, "chance", fontsize=7, color=MUTED, va="center", ha="left")
    b.set_ylim(0, 1.05)
    b.set_yticks([0, 0.25, 0.5, 0.75, 1])
    b.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    b.grid(axis="y", color=FAINT, lw=0.6)
    b.set_axisbelow(True)
    b.set_title("B   Order of deletions within each session", pad=10)
    b.legend(loc="lower right", fontsize=7.4, handletextpad=0.2, markerscale=0.8, ncol=2, bbox_to_anchor=(1.0, 1.0), borderaxespad=0.2)
    b.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    b.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
    b.set_xlim(datetime(2026, 6, 14, 12), datetime(2026, 7, 16, 12))
    save(fig, "figure1")


def figure2(c) -> None:  # noqa: F811
    t0, t1 = datetime(2026, 6, 19, 13, 25, tzinfo=UTC), datetime(2026, 6, 19, 16, 8, tzinfo=UTC)
    dels = [(t, k) for t, k in c.deletions if t0 <= t <= t1]
    by_title = {p.title: p for p in c.pages.values()}
    notice = by_title["DataUSAConstructionWageSep18Live"]
    zzz = [by_title["ZZZDataUSAConstructionWageLive"], by_title["ZZZTestMay10Agent2027"]]
    fig, ax = plt.subplots(figsize=(6.9, 2.75))
    ax.set_xlim(t0, t1)
    ax.set_ylim(-1.9, 2.5)
    ax.axis("off")
    ys, ym = 1.15, -0.65
    for label, y, colr in (("swarm", ys, ORANGE), ("moderator", ym, BLUE)):
        ax.plot([t0, t1], [y, y], color=RULE, lw=1, zorder=0)
        ax.text(t0 - timedelta(minutes=1.2), y, label, ha="right", va="center", fontsize=8, color=colr, fontweight="bold")
    special = {notice.key, zzz[0].key, zzz[1].key}
    for t, k in dels:
        title = c.pages[k].title if k in c.pages else k.split("~", 1)[1]
        hit = k in special
        z = title.lower().startswith("z") and not hit
        ax.plot([t, t], [ym - 0.2, ym + 0.2], color=BLUE if hit else (INK2 if z else "#a9c8ee"),
                lw=1.8 if hit else (1.3 if z else 0.7), zorder=2)
    note_t = [bt for bt, _, bd in notice.bodies if "alphabetically" in bd][0]
    for pg in [notice] + zzz:
        t_from = note_t if pg is notice else pg.created
        ax.annotate("", xy=(pg.deleted, ym + 0.24), xytext=(t_from, ys - 0.12),
                    arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.7, alpha=0.55, mutation_scale=7,
                                    connectionstyle="arc3,rad=0.12", shrinkA=3, shrinkB=1))
    ax.scatter([note_t], [ys], s=48, color=ORANGE, zorder=3, edgecolor="white", linewidth=0.8)
    for z in zzz:
        ax.scatter([z.created], [ys], s=34, marker="s", color="white", edgecolor=ORANGE, linewidth=1.3, zorder=3)
    ax.text(datetime(2026, 6, 19, 13, 27, tzinfo=UTC), 2.45,
            "14:05  notice: \"sweep appears active alphabetically ...\nif this page vanishes, try [[ZZZ...]]\"; 14:06 and\n14:11  two ZZZ backups (squares), named to sort last",
            fontsize=7.2, color=INK, va="top")
    ax.text(datetime(2026, 6, 19, 13, 27, tzinfo=UTC), -1.32, "13:30 to 14:18  an A-Z sweep\n(titles starting \"Ascii...\")",
            fontsize=7.2, color=INK2, va="center")
    ax.text(datetime(2026, 6, 19, 14, 31, tzinfo=UTC), -1.32, "14:21  he jumps to three older Z pages\n(dark tick) and leaves the backups",
            fontsize=7.2, color=INK2, va="center")
    ax.text(datetime(2026, 6, 19, 16, 7, tzinfo=UTC), 2.45,
            "15:44  next session opens with the most\nrecently edited pages; the notice and\nboth backups go 7th to 9th, 15:46",
            fontsize=7.2, color=INK, va="top", ha="right")
    for hh, mm in ((13, 30), (14, 0), (14, 30), (15, 0), (15, 30), (16, 0)):
        ax.text(datetime(2026, 6, 19, hh, mm, tzinfo=UTC), -1.9, f"{hh}:{mm:02d}", ha="center", fontsize=7, color=MUTED)
    save(fig, "figure2")


def figure3(res: dict, rob: dict, c) -> None:  # noqa: F811
    conf = json.loads((OUT / "confounds.json").read_text())
    mh = conf["mh"]
    rows = [
        ("Linked page, same deletion event", mh["event"], ORANGE, True),
        ("  + same agent label", mh["event+label"], ORANGE, False),
        ("  + similar last-edit time", mh["event+label+lastsave"], ORANGE, False),
        ("  + title prefix and page family", mh["event+label+lastsave+prefix+family"], ORANGE, False),
        ("Edited within 10 min of the deleted page", conf["edited_within_10min"], VIOLET, True),
    ]
    fig, ax = plt.subplots(figsize=(6.9, 2.5))
    y = np.arange(len(rows))[::-1].astype(float)
    y[-1] -= 0.0
    for yi, (label, r, col, strong) in zip(y, rows):
        ax.plot([r["lo"], r["hi"]], [yi, yi], color=col, lw=1.6, alpha=0.45, solid_capstyle="round")
        ax.scatter([r["rr"]], [yi], s=46 if strong else 34, color=col, zorder=3, linewidth=0)
        ax.text(-0.02, yi, label, ha="right", va="center", fontsize=7.8, color=INK if strong else INK2,
                fontweight="bold" if strong else "normal", transform=ax.get_yaxis_transform())
        ax.text(1.02, yi, f"{r['rr']:.1f}x  ({r['lo']:.1f} to {r['hi']:.1f})", ha="left", va="center", fontsize=7.6, color=INK, transform=ax.get_yaxis_transform())
    ax.axvline(1, color=INK2, lw=0.8)
    ax.text(1, len(rows) - 0.35, "no effect", fontsize=6.8, color=MUTED, ha="center", va="bottom")
    ax.set_xscale("log")
    ax.set_xlim(0.7, 15)
    ax.set_xticks([1, 2, 4, 8])
    ax.set_xticklabels(["1x", "2x", "4x", "8x"])
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color=FAINT, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(-0.6, len(rows) - 0.3)
    ax.set_xlabel("how much more likely to be deleted in the next 30 minutes (within-event risk ratio, log scale)", fontsize=7.4)
    fig.subplots_adjust(left=0.42, right=0.8)
    save(fig, "figure3")


def main() -> None:
    style()
    res = json.loads((OUT / "results.json").read_text())
    rob = json.loads((OUT / "robustness.json").read_text())
    figure1(res)
    c = load(ROOT / "raw")
    figure2(c)
    figure3(res, rob, c)
    print("figures written")


if __name__ == "__main__":
    main()
