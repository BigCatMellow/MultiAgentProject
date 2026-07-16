# TASK-144 MAP Renewal Assessment

task_id: TASK-144
owner: codex-lab-veto
date: 2026-07-04
scope: operator-requested full MAP assessment and first safe cleanup batch

## Backup

Whole `MAP_System/` backup completed before renewal edits:

```text
Projects/Backups/MAP_System-backup-2026-07-04T043707Z
size: 88M
verified includes: map.db, tasks/TASK-144.json, workflow/task_graph.json
```

The backup includes `.venv` and runtime files so it can be inspected or restored
without first reconstructing the execution environment.

## Baseline Health

Initial checks before cleanup:

- `validate_task_mirrors.py`: pass
- `validate_task_graph.py`: pass
- `validate_shared_state.py --shared-dir MAP_System/shared`: 19 files checked, 0 failures, 0 warnings
- `validate_decisions.py`: 27 decisions checked, 0 failures
- `map_emergence.py validate`: 38 artifacts checked
- `map_emergence.py stale`: no findings
- `validate_repair_artifacts.py`: pass
- `validate_research_artifacts.py`: pass
- `validate_context_packets.py`: pass
- `validate_risk_registers.py`: pass

The system is basically healthy. The renewal pass found drift in live operating
surfaces and active-memory wording rather than broken core state.

## Coordination

The broadcast was split under the TASK-142 Broadcast Coordinator Convention:

- `codex-lab-veto` owns TASK-144: backup, structural/process assessment, and
  first safe cleanup batch.
- `claude-lab-magi` owns TASK-145: current external LangGraph practice research
  using the Research templates, feeding findings back to TASK-144.

This is the right use of the Research System after DEC-027: a time-sensitive
external-library practice question, not ceremony.

## Cleanup Applied

### Fixed stale canonical repo paths in live launchers

Finding: live command-center launch scripts still pointed to
`/home/home/Downloads/MultiAgentProject`, even though DEC-014 makes
`/home/home/Projects/MultiAgentProject` canonical.

Changed:

- `scripts/ai-command-center-cli`
- `scripts/ai-command-center-shell`
- `scripts/ai-command-center-antigravity`
- `scripts/agent-deck`
- `scripts/validate_canonical_repo_paths.py`

The canonical-path validator now scans these launchers, not only prose docs.

Related Emergence capture:

- `emergence/insights/INS-0016-validator-coverage-must-include-live-command-surfaces-not-only-d.md`

### Updated event-warning active guidance

Finding: `shared/current-state.md` still described legacy event warnings as an
unresolved cleanup, but TASK-142 turned that into a baseline gate.

Changed:

- `shared/current-state.md`
- `shared/improvement-backlog.md`
- `events/README.md`

Current rule: `validate_events.py --fail-on-new` accepts the historical
33-warning baseline from `events/warning_baseline.json` but fails any new
warning-worthy event lines.

### Bounded LangGraph dependency versions

Input: TASK-145 Research Summary found MAP's LangGraph patterns align with
current official 1.x practice, but `requirements.txt` had unbounded
`langgraph` and `langchain-core`.

Changed:

- `requirements.txt`

New bounds:

```text
langgraph>=1.0,<2.0
langchain-core>=1.0,<2.0
```

The unused `MapSqliteSaver.delete_thread()` completeness gap is recorded in
`shared/improvement-backlog.md` as low priority, not implemented speculatively.

### Cleaned stale backlog status

Finding: `shared/improvement-backlog.md` still listed TASK-050 and TASK-051
follow-ups as open, but those task records are approved and the relevant code
already contains the fixes.

Changed:

- `shared/improvement-backlog.md`

## Assessment By Area

### Folder Structure

The current folder structure is coherent:

- `tasks/`, `workflow/`, and `map.db` form the task state system.
- `shared/` holds current project truth and validates cleanly.
- `artifacts/` holds review/release/report/research outputs.
- `emergence/`, `repairs/`, `retros/`, and `research/` now each have a clear
  role and validator or usage rule.
- `archive/`, `logs/`, `.venv/`, `.locks/`, and backups remain non-primary
  context.

No broad folder move is recommended in this batch. The higher-value cleanup is
continuing to keep active guidance synchronized with validators and launcher
behavior.

### Process Gates

The strongest MAP systems are still the ones with scripts or gate pressure:

- task mirror reconciliation;
- task graph validation;
- review and release gates;
- decision/shared-state validators;
- event warning baseline;
- Emergence release consideration;
- canonical path validation.

The main lesson from this pass is that validators should scan live command
surfaces as well as docs when those surfaces encode policy.

Live confirmation after cleanup: when another agent claimed TASK-146 without
immediately exporting file mirrors, `validate_task_mirrors.py` blocked with a
clear SQLite-vs-file status mismatch. This is the intended behavior from
TASK-143: drift is visible before approval/release instead of silently passing.

### Emergence / Insights

Emergence is healthy and not stale:

- 38 artifacts validate.
- No stale/content findings.
- TASK-144 added INS-0016 for a real cross-cutting pattern.

No new process is needed immediately. The right improvement is to keep turning
real recurring patterns into small validators or tasks, not to require insight
records for every ordinary edit.

### Research

TASK-145 successfully exercised the Research System for the first genuine
external/current-practice question after DEC-027. That is the intended use
case. The system does not need forced sample artifacts; it needs real questions
like this one.

### LangGraph / Graph Use

Based on TASK-145's Research Summary, MAP's current `StateGraph`,
`Command(resume=...)`, `interrupt()`, and checkpointer pattern is aligned with
official current practice for the parts MAP uses. The action item was dependency
pinning, applied here.

### HPOM

HPOM is functioning as the assignment layer:

- broadcast split happened explicitly;
- Research was routed to the task shape that needed it;
- no helper was spawned unnecessarily;
- review/release gates remain intact.

Remaining HPOM friction is in the backlog: operator request worker-fit adoption
and live-vs-durable agent presentation.

## Remaining Follow-Ups

No high-confidence broad rewrite is warranted from this pass. Useful follow-ups
remain:

- implement a first-class operator request worker-fit intake habit/UI;
- improve live hcom vs durable agent status presentation;
- choose a first real general MAP workflow target to prove the system outside
  MAP maintenance;
- optionally add `MapSqliteSaver.delete_thread()` if MAP starts managing
  LangGraph thread lifecycle;
- keep historical `langgraph/` path references historical, but avoid treating
  old task records as active instructions.

## Verification After Cleanup

Focused checks run after the first cleanup batch:

```text
python3 MAP_System/scripts/validate_canonical_repo_paths.py
sh -n MAP_System/scripts/ai-command-center-cli
bash -n MAP_System/scripts/ai-command-center-shell
sh -n MAP_System/scripts/ai-command-center-antigravity
sh -n MAP_System/scripts/agent-deck
python3 MAP_System/scripts/validate_events.py --fail-on-new
python3 MAP_System/scripts/validate_shared_state.py --shared-dir MAP_System/shared
python3 MAP_System/scripts/map_emergence.py validate
python3 MAP_System/scripts/map_emergence.py stale
python3 MAP_System/scripts/validate_repair_artifacts.py
python3 MAP_System/scripts/validate_research_artifacts.py
python3 MAP_System/scripts/validate_context_packets.py
python3 MAP_System/scripts/validate_risk_registers.py
```

Full-suite verification should run before submission.

Final full-suite result before submission:

```text
MAP_System/scripts/run_tests.sh
SUMMARY pass=37 fail=0 total=37
```
