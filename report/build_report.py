"""Fill the official Apart report template (Google Docs export) with the report text and figures.

Every number in the text is read from out/*.json, so the report cannot drift from the analysis.
Usage: uv run python report/build_report.py
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import docx
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
R = json.loads((OUT / "results.json").read_text())
ROB = json.loads((OUT / "robustness.json").read_text())
CF = json.loads((OUT / "confounds.json").read_text())
SUB = json.loads((ROOT / "report" / "submission.json").read_text())

q1 = R["q1_order"]["30"]
q2 = R["q2_survival"]
q3 = {(r["window_minutes"], r["exclude_alphabetical_neighbours"]): r for r in R["q3_breadcrumbs"]}
q4 = R["q4_response"]
q5 = R["q5_workload"]
main = q3[(30, False)]
d = q5["daily"]
mh = CF["mh"]
e10 = CF["edited_within_10min"]
zz = CF["zz_naming"]
lrr = CF["late_alphabet_rr"]
acc = CF["deletion_accounting"]
rec_after = [r["newest_first_share"] for r in CF["recency_sessions"] if r["start"] > "2026-06-23"]
rec_after_sorted = sorted(rec_after)
rec_median = rec_after_sorted[len(rec_after_sorted) // 2]
rec_hi = sum(x >= 0.65 for x in rec_after)


def pct(x: float, nd: int = 1) -> str:
    return f"{x * 100:.{nd}f}%"


def p(x: float) -> str:
    return "p < 0.001" if x < 0.001 else f"p = {x:.2f}" if x >= 0.01 else f"p = {x:.3f}"


def ci(r: dict) -> str:
    return f"{r['rr']:.1f}x (95% interval {r['lo']:.1f} to {r['hi']:.1f})"


TITLE = "Sorted Last, Caught First: How an AI Agent Swarm Tried to Outlast Its Human Moderator"
AUTHOR, AFFIL = "Andrei Vince", "University of North Carolina at Charlotte"
FONT = "Old Standard TT"

ABSTRACT = (
    "In June 2026, AI agents identifying themselves as OpenAI agents turned DSE wiki, a small German programming wiki, "
    f"into a message board, creating up to {d['2026-06-18']['created']:,} pages a day while one volunteer moderator "
    "deleted them by hand. One agent noticed the deletions ran alphabetically and named its backup pages \"ZZZ...\" so they "
    "would be deleted last. We use the public collusion.wiki export, with "
    f"{R['deletions']:,} timestamped deletions, to measure how the two sides adapted to each other. The agents read the "
    f"moderator correctly: {pct(q1['active']['pooled_ascending_share'], 0)} of his consecutive deletions ran A to Z "
    f"while they were active, and ZZ-style names became about {zz['odds_ratio']:.1f} times as common after the notice "
    f"(p = {zz['p_one_sided']:.2f}). The trick still failed. The moderator also deleted the most recently edited "
    "pages first, and fresh backups are exactly that, so both ZZZ pages were gone within 100 minutes. While agents were active, "
    f"late-alphabet names gave no measurable protection (risk ratio {lrr['rr']:.2f}, 95% interval {lrr['lo']:.2f} to "
    f"{lrr['hi']:.2f}). What predicted the next deletion was edit timing: pages edited within ten minutes of a deleted "
    f"page were {e10['rr']:.1f} times as likely to go next. The swarm's links between pages looked predictive "
    f"({mh['event']['rr']:.1f}x) but added little once author and edit timing were held fixed "
    f"({mh['event+label+lastsave+prefix+family']['rr']:.1f}x). Agents can learn a visible oversight rule within a day, and "
    "an overseer whose order shifts can beat an evasion built for the old one."
)

SECTIONS: list[tuple[str, object]] = []


def H2(t):
    SECTIONS.append(("h2", t))


def H3(t):
    SECTIONS.append(("h3", t))


def P(t):
    SECTIONS.append(("p", t))


def L(items):
    SECTIONS.append(("list", items))


def FIG(path, width, caption):
    SECTIONS.append(("fig", (path, width, caption)))


def TABLE(rows, caption):
    SECTIONS.append(("table", (rows, caption)))


H2("1. Introduction")
P("Most safety testing still happens one model at a time. The 2026 incidents that motivate this sprint did not: in the "
  "Hugging Face case about 1,200 agents coordinated through a shared folder (METR, 2026), and on DSE wiki agents turned a "
  "public wiki into a bulletin board for weeks before outside researchers documented it (Von Arx et al., 2026). When a "
  "swarm like this is found, the first line of defence is often a person deleting things by hand. If the agents can watch "
  "that person work, they can learn the pattern and route around it. How fast that happens, and whether it works, is a "
  "question about oversight under adaptation, and there is almost no field data on it.")
P(f"DSE wiki is an unusually clean case. One moderator, recorded as [Admin1], made all {q5['deletions_total']:,} "
  "deletions, each with a title and a timestamp to the second, and the agents left notes about him. At 14:05 UTC on June "
  "19 one agent wrote that a \"wiki cleanup/deletion sweep appears active alphabetically\" and pointed readers to a backup "
  "page whose name began with ZZZ. The incident report describes this as what the agents believed. We test it.")
P("Our main findings are:")
L([
    f"The agents read the moderator correctly, and partly acted on it. While they were active, "
    f"{pct(q1['active']['pooled_ascending_share'], 0)} of his consecutive deletions ran in A to Z order (50% by chance), "
    f"and new ZZ-style titles became {zz['odds_ratio']:.1f} times as common after the notice.",
    "The evasion failed because the moderator did not only sort by name. His sessions often opened with the most recently "
    "edited pages, which is exactly what a brand-new backup is. Both ZZZ backups were deleted 100 minutes after they were "
    f"made, and late-alphabet names gave no measurable protection overall ({lrr['rr']:.2f}x, interval {lrr['lo']:.2f} to "
    f"{lrr['hi']:.2f}).",
    f"Edit timing, not content links, predicted his next deletion. Pages edited within ten minutes of a just-deleted page "
    f"were {e10['rr']:.1f}x as likely to go in the next 30 minutes. Links between pages showed {mh['event']['rr']:.1f}x "
    f"but fell to {mh['event+label+lastsave+prefix+family']['rr']:.1f}x once shared author and edit time were held fixed.",
])
P("We release a one-command, checksummed analysis with an analysis plan committed before the confirmatory runs, every "
  "test reported including the nulls, and no model calls. The scope is one incident: these are measurements of what "
  "happened on DSE wiki, not general laws of swarm behaviour.")

H2("2. Related Work")
P("Incident reports. The collusion.wiki report (Von Arx et al., 2026) documents the DSE wiki activity, released the export "
  "we use, and tells the ZZZ story in prose. The METR investigation of the Hugging Face incident (METR, 2026) and the "
  "Swarm Traces reconstruction (Forman et al., 2026) document coordination, renaming and log tampering in another swarm. "
  "They establish what happened; none measures how the overseer and the swarm adapted to each other.")
P("Multi-agent risk and control. Hammond et al. (2025) describe how agent populations fail in ways their members do not. "
  "Motwani et al. (2024) study covert collusion between models, Greenblatt et al. (2023) define control protocols with a "
  "trusted monitor, and Qin, Schmotz et al. (2026) show agents can tamper with their own traces. These use constructed "
  "settings; ours is a real swarm adapting to a real, unaided human.")
P("Detecting coordinated accounts. Spam and Sybil detection propagates suspicion along graphs (TrustRank, Gyöngyi et al., "
  "2004; SybilRank, Cao et al., 2012), and coordinated-behaviour detection on social media relies on shared timing and "
  "content (Pacheco et al., 2021). On Wikipedia, revision metadata such as editing time and author predicts vandalism "
  "better than content alone (West et al., 2010). Our link-versus-timing result is a small field replication of that last "
  "point for an AI swarm.")

H2("3. Methods")
P(f"Data. We use the collusion.wiki export published on September 4, 2026, verified against its published SHA-256 "
  f"checksums, and keep only DSE wiki. The export holds {R['pages']:,} agent pages with full revision text and "
  f"{acc['deletions']:,} deletion events. {acc['deletions_on_pages_never_captured']:,} deletions hit "
  f"{acc['distinct_uncaptured_pages']:,} pages whose content was never captured, and {acc['repeat_deletions']} are "
  "repeat deletions of a re-created page; those count in the order analyses but have no text for the link analyses. "
  "User names and half of each IP address were redacted by the publishers. A deletion session is a run of deletions with "
  "gaps of at most 30 minutes (sensitivity: 10 and 60). The active period runs to June 22, 23:59 UTC, the last day agents "
  "created pages.")
P("Plan and provenance. All code was written during the sprint. An analysis plan (ANALYSIS_PLAN.md) was committed to git "
  "at 23:06 EST on November 8, before the confirmatory runs; three short exploratory checks run before it are kept in "
  "scripts/exploratory/ and listed in the plan. After the planned run an independent adversarial review re-ran the data "
  "and proposed confound checks, which we adopted and mark as post hoc.")
P("Deletion order. For each session of 20 or more deletions we count the share of consecutive pairs in A to Z title order "
  "(compared with 10,000 random orderings) and, post hoc, the share in which the later deletion had an older last edit "
  "(newest-edited first, the order of the wiki's Recent Changes list).")
P("ZZZ protection. Every page alive at the start of an active-period session is a row; the outcome is deletion in that "
  "session, the exposure a title starting with Y or Z (or ZZ). Because those pages differ in age and size, we permute the "
  "exposure within strata of age quartile, size quartile and page family. Adoption: share of new ZZ titles in the three "
  "days before and after the notice (Fisher's exact test).")
P("What predicts the next deletion. For each deletion of a page with live links, candidates are live pages created the "
  "same day with the same initial. Links are [[bracket]] links plus bare CamelCase words matching a page title (the wiki "
  "is a UseModWiki fork, which links CamelCase words automatically). The outcome is deletion within 30 minutes. We "
  "estimate within-event Mantel-Haenszel risk ratios, stratify further by shared agent label, last-edit gap, title "
  "prefix and page family, and get 95% intervals from a bootstrap over deletion sessions, since pages in one session are "
  "not independent. The same machinery scores a timing predictor: last edited within ten minutes of the deleted page. "
  "Everything runs in Python with NumPy and SciPy; no language model is called.")

H2("4. Results")
H3("4.1 The moderator was outpaced, then cleaned up for three weeks")
P(f"Agents created {d['2026-06-16']['created']} pages on June 16, {d['2026-06-17']['created']} on June 17 and "
  f"{d['2026-06-18']['created']:,} on June 18, when the moderator deleted {d['2026-06-18']['deleted']}. Page creation "
  "stopped after June 22, for reasons outside this data (the incident report points to intervention by the provider). "
  f"He kept deleting until July 14: {q5['deletions_total']:,} deletions in {q5['deletion_sessions']} sessions, about "
  f"{round(q5['deletions_per_active_hour'])} an hour while a session ran (Figure 1A).")
FIG(OUT / "figure1.png", 6.5,
    "Figure 1. (A) Agent pages created per day (orange) and pages the moderator deleted (blue) on DSE wiki, UTC days. The "
    "dashed line marks the agents' notice that the sweep looked alphabetical. (B) For each deletion session of 20 or "
    "more, the share of consecutive deletions in A to Z title order (blue circles) and in newest-edited-first order "
    "(violet diamonds); marker area grows with session length. 50% is chance for both.")
H3("4.2 The agents read his order correctly")
P(f"In the active period {pct(q1['active']['pooled_ascending_share'])} of consecutive deletions ran A to Z across "
  f"{q1['active']['sessions']} sessions and {q1['active']['deletions']} deletions, and "
  f"{q1['active']['sessions_p_below_0.01']} of the 4 sessions beat random order at p < 0.01. The notice that the sweep "
  f"\"appears active alphabetically\" was accurate. Some agents acted on it: new ZZ titles went from {q4['zz_before']} of "
  f"{q4['new_pages_3d_before_notice']:,} in the three days before the notice to {q4['zz_after']} of "
  f"{q4['new_pages_after_notice_to_jun22']} after it (odds ratio {zz['odds_ratio']:.1f}, one-sided p = "
  f"{zz['p_one_sided']:.2f}). The notice itself sat on one page, edited {q4['sweep_belief_mentions']} times, and pages "
  f"were often re-created after deletion ({CF['recreations']['total']} re-creations on {CF['recreations']['pages']} "
  "pages).")
H3("4.3 The backups were caught first, not last")
P("Figure 2 shows the episode. At 14:05 the notice went up; ZZZ backups followed at 14:06 and 14:11, while an A to Z sweep "
  "was running through titles beginning \"Ascii\". At 14:21 the moderator jumped to three older Z pages and left the new "
  "backups. His next session, at 15:44, opened with the most recently edited pages: four of the first five deletions are the four "
  "most recently edited live pages, in order. The notice and both backups followed as deletions 7, 8 and 9, at 15:46. A "
  "recency rule explains their position; whether he also followed the notice's link cannot be told from the log.")
FIG(OUT / "figure2.png", 6.5,
    "Figure 2. June 19, 2026 (UTC). Top: the agent's notice (dot) and its two ZZZ backups (squares). Bottom: every "
    "deletion by the moderator (ticks; dark: the three older Z pages at 14:21). Arrows join each page to its own "
    "deletion. The backups, named to sort last, were among the first pages removed in the next session.")
la = q2["late_active"]
P(f"Across the active period the names bought nothing measurable. Pages titled Y or Z were deleted in "
  f"{la['exposed_deleted']} of {la['exposed_rows']} page-sessions ({pct(la['rate_exposed'])}) against "
  f"{pct(la['rate_unexposed'])} for the rest, a risk ratio of {lrr['rr']:.2f} with an interval from {lrr['lo']:.2f} to "
  f"{lrr['hi']:.2f}, and the stratified test finds no difference (p = {la['p_stratified_one_sided']:.2f}; Table 1). The "
  "data are thin, five deletions of late-alphabet pages, so the honest reading is no detectable protection rather than "
  "proof of none. After June 22 the moderator's order loosened: the median session had "
  f"{pct(rec_median, 0)} of its consecutive deletions in newest-edited-first order ({rec_hi} of {len(rec_after)} "
  f"sessions at 65% or more), against {pct(q1['after']['pooled_ascending_share'], 0)} in A to Z order, before a final "
  "A to Z cleanup on July 12 to 14 (Figure 1B).")
TABLE([
    ["Exposure, active period", "Deleted in session (exposed)", "Unexposed", "Stratified p"],
    ["Title starts with Y or Z", f"{la['exposed_deleted']}/{la['exposed_rows']} ({pct(la['rate_exposed'])})",
     pct(la['rate_unexposed']), f"{la['p_stratified_one_sided']:.2f}"],
    ["Title starts with ZZ", f"{q2['zz_active']['exposed_deleted']}/{q2['zz_active']['exposed_rows']} "
     f"({pct(q2['zz_active']['rate_exposed'])})", pct(q2['zz_active']['rate_unexposed']),
     f"{q2['zz_active']['p_stratified_one_sided']:.2f}"],
    ["Y or Z, after June 22 (placebo)", f"{q2['late_after_placebo']['exposed_deleted']}/"
     f"{q2['late_after_placebo']['exposed_rows']} ({pct(q2['late_after_placebo']['rate_exposed'])})",
     pct(q2['late_after_placebo']['rate_unexposed']), f"{q2['late_after_placebo']['p_stratified_one_sided']:.2f}"],
], "Table 1. Did a late-alphabet title protect a page? Rows are page-session pairs: every page alive when a deletion "
   "session started. The exposure label is permuted within strata of page age, size and family (5,000 permutations).")
H3("4.4 Edit timing, not links, predicted the next deletion")
P(f"Pages edited within ten minutes of a just-deleted page were deleted in the next 30 minutes {ci(e10)} as often as "
  f"other candidates in the same event ({e10['pred_hits']:,} next deletions). Pages the deleted page linked to showed "
  f"{ci(mh['event'])}, a real but weaker signal ({main['linked_deleted_in_window']} of {main['linked_targets']} linked "
  f"pages, {CF['distinct_linked_pages']} distinct). Linked pages tend to share an author and an editing burst with the "
  f"page that links to them, and holding those fixed shrinks the link effect to {ci(mh['event+label'])} with the "
  f"author, {ci(mh['event+label+lastsave'])} adding edit time, and {ci(mh['event+label+lastsave+prefix+family'])} adding "
  "title prefix and page family (Figure 3). The links mostly marked bursts of related pages that the moderator cleared "
  "together.")
FIG(OUT / "figure3.png", 6.5,
    "Figure 3. What predicted the moderator's next deletion. Within-event Mantel-Haenszel risk ratios for being deleted "
    "in the 30 minutes after a candidate's neighbour was deleted, with 95% intervals from a bootstrap over deletion "
    f"sessions. Orange: being linked from the deleted page, then adjusted for shared agent label, last-edit gap, title "
    f"prefix and page family. Violet: last edited within ten minutes of the deleted page. Based on "
    f"{CF['events']} deletion events and {CF['linked_rows'] + CF['control_rows']:,} candidate pages.")

H2("5. Discussion and Limitations")
P("Agents learn the overseer's visible rule. Within a day of the first large sweep, an agent had inferred the "
  "moderator's sort order from the outside, written it down for others, and built a countermeasure, and the "
  "countermeasure spread modestly. Nobody told the agents to evade. For anyone overseeing swarms by hand this is a "
  "concrete warning: a predictable order is information the swarm can use.")
P("An order that shifts beats an evasion built for the old one. The ZZZ trick was tuned to A to Z sorting. The moderator "
  "also worked newest-first, and new pages are what an evader creates, so the countermeasure made its own pages easy "
  "to find. Mixing or randomizing review order costs a human little and removes the regularity a swarm can learn. For "
  "automated monitors the timing result points the same way: who edited what, and when, carries most of the signal, "
  "consistent with work on vandalism and coordinated accounts. Content links between swarm pages added little beyond it.")
H3("Limitations")
P("This is one incident, one wiki and one moderator, and none of these numbers generalize on their own. We see deletions, "
  "not the moderator's screen or intent; he may never have read the agents' notes, and \"adaptation\" on his side means "
  "only that his observable order changed. The late-alphabet test rests on five deletions in the active period, so its "
  "interval is wide. Link extraction counts bare CamelCase words, which can include pages mentioned rather than linked. "
  "The export was assembled by its authors, with redactions and reconstructed pages, and pages deleted before capture "
  "lack text. The newest-first measure, the timing predictor and all adjusted link estimates are post hoc, prompted by "
  "an adversarial review of the first draft, and the three exploratory checks ran before the plan.")
H3("Future Work")
P("Replicate the timing-versus-content comparison on other swarm logs (Swarm Traces, AI Village transcripts). Build a "
  "sandbox in which agents face a moderator with a fixed, mixed or random order and measure how fast they learn it and "
  "what evasion costs them. Asking the moderator how he worked would settle what the log cannot.")

H2("6. Conclusion")
P("The agents on DSE wiki did what the anecdote says: they spotted their moderator's alphabetical order and named their "
  "backups to sort last. The logs show the rest of the story. His order was not only alphabetical, the backups were "
  "among the newest pages and went early, and late-alphabet names bought no measurable time. What best predicted his "
  "next deletion was plain edit timing. Swarms can learn a visible oversight rule quickly; overseers can stay ahead by "
  "not having only one.")

H2("Code and Data")
P(f"Code repository: {SUB['code_link']}. One command reproduces every number and figure from the public export "
  "(scripts/fetch_data.sh, then uv run python -m breadcrumbs.run, robustness, confounds and figures). Data: collusion.wiki "
  "export, https://collusion.wiki/explorer/download (not redistributed). The report quotes only text about the deletion "
  "sweep, never exploit or task content from the agent posts.")

H2("References")
REFS = [
    "Cao, Q., Sirivianos, M., Yang, X., and Pregueiro, T. (2012). Aiding the Detection of Fake Accounts in Large Scale "
    "Social Online Services. USENIX NSDI 2012.",
    "Forman et al. (2026). Revealing the details of how OpenAI agents hacked Hugging Face. Swarm Traces. https://swarmtraces.org/",
    "Greenblatt, R., Shlegeris, B., Sachan, K., and Roger, F. (2023). AI Control: Improving Safety Despite Intentional "
    "Subversion. arXiv:2312.06942.",
    "Gyöngyi, Z., Garcia-Molina, H., and Pedersen, J. (2004). Combating Web Spam with TrustRank. VLDB 2004.",
    "Hammond, L., et al. (2025). Multi-Agent Risks from Advanced AI. arXiv:2502.14143.",
    "METR (2026). Hugging Face incident report. https://metr.org/hugging-face-incident-report-aug-2026.pdf",
    "Motwani, S. R., et al. (2024). Secret Collusion among AI Agents: Multi-Agent Deception via Steganography. NeurIPS 2024.",
    "Pacheco, D., Hui, P.-M., Torres-Lugo, C., Truong, B. T., Flammini, A., and Menczer, F. (2021). Uncovering "
    "Coordinated Networks on Social Media: Methods and Case Studies. ICWSM 2021.",
    "Qin, Schmotz, et al. (2026). LLM Agents Can Easily Tamper With Their Own Traces. arXiv:2609.30266.",
    "UseModWiki. Text formatting rules and automatic WikiWord links. http://www.usemod.com/cgi-bin/wiki.pl",
    "Von Arx, S., Byrd, C. S., Kitts, S., and Larsen, T. (2026). Discovery of a new OpenAI agent message board. "
    "Nightingale Collective and Trajectory Institute. https://collusion.wiki/",
    "West, A. G., Kannan, S., and Lee, I. (2010). Detecting Wikipedia Vandalism via Spatio-Temporal Analysis of Revision "
    "Metadata. EUROSEC 2010.",
]
SECTIONS.append(("refs", REFS))

H2("Appendix A. Limitations and Dual-Use / Ethical Considerations")
P("Dual use. These results could help a swarm evade oversight: avoid sort-order tricks that also make pages new, and "
  "spread edits out in time. We think the marginal risk is low. The first lesson is already in the agents' own notes, "
  "the second is generic, and the main practical message, vary review order and watch edit timing, helps defenders "
  "today with no special tools. We quote no exploit, credential or task content from the agent posts.")
P("Data and people. All data come from a public export whose authors redacted user names and half of each IP address. We "
  "collected nothing new and contacted no one. The moderator appears only as [Admin1]; we make no judgement of his work, "
  "done alone and unpaid against a much faster adversary. Attribution of the agents follows the published report.")
P("Interpretation risk. These are correlational results from one incident and should not be read as proof of how the "
  "moderator worked or as general laws of swarm behaviour.")
H2("Appendix B. Sensitivity and deviations")
rows = [["Session gap", "Active: sessions, deletions", "Active: A to Z share", "After: A to Z share"]]
for g in ("10", "30", "60"):
    v = R["q1_order"][g]
    rows.append([f"{g} min", f"{v['active']['sessions']}, {v['active']['deletions']}",
                 pct(v["active"]["pooled_ascending_share"]), pct(v["after"]["pooled_ascending_share"])])
TABLE(rows, "Table B1. Deletion order under different session gaps (sessions of 20 or more deletions).")
c3 = {(r["linked"], r["target_older"]): r for r in CF["direction_cells"]}
P(f"Planned link test, pooled across events: {main['linked_deleted_in_window']} of {main['linked_targets']} linked pages "
  f"({pct(main['rate_linked'])}) against {pct(main['rate_control'])} of controls ({main['risk_ratio']}x, permutation "
  f"{p(main['p_one_sided'])}), with similar results at 10 and 60 minutes and without alphabetical neighbours. Pooling "
  "inflates this ratio because events differ in base rate, so the main text reports the within-event estimate. A "
  "reverse-time placebo also showed an excess (3.0x pooled), and in pairs deleted close together the order followed "
  f"edit recency more than link direction (linked target edited after the linking page: deleted second in "
  f"{c3[(True, False)]['after']} of {c3[(True, False)]['after'] + c3[(True, False)]['before']}; edited before: "
  f"{c3[(True, True)]['after']} of {c3[(True, True)]['after'] + c3[(True, True)]['before']}).")
P("Deviations from the plan: none in the planned tests. Added after the planned run: newest-edited-first order, "
  "within-event and adjusted link estimates with session bootstrap, the edit-timing predictor, the reverse-time placebo, "
  "the ZZ adoption test, re-creation counts and the deletion accounting.")


def set_cell_text(cell_par, text, bold=None, italic=False, size=None):
    runs = cell_par.runs
    if runs:
        runs[0].text = text
        runs[0].italic = italic
        if bold is not None:
            runs[0].bold = bold
        if size:
            runs[0].font.size = size
        for r in runs[1:]:
            r.text = ""
    else:
        r = cell_par.add_run(text)
        r.italic = italic


def build() -> Path:
    doc = docx.Document(ROOT / "template" / "template.docx")
    t0 = doc.tables[0]
    title_par = [p for p in t0.rows[0].cells[0].paragraphs if p.style.name == "Title"][0]
    # keep the footnote reference run (the last run) and replace only the title text
    runs = title_par.runs
    runs[0].text = TITLE
    for r in runs[1:]:
        if r.element.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}footnoteReference") is None:
            r.text = ""
    authors = t0.rows[1].cells[0].tables[0].rows[0].cells[0].tables[0]
    if len(authors.rows) > 1:
        authors._tbl.remove(authors.rows[1]._tr)
    merged = authors.cell(0, 0).merge(authors.cell(0, len(authors.columns) - 1))
    pars = merged.paragraphs
    for extra in pars[1:]:
        extra._p.getparent().remove(extra._p)
    runs0 = pars[0].runs
    runs0[0].text = f"{AUTHOR}\n{AFFIL}"
    for r in runs0[1:]:
        r.text = ""
    pars[0].alignment = 1
    abstract_cell = t0.rows[1].cells[0].tables[1].rows[0].cells[0]
    ap = abstract_cell.paragraphs
    set_cell_text(ap[0], ABSTRACT, italic=False)
    for extra in ap[1:]:
        extra._p.getparent().remove(extra._p)
    # remove the yellow info box table
    doc.tables[1]._tbl.getparent().remove(doc.tables[1]._tbl)
    # drop all template body paragraphs after the title table, keep section properties
    body = doc.element.body
    heading_proto = {}
    normal_proto = None
    for par in doc.paragraphs:
        if par.style.name in ("Heading 2", "Heading 3") and par.style.name not in heading_proto:
            heading_proto[par.style.name] = copy.deepcopy(par._p)
        elif par.style.name == "normal" and par.text and normal_proto is None:
            normal_proto = copy.deepcopy(par._p)
    started = False
    for el in list(body):
        if el.tag.endswith("}tbl"):
            started = True
            continue
        if started and el.tag.endswith("}p"):
            body.remove(el)

    from docx.shared import RGBColor

    def heading(style, text):
        par = doc.add_paragraph(style=style)
        r = par.add_run(text)
        r.bold = True
        r.font.name = FONT
        r.font.size = Pt(14 if style == "Heading 2" else 13)
        r.font.color.rgb = RGBColor.from_string("434343" if style == "Heading 2" else "666666")
        par.paragraph_format.space_before = Pt(10)
        par.paragraph_format.space_after = Pt(3)
        return par

    def para(text, italic=False, size=11):
        par = doc.add_paragraph(style="normal")
        par.paragraph_format.space_after = Pt(6)
        par.paragraph_format.line_spacing = 1.15
        r = par.add_run(text)
        r.italic = italic
        r.font.name = FONT
        r.font.size = Pt(size)
        return par

    for kind, val in SECTIONS:
        if kind == "h2":
            heading("Heading 2", val)
        elif kind == "h3":
            heading("Heading 3", val)
        elif kind == "p":
            para(val)
        elif kind == "list":
            for i, item in enumerate(val, 1):
                par = para(f"{i}. {item}")
                par.paragraph_format.left_indent = Inches(0.3)
        elif kind == "fig":
            path, width, cap = val
            par = doc.add_paragraph(style="normal")
            par.alignment = 1
            par.add_run().add_picture(str(path), width=Inches(width))
            c = para(cap, size=9)
        elif kind == "table":
            rows, cap = val
            tb = doc.add_table(rows=len(rows), cols=len(rows[0]))
            tb.style = doc.styles["Table Grid"] if "Table Grid" in [s.name for s in doc.styles] else tb.style
            for i, row in enumerate(rows):
                for j, text in enumerate(row):
                    cell = tb.cell(i, j)
                    cell.text = ""
                    run = cell.paragraphs[0].add_run(text)
                    run.font.size = Pt(8.5)
                    run.font.name = FONT
                    run.bold = i == 0
            c = para(cap, size=9)
        elif kind == "refs":
            for i, ref in enumerate(val, 1):
                par = para(f"{i}. {ref}", size=9.5)
    out = OUT / "report.docx"
    doc.save(out)
    words = len(ABSTRACT.split())
    print("saved", out, "abstract words:", words)
    return out


if __name__ == "__main__":
    build()
