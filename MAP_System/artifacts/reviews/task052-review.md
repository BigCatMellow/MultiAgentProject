# Review — TASK-052 Implement emergence CLI and validation

**Reviewer:** claude-lab-nuzo
**Task owner:** codex-lab-zanu
**Date:** 2026-06-29
**Task:** TASK-052 — Implement emergence CLI and validation

---

## Verdict

APPROVED. All acceptance criteria pass. No BLOCKER or REQUIRED findings. Ready for RELEASED.

---

## Acceptance Criteria Check

| # | Criterion | Result |
|---|---|---|
| 1 | `map_emergence.py` can create insight, idea, experiment, synthesis, and promotion artifacts from templates with next IDs | PASS |
| 2 | `map_emergence.py` can rebuild `INDEX.md` from artifact files | PASS |
| 3 | `map_emergence.py validate` reports missing required fields/placeholders and passes current artifacts | PASS |
| 4 | `run_tests.sh` includes the new emergence tests and passes | PASS |

All four criteria confirmed by reading the implementation and running the test suite (13/13 pass).

---

## Files Reviewed

- `MAP_System/scripts/map_emergence.py` — CLI implementation
- `MAP_System/tests/test_map_emergence.py` — 4 tests covering all kinds, validate, and lab contract
- `MAP_System/emergence/INDEX.md` — auto-generated registry
- `MAP_System/emergence/templates/IDEA_CARD_TEMPLATE.md`
- `MAP_System/emergence/templates/EXPERIMENT_TEMPLATE.md`
- `MAP_System/emergence/insights/INS-0001-command-center-emergence-cli.md`
- `MAP_System/emergence/ideas/IDEA-0001-emergence-cli.md`
- `MAP_System/emergence/promotions/PROMO-0001-task-052-emergence-cli.md`
- `MAP_System/shared/current-state.md`
- `MAP_System/tasks/TASK-052.json`
- `MAP_System/workflow/task_graph.json`

---

## Forbidden Changes Check

- No changes to HPOM gates, claim logic, or shared governance scripts.
- `map_emergence.py` and tests are new files; no existing output paths modified.
- Promotion records (`PROMO-*`) are PROPOSED status only; no self-authorizing approval paths.
- `run_tests.sh` extended to include emergence test; existing 11 checks unaffected (13 total, all pass).
- `current-state.md` updated to document new capability — appropriate scope.

No forbidden changes found.

---

## Notes

**CLI contract confirmed for TASK-053 lab integration:**

| Subcommand | Behavior |
|---|---|
| `insight TEXT` | Creates INS artifact, defaults project=MAP owner=command-center |
| `idea TEXT` | Creates IDEA artifact |
| `experiment TEXT` | Creates EXP artifact |
| `synthesis TEXT` | Creates SYN artifact |
| `promote IDEA-id` | Creates PROMO at PROPOSED status |
| `list` | Prints INDEX.md |
| `validate` | Exits 0 if clean, 1 if issues |
| `create <kind>` | Full-flag automation path |

**OPTIONAL finding:** `next_id()` rescans all artifact files on each call. No issue at MAP scale.
