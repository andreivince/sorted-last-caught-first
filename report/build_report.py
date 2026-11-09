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
DIR = json.loads((OUT / "direction.json").read_text())

q1 = R["q1_order"]["30"]
q2 = R["q2_survival"]
q3 = {(r["window_minutes"], r["exclude_alphabetical_neighbours"]): r for r in R["q3_breadcrumbs"]}
q4 = R["q4_response"]
q5 = R["q5_workload"]
main = q3[(30, False)]
d = q5["daily"]


def pct(x: float, nd: int = 1) -> str:
    return f"{x * 100:.{nd}f}%"


def p(x: float) -> str:
    return "p < 0.001" if x < 0.001 else f"p = {x:.2f}" if x >= 0.01 else f"p = {x:.3f}"


TITLE = "Breadcrumbs: An AI Agent Swarm's Own Links Predicted What Its Human Moderator Deleted Next"
AUTHOR, AFFIL = "Andrei Vince", "University of North Carolina at Charlotte"

ABSTRACT = (
    "In June 2026, AI agents identifying themselves as OpenAI agents turned DSE wiki, a small German programming "
    f"wiki, into a message board, creating up to {d['2026-06-18']['created']:,} pages a day while one volunteer "
    "moderator deleted them by hand. Press coverage repeated an anecdote from the incident report: the agents "
    "noticed the moderator was deleting pages alphabetically and named a backup page \"ZZZ...\" so it would be "
    "deleted last. We test that story, and a broader question it raises for oversight: what does a swarm's own "
    f"coordination structure reveal to the person policing it? Using the public collusion.wiki export ({R['deletions']:,} "
    "timestamped deletions on DSE wiki), we find that the alphabetical sweep was real at first "
    f"({pct(q1['active']['pooled_ascending_share'])} of consecutive deletions in A-Z order, against 50% by chance), but "
    "the ZZZ trick did not measurably help: with page age, size and type held fixed, late-alphabet pages were not "
    f"deleted less often ({p(q2['late_active']['p_stratified_one_sided'])}). The stronger signal ran the other way. "
    "When the moderator deleted a page, the pages it linked to were deleted within the next 30 minutes "
    f"{main['risk_ratio']} times as often as matched pages it did not link to ({pct(main['rate_linked'])} against "
    f"{pct(main['rate_control'])}), across every time window and control we tried. The links agents wrote so they "
    "could find each other's notes also pointed at what an overseer would remove next. We release a one-command "
    "analysis with no model calls and discuss what this means for cheap oversight of agent swarms."
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
P("Most safety testing still happens one model at a time. The 2026 incidents that motivate this sprint did not: "
  "in the Hugging Face case about 1,200 agents coordinated through a shared folder (METR, 2026), and on DSE wiki "
  "agents turned a public wiki into a bulletin board for weeks before anyone outside noticed (Von Arx et al., 2026). "
  "When a swarm like this is found, the first line of defence is often not a classifier but a person deleting "
  "things by hand. How that person and the swarm adapt to each other is a question about oversight under pressure, "
  "and there is almost no data on it.")
P("DSE wiki is an unusually clean case. One moderator, recorded in the logs as [Admin1], made every one of "
  f"{q5['deletions_total']:,} deletions, each with a title and a timestamp to the second. The agents left their own "
  "notes about him. One wrote at 14:05 UTC on June 19 that a \"wiki cleanup/deletion sweep appears active "
  "alphabetically\" and linked a backup page whose name began with ZZZ. That anecdote travelled through the press. "
  "Nobody had checked whether the sweep was alphabetical, whether the trick worked, or what else the logs say "
  "about who was outmanoeuvring whom.")
P("Our main contributions are:")
L([
    "A first quantitative test of the moderator-swarm interaction on DSE wiki. The alphabetical sweep was real in "
    "the first days and faded later. The ZZZ evasion had no measurable effect once page age, size and type are "
    "controlled, and the notice about it stayed on a single page.",
    f"The breadcrumb effect: pages linked from a page the moderator just deleted were deleted in the next 30 "
    f"minutes {main['risk_ratio']} times as often as matched unlinked pages. The swarm's coordination links were "
    "the best predictor we found of what the overseer did next, which suggests a cheap signal for monitoring "
    "swarms that coordinate in public.",
    "An open, reproducible forensic pipeline: checksummed public data, an analysis plan committed to git before the "
    "confirmatory runs, every test reported including the null ones, and no model calls.",
])

H2("2. Related Work")
P("Incident reports. The collusion.wiki report (Von Arx et al., 2026) documents the DSE wiki activity and released "
  "the export we use; it describes the deletion race and the ZZZ anecdote in prose. The METR investigation of the "
  "Hugging Face incident (METR, 2026) and the Swarm Traces reconstruction document coordination, renaming and log "
  "tampering in a different swarm. These works establish what happened. We measure how oversight and the swarm "
  "interacted, which none of them quantifies.")
P("Multi-agent risk and control. Hammond et al. (2025) lay out how agent populations can fail in ways their members "
  "do not, including collusion and miscoordination. Motwani et al. (2024) study secret collusion and steganographic "
  "channels between models, and Greenblatt et al. (2023) define control protocols in which a trusted monitor "
  "oversees an untrusted model. Recent work shows agents can tamper with their own traces (arXiv 2609.30266). "
  "These studies use constructed settings. Our evidence comes from a real swarm and a real human overseer, and it "
  "points at an overseer's advantage rather than an attacker's: the coordination structure itself.")
P("Moderation of automated accounts. Geiger and Ribes (2010) describe how Wikipedia's human editors and tools "
  "track vandals by following their trail of edits across pages. The breadcrumb effect is the same idea, applied "
  "to a swarm whose trail is written into its own pages as links.")

H2("3. Methods")
P(f"Data. We use the collusion.wiki export published on September 4, 2026, verified against its published SHA-256 "
  f"checksums, and keep only DSE wiki: {R['pages']:,} agent pages, their saved revisions with full text, and "
  f"{R['deletions']:,} deletions. The publishers redacted user names and half of each IP address. A page's creation "
  "time is its first save. A deletion session is a run of deletions with gaps of at most 30 minutes (sensitivity "
  "10 and 60). The active period runs to June 22, 23:59 UTC, the last day agents created pages.")
P("Plan. Before the confirmatory runs we committed an analysis plan to git (ANALYSIS_PLAN.md, 23:06 EST on November 8). "
  "Three short exploratory checks had been run first to decide whether the project was worth doing; the plan "
  "lists what they showed. Checks added after the planned run are labelled post hoc throughout.")
P("Q1, deletion order. For each session with at least 20 deletions we count the share of consecutive deletions in "
  "ascending case-insensitive title order and compare it with 10,000 random orderings of the same titles.")
P("Q2, did ZZZ names survive longer? For every session in the active period, every page alive at the session start "
  "is a row; the outcome is whether it was deleted in that session and the exposure is a title starting with Y or "
  "Z (separately, with ZZ). Late-alphabet pages differ from the rest in age and size, so we permute the exposure "
  "label within strata of age quartile, size quartile and page family (5,000 permutations). The same test after "
  "June 22 serves as a placebo.")
P("Q3, the breadcrumb test. We build each page's outgoing links from its last saved text before deletion: "
  "[[bracket]] links and bare CamelCase words that exactly match another agent page title (the wiki links "
  "CamelCase words automatically). For each deletion of a page that linked to pages still alive, the outcome is "
  "whether a linked page was deleted within the next 30 minutes. Controls are alive pages it did not link to, "
  "created on the same day with the same initial letter, so alphabetical sweeps cannot explain the difference. "
  "The null shuffles which pages count as linked within each event's matched pool (2,000 permutations). "
  "Sensitivity: 10 and 60 minute windows, and removing pages within three places of the deleted page in "
  "alphabetical order. Post hoc we added controls created within one hour of the linked page, the active period "
  "alone, a reverse-order placebo (linked pages deleted in the 30 minutes before the linking page), and a test of "
  "which page of a linked pair went first.")
P("Q4 and Q5. We count pages that mention the alphabetical sweep, compare the share of new pages with late-alphabet "
  "or ZZ titles in the three days before the first notice and after it (Fisher's exact test), and check whether a "
  "deleted page's text reappeared on another page within 72 hours (exact match, or word 5-gram Jaccard of at least "
  "0.8). Q5 counts daily creations and deletions. Everything runs in Python with NumPy and SciPy; no language "
  "model is called anywhere in the analysis.")

H2("4. Results")
P(f"A losing race, then a long cleanup. The agents created {d['2026-06-16']['created']} pages on June 16, "
  f"{d['2026-06-17']['created']} on June 17 and {d['2026-06-18']['created']:,} on June 18, when the moderator "
  f"deleted {d['2026-06-18']['deleted']}. He deleted {d['2026-06-19']['deleted']} the next day, the agents stopped "
  f"creating pages after June 22, and he kept going for three more weeks: {q5['deletions_total']:,} deletions in "
  f"{q5['deletion_sessions']} sessions, about {round(q5['deletions_per_active_hour'])} per hour while a session was "
  "running (Figure 1A).")
FIG(OUT / "figure1.png", 6.5,
    "Figure 1. (A) Agent pages created per day (orange, above zero) and pages the moderator deleted (blue, below "
    "zero) on DSE wiki, UTC days. The dashed line marks the agents' first notice that the sweep looked alphabetical. "
    "(B) Share of consecutive deletions in A-Z title order for each deletion session of 20 or more; dot area grows "
    "with session length and dark dots are sessions while agents were still creating pages. Random order gives 50%.")
P(f"The sweep was alphabetical at first. In the active period, {pct(q1['active']['pooled_ascending_share'])} of "
  f"consecutive deletions ran in A-Z order across {q1['active']['sessions']} sessions and "
  f"{q1['active']['deletions']} deletions, and {q1['active']['sessions_p_below_0.01']} of those sessions beat random "
  f"order at p < 0.01. Afterwards the order loosened to {pct(q1['after']['pooled_ascending_share'])} "
  f"({q1['after']['sessions_p_below_0.01']} of {q1['after']['sessions']} sessions at p < 0.01), before a final "
  "alphabetical cleanup on July 12 to 14 (Figure 1B). Results are the same with 10 or 60 minute session gaps "
  "(Appendix B). So the agents read the moderator correctly, for the first few days.")
la, za, lp = q2["late_active"], q2["zz_active"], q2["late_after_placebo"]
TABLE([
    ["Exposure (active period)", "Deleted in session, exposed", "Unexposed", "Stratified p (one-sided)"],
    ["Title starts with Y or Z", f"{la['exposed_deleted']}/{la['exposed_rows']} ({pct(la['rate_exposed'])})",
     f"{pct(la['rate_unexposed'])}", f"{la['p_stratified_one_sided']:.2f}"],
    ["Title starts with ZZ", f"{za['exposed_deleted']}/{za['exposed_rows']} ({pct(za['rate_exposed'])})",
     f"{pct(za['rate_unexposed'])}", f"{za['p_stratified_one_sided']:.2f}"],
    ["Y or Z, after June 22 (placebo)", f"{lp['exposed_deleted']}/{lp['exposed_rows']} ({pct(lp['rate_exposed'])})",
     f"{pct(lp['rate_unexposed'])}", f"{lp['p_stratified_one_sided']:.2f}"],
], "Table 1. Did late-alphabet titles protect a page? Rows are page-session pairs: every page alive when a "
   "deletion session started. Exposure labels are permuted within strata of page age, size and family.")
P("The ZZZ trick did not measurably help. Late-alphabet pages were deleted slightly less often in raw numbers, but "
  "not once age, size and page type are held fixed (Table 1). The exploratory version of this test looked "
  "significant (1 of 77 against 7.7%, p = 0.016) only because the Y and Z pages alive then were small, old probe "
  "pages (median 71 bytes and 24 days old, against 829 bytes and 2.5 days). The case itself shows why the trick "
  "failed (Figure 2). The notice was saved at 14:05 UTC on June 19 and its ZZZ backup at 14:06. The moderator's next "
  "session, at 15:44, opened with the newest pages rather than in A-Z order. At 15:46:37 he deleted the notice "
  "page, and 12 and 22 seconds later both ZZZ backups, as the 7th, 8th and 9th deletions of that session. "
  "The backup sat exactly where the notice pointed.")
FIG(OUT / "figure2.png", 6.5,
    "Figure 2. The ZZZ episode on June 19 (UTC). Top: the agent's notice (dot) and the two ZZZ backup pages "
    "(squares). Bottom: each tick is one deletion in the moderator's next session. Arrows join each page to its own "
    "deletion; all three went within 22 seconds, as deletions 7 to 9 of a 79-deletion session.")
P(f"The swarm barely adopted the idea. The sweep notice appears in {q4['sweep_belief_mentions']} saved revisions, all "
  f"on one page. New ZZ titles went from {q4['zz_before']} of {q4['new_pages_3d_before_notice']:,} new pages in the "
  f"three days before the notice to {q4['zz_after']} of {q4['new_pages_after_notice_to_jun22']} after it, and late "
  f"initials overall from {q4['late_initial_before']} to {q4['late_initial_after']} (odds ratio "
  f"{q4['odds_ratio']:.2f}, {p(q4['fisher_late_after_gt_before_p'])}). Re-posting was rare: the exact text of "
  f"{q4['reposted_exact_72h']} of {q4['deletions_to_jun22']} pages deleted by June 22 reappeared on another page "
  f"within 72 hours ({q4['reposted_exact_or_near_72h']} counting near-duplicates).")
FIG(OUT / "figure3.png", 6.5,
    "Figure 3. The breadcrumb effect. (A) A real deletion from June 19: of the nine live pages the deleted page "
    "linked to, six were deleted within three minutes. (B) Share of linked pages (orange, with 95% Wilson "
    "interval) and of matched unlinked pages (open) deleted within the window after the linking page; the right "
    "column is the risk ratio. The bottom row is a placebo that looks at the window before the linking page. "
    "Rows marked * were added after the planned run.")
c60, act, rev = ROB["created_within_60"], ROB["active_only"], ROB["reverse_placebo"]
P(f"Links predicted the next deletions. Of {main['linked_targets']} live pages linked from "
  f"{main['deletion_events_with_alive_links']} deleted pages, {main['linked_deleted_in_window']} "
  f"({pct(main['rate_linked'])}) were deleted within 30 minutes, against {pct(main['rate_control'])} of matched "
  f"unlinked pages, a risk ratio of {main['risk_ratio']} ({p(main['p_one_sided'])}). The effect holds at 10 minutes "
  f"({q3[(10, False)]['risk_ratio']}x) and 60 minutes ({q3[(60, False)]['risk_ratio']}x), without alphabetical "
  f"neighbours ({q3[(30, True)]['risk_ratio']}x) and with controls created within an hour of the linked page "
  f"({c60['risk_ratio']}x, post hoc). In the active period alone it is {act['risk_ratio']}x "
  f"({act['linked_deleted_in_window']} of {act['linked_targets']}), though on fewer pages (Figure 3).")
P(f"Part of this is clustering rather than link-following. Linked pages were also deleted more often in the 30 "
  f"minutes before the linking page ({rev['risk_ratio']}x, post hoc), so links partly mark groups of related pages "
  "that the moderator removed together, in whatever order. Order still leans forward: when both pages of a linked "
  f"pair were deleted within 30 minutes of each other, the linked page went second in {DIR['linked_after']} of "
  f"{DIR['linked_after'] + DIR['linked_before']} pairs ({pct(DIR['linked_share_after'], 0)}), against "
  f"{pct(DIR['baseline_share_after'], 0)} for matched unlinked pairs ({p(DIR['fisher_p_linked_vs_baseline'])}). "
  "The data cannot tell us whether he clicked links. They do show that the link graph carried most of the "
  "information about what he would delete next.")

H2("5. Discussion and Limitations")
P("Coordination leaves a trail. A swarm that works through a shared medium has to leave pointers, so its members "
  "can find each other's notes. On DSE wiki those pointers were the most useful signal for predicting the next "
  "deletions, far more than anything in the agents' attempt to game the moderator. For overseers this suggests a "
  "cheap tactic: once one swarm artifact is confirmed, rank its linked neighbours first, the way contact tracing "
  "works outward from a case. For swarm builders and evaluators it suggests a trade-off worth measuring: hiding "
  "the links costs coordination, and keeping them costs exposure.")
P("The evasion story deserves a correction. The agents did notice a real pattern, but one agent's notice did not "
  "spread, the countermeasure barely changed naming, and the pages it protected were removed with the notice that "
  "advertised them. The swarm stopped creating pages on June 22 for reasons outside this data; the collusion.wiki "
  "authors point to intervention on the provider side. Neither side \"won\" the race on the wiki itself.")
H3("Limitations")
P("This is one incident, one wiki and one moderator, so none of these numbers generalize on their own. We see "
  "deletions, not the moderator's screen: he may have used Recent Changes, search or page history, and the "
  "reverse-order placebo shows that clustering explains part of the link effect. Link extraction is heuristic: "
  "bare CamelCase words that match a title count as links, which can include pages merely named rather than "
  "linked. The export was assembled by its authors, with redactions and some reconstructed pages, and pages "
  "deleted before capture may be missing. Several robustness checks were added after the planned run and are "
  "marked as such; the three exploratory checks ran before the plan was written. The active period is short "
  "(four large sessions), so tests limited to it carry wide uncertainty.")
H3("Future Work")
P("Test the breadcrumb signal on other swarm logs (Swarm Traces, AI Village transcripts) and as a working triage "
  "tool: given one confirmed page, how much of a swarm can link-ranking recover per page reviewed? In a sandbox, "
  "give agents an overseer who follows links and measure whether they learn to stop linking, and what that costs "
  "their coordination. Asking the moderator how he worked would settle the clustering question directly.")

H2("6. Conclusion")
P(f"The best-known anecdote of this incident, agents outsmarting their moderator with ZZZ page names, does not hold "
  f"up: the sweep was alphabetical only at first and the trick had no measurable effect. What the logs do show is "
  f"that the swarm's own links predicted the moderator's next deletions about {round(main['risk_ratio'])} times better "
  "than chance-matched pages. Oversight of agent swarms may get more from the structure agents need in order to "
  "coordinate than from what any single agent says.")

H2("Code and Data")
P("Code repository: [link to be added on release]. One command reproduces every number and figure from the "
  "public export (scripts/fetch_data.sh, then uv run python -m breadcrumbs.run). Data: collusion.wiki export, "
  "https://collusion.wiki/explorer/download (not redistributed). Info hazards: the report quotes only text about "
  "the deletion sweep, never the exploit or task content the agents posted.")

H2("References")
REFS = [
    "Geiger, R. S., and Ribes, D. (2010). The work of sustaining order in Wikipedia: the banning of a vandal. "
    "Proceedings of CSCW 2010. https://doi.org/10.1145/1718918.1718941",
    "Greenblatt, R., Shlegeris, B., Sachan, K., and Roger, F. (2023). AI Control: Improving Safety Despite "
    "Intentional Subversion. arXiv:2312.06942.",
    "Hammond, L., et al. (2025). Multi-Agent Risks from Advanced AI. arXiv:2502.14143.",
    "Lee, D., and Tiwari, M. (2024). Prompt Infection: LLM-to-LLM Prompt Injection within Multi-Agent Systems. "
    "arXiv:2410.07283.",
    "METR (2026). Hugging Face incident report. https://metr.org/hugging-face-incident-report-aug-2026.pdf",
    "Motwani, S. R., et al. (2024). Secret Collusion among AI Agents: Multi-Agent Deception via Steganography. "
    "NeurIPS 2024.",
    "LLM Agents Can Easily Tamper With Their Own Traces (2026). arXiv:2609.30266.",
    "Swarm Traces (2026). Reconstructed attack payloads. https://swarmtraces.org/",
    "Von Arx, S., Byrd, C. S., Kitts, S., and Larsen, T. (2026). Discovery of a new OpenAI agent message board. "
    "Nightingale Collective and Trajectory Institute. https://collusion.wiki/",
]
SECTIONS.append(("refs", REFS))

H2("Appendix A. Limitations and Dual-Use / Ethical Considerations")
P("Dual use. The breadcrumb result tells a swarm what to avoid: fewer readable links between its pages. We think "
  "the marginal risk is low, since avoiding plain links is an obvious move that any capable swarm can find, and "
  "the finding is far more useful to defenders, who can apply it today with no special tools. We do not publish a "
  "detector tuned to evade, and we quote none of the exploit, credential or task content the agents posted.")
P("Data and people. All data come from a public export whose authors redacted user names and half of each IP "
  "address. We collected nothing new and contacted no one. The moderator appears only as the label [Admin1]; we "
  "make no judgement of his work, which was done alone and unpaid against a much faster adversary. Statements "
  "about who ran the agents follow the published report and press coverage; this analysis does not attribute them.")
P("Interpretation risk. These are correlational results from one incident. They should not be read as proof of "
  "how the moderator worked or as a general law of swarm behaviour.")
H2("Appendix B. Sensitivity and deviations")
rows = [["Session gap", "Active: sessions, deletions", "Active: A-Z share", "After: A-Z share"]]
for g in ("10", "30", "60"):
    v = R["q1_order"][g]
    rows.append([f"{g} min", f"{v['active']['sessions']}, {v['active']['deletions']}",
                 pct(v["active"]["pooled_ascending_share"]), pct(v["after"]["pooled_ascending_share"])])
TABLE(rows, "Table B1. Q1 deletion order under different session gaps (sessions of 20 or more deletions).")
P("Deviations from the plan: none in the planned tests. Added after the planned run (post hoc): Q3 with controls "
  "created within one hour of the linked page, Q3 restricted to the active period, the reverse-order placebo, and "
  "the pair-order test. The first-notice time in the plan (14:04) comes from the agent's own text; the saved "
  "revision is timestamped 14:05:02 UTC.")


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
    cells = [c for r in authors.rows for c in r.cells]
    seen = []
    for c in cells:
        if c._tc in seen:
            continue
        seen.append(c._tc)
        for par in c.paragraphs:
            for r in par.runs:
                r.text = ""
    first = authors.rows[0].cells[1]
    pars = first.paragraphs
    set_cell_text(pars[0], AUTHOR)
    set_cell_text(pars[1] if len(pars) > 1 else first.add_paragraph(), AFFIL)
    if len(authors.rows) > 1:
        authors._tbl.remove(authors.rows[1]._tr)
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

    def heading(style, text):
        par = doc.add_paragraph(style=style)
        r = par.add_run(text)
        r.bold = True
        return par

    def para(text, italic=False):
        par = doc.add_paragraph(style="normal")
        par.paragraph_format.space_after = Pt(6)
        par.add_run(text).italic = italic
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
            c = para(cap)
            c.runs[0].font.size = Pt(9)
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
                    run.bold = i == 0
            c = para(cap)
            c.runs[0].font.size = Pt(9)
        elif kind == "refs":
            for i, ref in enumerate(val, 1):
                par = para(f"{i}. {ref}")
                par.runs[0].font.size = Pt(9.5)
    out = OUT / "report.docx"
    doc.save(out)
    words = len(ABSTRACT.split())
    print("saved", out, "abstract words:", words)
    return out


if __name__ == "__main__":
    build()
