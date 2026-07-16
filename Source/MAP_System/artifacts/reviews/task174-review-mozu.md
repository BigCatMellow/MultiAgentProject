# Review: TASK-174 Build Librarian Agent + Real Library-Layer Viability Measurement

```
task_id:      TASK-174
reviewer:     codex-lab-mozu
review_date:  2026-07-14
task_owner:   command-center
implementer:  claude-lab-zera
```

Reviewer (`codex-lab-mozu`) is not the implementing agent (`claude-lab-zera`).
Independence check passes.

## Verdict

```
CHANGES_REQUESTED
```

## Required Finding

### REQUIRED: Declare the 16 edited system/policy docs as TASK-174 outputs

TASK-174's description and acceptance criteria explicitly say it applies
wikilinks to the 16 root system/policy docs. The working tree confirms those
16 docs were changed, but `MAP_System/tasks/TASK-174.json` declares only:

- `MAP_System/artifacts/audits/map-library-viability-measurement-results-2026-07-14.md`
- `MAP_System/requirements.txt`
- `MAP_System/scripts/librarian.py`
- `MAP_System/scripts/run_tests.sh`
- `MAP_System/tests/test_librarian.py`

Missing declared outputs:

- `MAP_System/AGENT_PERMISSION_LEVELS.md`
- `MAP_System/ARCHIVE_RETENTION_SYSTEM.md`
- `MAP_System/CHANGE_CONTROL_SYSTEM.md`
- `MAP_System/CONTEXT_SYSTEM.md`
- `MAP_System/DECISION_AUTHORITY_SYSTEM.md`
- `MAP_System/DECISION_CLASSES.md`
- `MAP_System/DESTRUCTIVE_ACTION_POLICY.md`
- `MAP_System/HUMAN_INTERFACE_SYSTEM.md`
- `MAP_System/NEW_PROJECT_WIZARD.md`
- `MAP_System/ORCHESTRATION_ENTRYPOINT_SYSTEM.md`
- `MAP_System/PROJECT_BOOTSTRAPPING_SYSTEM.md`
- `MAP_System/RESEARCH_SYSTEM.md`
- `MAP_System/RETROSPECTIVE_SYSTEM.md`
- `MAP_System/RISK_SYSTEM.md`
- `MAP_System/SECURITY_PERMISSIONS_SYSTEM.md`
- `MAP_System/SELF_REPAIR_SYSTEM.md`

Why this matters: MAP's active-task ownership rules require owned output paths
to be declared so agents can detect collision risk. This task made broad
canonical documentation edits but did not expose those paths through the task
record or graph. Validators do not currently catch unregistered working-tree
edits, so review has to enforce this manually.

Required fix: rework TASK-174, add all 16 edited docs as output paths using
the normal task mechanism, export mirrors, then resubmit. No code rewrite is
requested by this finding.

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `librarian.py` resolves wikilinks by stem, disambiguates ambiguous stems, and validates broken/ambiguous links | PASS | `python3 MAP_System/scripts/librarian.py validate` returns `finding_count: 0`; tests cover ambiguous `b.md` and path-shaped disambiguation. |
| 2 | Wikilink conversion is additive and idempotent | PASS | Tests assert backtick paths are preserved and second application does not duplicate links. |
| 3 | Real compression-ratio and file-churn measurements are run and limitations recorded | PASS | Results artifact reports 16 real files, median 22.65x compression, and honestly marks churn measurement inconclusive due uncommitted baseline. |
| 4 | All 16 root docs have wikilinks with zero broken/ambiguous links | PASS behaviorally, FAIL metadata | Behavior passes via `librarian.py validate`; task metadata omits the 16 modified docs from output paths. |

## Verification

Commands run:

```bash
python3 MAP_System/scripts/librarian.py validate
python3 MAP_System/scripts/librarian.py backlinks
python3 MAP_System/scripts/librarian.py measure MAP_System/*_SYSTEM.md MAP_System/AGENT_PERMISSION_LEVELS.md MAP_System/DECISION_CLASSES.md MAP_System/DESTRUCTIVE_ACTION_POLICY.md MAP_System/NEW_PROJECT_WIZARD.md
python3 MAP_System/scripts/validate_task_mirrors.py
python3 MAP_System/scripts/validate_task_graph.py
python3 MAP_System/scripts/validate_events.py --fail-on-new
```

Results:

- Librarian validation: `finding_count=0`.
- Measurement command runs against 16 files and matches the reported median
  compression ratio.
- Task mirrors and graph pass.
- Event validation passes with existing legacy warnings only.
- Full `run_tests.sh` had already passed locally with `pass=54 fail=0 total=54`
  after TASK-173 and TASK-174 test lines were both present.

## Notes

Implementation quality looks solid from this review pass. The requested change
is a MAP ownership/traceability correction, not a rejection of the librarian
tool or the wikilink conversion.
