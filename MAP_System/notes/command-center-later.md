# Command Center Later

## Status

- Purpose: deferred MAP items that need operator input or a deliberate next phase.
- Last reviewed: 2026-06-29 (Phase 2 / HPOM sprint close)

---

## Done — Closed Items (HPOM sprint 2026-06-29)

The following items from the original checklist are now fully implemented and tested:

| Item | Closed by |
|---|---|
| Strict task promotion gate (promote_task.py) | TASK-035 |
| Claim-time metadata defense (claims.py) | TASK-035/044 |
| Enforce reviewer != owner (no-self-review) | TASK-044 |
| Block approval when review artifact missing | TASK-047 |
| Store review result in artifacts/reviews/ | TASK-047 |
| Aider wrapper (clean git, scope, interactive) | TASK-049 |
| Local model health checks (local_assistant_health.py) | TASK-036 |
| Ollama helper runner (local_runner.py) | TASK-048 |
| CONFLICT status freeze (flag_conflict.py) | TASK-040 |
| Release gate with checklist (release_task.py) | TASK-038 |
| Decision log validation (validate_decisions.py) | TASK-041 |
| Metrics dashboard (map_metrics.py) | TASK-043 |
| HPOM shared-state metadata (validate_shared_state.py) | TASK-039 |

---

## Open — Still Pending

### Git Baseline (PRIORITY: HIGH)

The entire HPOM sprint (~200 file changes, TASK-035 through TASK-051) has never
been committed. The working tree has diverged significantly from the last commit.

Before using Aider for broad MAP work, make a clean commit:

```bash
git status
git add -p   # review hunks; skip secrets, private notes, runtime DB
git commit -m "HPOM sprint: gates, local assistants, cleanup"
git push origin main
```

Before pushing, verify:
- no API keys or secrets in staged files
- no unwanted Pathwell story/private files
- `MAP_System/map.db` is excluded by .gitignore

### First Real Workflow Target (PRIORITY: HIGH — command-center decision)

`shared/unresolved-questions.md` still asks: what is the first concrete workflow
MAP runs through its governance layer? Options: writing, software, research, or
general project management.

Without a real workflow, MAP accumulates infrastructure without proving itself.

### Reconciliation Script

`scripts/reconcile.py` exists but the "restart runbook" in the original doc
referenced `map_status.py` and the LangGraph runner. A single operator command
for session resume would be:

```bash
git status
python3 MAP_System/scripts/validate_task_graph.py
bash MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/map_metrics.py
python3 MAP_System/scripts/map_status.py
```

LangGraph runner (`graph/runner.py`) is future; do not include in current runbook.

### Task JSON Schema Validation

No formal JSON schema for `tasks/TASK-NNN.json`. The promotion gate validates
required fields, but there is no schema validator for structural correctness.

### Naming Consistency Cleanup

Minor inconsistency between artifact file name patterns:
- `artifacts/reviews/taskNNN-review.md` (no hyphen in number)
- `artifacts/releases/task-NNN-release-checklist.md` (hyphen in number)

Not blocking; cosmetic. Fix whenever reviewing the artifacts directory.

---

## Delay (Intentional)

- Automated helper spawning.
- Automated brain compaction agent.
- Full swarm-style routing.
- SQLite triggers for task-state transitions.
- Registering local models as core agents before manual use proves value.

---

## Pushback Notes

- Do not add SQLite triggers before script-level gates are proven.
- Do not let self-healing invent task intent.
- Do not automate helpers before the normal task loop stays green.
- Do not build compaction automation until active memory is actually noisy.

---

## Current Baseline (2026-06-29)

- `python3 MAP_System/scripts/validate_task_graph.py` passes.
- `bash MAP_System/scripts/run_tests.sh` passes (12/12).
- `python3 MAP_System/scripts/validate_shared_state.py` passes (0 stale files).
- `python3 MAP_System/scripts/validate_decisions.py` passes (11/11 decisions OK).
- Normal root Git is active at `/home/home/Downloads/MultiAgentProject`.
- GitHub remote `origin`: `https://github.com/BigCatMellow/MultiAgentProject.git`.
- **Working tree has ~200 uncommitted changes (entire HPOM sprint). Not yet pushed.**
- TASK-050 and TASK-051 are READY for Codex (minor fixes, no blocking issues).
