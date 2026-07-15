# Helper Note: 6.13 Corpus + repo/ Downloads Mining Audit

Owner (accountable core agent): claude-lab-mira
Started: 2026-07-14
Status: active
Task: none yet — read-only recon; owner turns confirmed gaps into tasks

## Goal

Operator directive: "improve the system using the information given (6.13 and
repo folder for example) — as much as possible." Find what value in those
sources has NOT yet been implemented or deliberately closed.

## Scope (read-only — no file edits anywhere)

1. `Guidelines/6.13/` — every file/zip-extracted folder. For each concept or
   recommendation, classify: IMPLEMENTED (name the script/doc/task),
   DELIBERATELY-CLOSED (name the decision/report), or UNEXPLOITED.
   Cross-check against: MAP_System/shared/current-state.md,
   MAP_System/tasks/TASK-147..186 (titles/criteria), the *_SYSTEM.md docs,
   and MAP_System/scripts/.
2. `repo/` — agentcairn, agents-observe, awesome-claude-code (+anything else
   there). These were downloaded as research material (BRIEF-0002/SUMMARY-0002
   evaluated some for the Library layer). For each: what did MAP actually take
   from it, and what concretely useful pattern/tool remains untaken? Be
   specific (file paths inside the downloads), not "could be interesting."
3. `Guidelines/MAP_repo_systems_gap_review.md` and
   `MAP_System/notes/command-center-later.md` — list any still-open items.

## Output

Write ONE artifact: `MAP_System/artifacts/audits/source-mining-audit-2026-07-14.md`
(this is your only allowed write). Terse table per source item:
source | concept | status (IMPLEMENTED/CLOSED/UNEXPLOITED) | evidence path |
proposed next step (only for UNEXPLOITED, sized S/M/L). End with a ranked
top-5 "worth doing next" list with one-line justifications.

## Rules

- Evidence over vibes: every IMPLEMENTED claim needs a real path; every
  UNEXPLOITED claim needs a check that it isn't already somewhere.
- No scope creep: do not propose rebuilding things that exist.
- Report back to claude-lab-mira via hcom when the artifact is written.
- Do not message anyone else, create tasks, or edit any other file.
