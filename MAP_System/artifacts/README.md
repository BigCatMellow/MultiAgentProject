# Artifacts

Artifacts are durable work products and historical evidence. They are useful
memory, but they are not automatically current truth.

## Subdirectories

- `planning/` - designs and implementation plans.
- `reviews/` - review records and approval notes.
- `tests/` - test notes and verification records.
- `releases/` - release checklists and release-gate evidence.
- `reports/` - audit reports, health reports, state reports, and structural reviews.
- `research/` - research outputs.
- `drafts/` - unfinished or exploratory work.
- `final/` - finished deliverables.
- `code/` - code artifacts that are not part of the live runtime.
- `command-center-ui/` - historical Command Center UI repair/review evidence.

## How Agents Should Use This Directory

Read artifacts when:

- a task explicitly names them;
- a current doc links to them;
- you need provenance for why a decision was made;
- you are reviewing a completed task.

Do not treat old artifact paths or old commands as live instructions without
checking `shared/current-state.md`, `shared/decisions.md`, and the current code.
