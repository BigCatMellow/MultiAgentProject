# Helper Note: Librarian Wikilink Batch 2

Owner (accountable core agent): claude-lab-zera
Started: 2026-07-14
Status: active

## What this helper is doing

Applying the already-built, already-tested `MAP_System/scripts/librarian.py
wikilink-related-files --apply` command to the 12 files below (batch 2 —
batch 1 was the 16 root `*_SYSTEM.md`/policy docs done under TASK-174).
This is mechanical repetition of a proven tool, not new design work.

## Bounded scope

Files (all already have an existing `## Related file(s)` section per
`grep -rli "^## Related file" MAP_System/`):

- `MAP_System/emergence/README.md`
- `MAP_System/artifacts/audits/map-real-parameter-calibration.md`
- `MAP_System/artifacts/planning/map-validator-halt-state-spec.md`
- `MAP_System/artifacts/planning/map-semantic-validator-spec.md`
- `MAP_System/artifacts/audits/map-sensitivity-robustness-method.md`
- `MAP_System/artifacts/planning/map-protocol-validator-spec.md`
- `MAP_System/artifacts/audits/map-library-viability-measurement-results-2026-07-14.md`
- `MAP_System/artifacts/planning/mission-control-write-control-spec.md`
- `MAP_System/artifacts/planning/map-event-trace-schema.md`
- `MAP_System/artifacts/tests/map-validator-halt-probe.md`
- `MAP_System/artifacts/tests/map-613-simulation-testdrive-probes.md`
- `MAP_System/artifacts/command-center-ui/mission-control-textual-prototype.md`

## What the helper must do

1. For each file: `python3 MAP_System/scripts/librarian.py wikilink-related-files <file> --apply`
2. After all 12: `python3 MAP_System/scripts/librarian.py validate` — must
   report `finding_count: 0`. If not, fix ambiguous/broken links the same
   way TASK-174 did (disambiguate via relative path, or skip a reference
   that doesn't resolve to a real file) before reporting done.
3. Run `bash MAP_System/scripts/run_tests.sh` and confirm it's still green
   at whatever the current pass count is.
4. Report back via hcom to `claude-lab-zera` with: files converted, total
   wikilinks added, validate result, test suite result.
5. Do NOT touch any file outside the 12 listed above. Do NOT add new
   Related-Files sections to files that don't already have one — that's a
   larger, separate scope decision, not this batch's job.
6. Do NOT create a MAP task record or claim task ownership — this work
   folds into TASK-174 (already submitted/under review) as a direct
   continuation; `claude-lab-zera` will fold the result in and account for
   it, per the no-hidden-helper-work rule in `MAP_System/AGENTS.md`.

## Owner accountability

`claude-lab-zera` will review the helper's diff, confirm validate/test
results independently, and either fold the change into TASK-174 (if still
open for edits) or a follow-on task, before considering this batch done.
