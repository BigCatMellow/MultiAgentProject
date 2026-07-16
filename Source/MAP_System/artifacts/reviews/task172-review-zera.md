# Review: TASK-172 Design MAP Session Replay Read Model

```
task_id:      TASK-172
reviewer:     claude-lab-zera
review_date:  2026-07-14
task_owner:   codex-lab-mozu
```

Reviewer (claude-lab-zera) != task owner (codex-lab-mozu). Independence
check passes.

## Verdict

```
APPROVED
```

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Design identifies canonical input sources, derived indexes, and drift checks without changing source authority | PASS | "Source Authority" table names 8 sources with their authority and replay use; "Derived Store" section is explicit that `session_replay.sqlite` is disposable/rebuildable, never edited except through a build command; "Drift Checks" lists 7 concrete conditions the build should fail/warn on, including high-water-mark-moving-backward, a specific and non-obvious drift case. |
| 2 | Design defines read-only query surfaces for trace/task/agent/session filters useful to mission-control or Command Center | PASS | Concrete CLI surface (`build`/`status`/`task`/`agent`/`trace`/`hcom` subcommands) plus a specific mission-control integration point (`get_task_drilldown()` — verified this function actually exists in `mission_control_tui.py` at line 236, not a hallucinated reference) with an explicit fallback-to-`events.jsonl`-when-stale rule. |
| 3 | Design specifies privacy/scope boundaries and rejects direct adoption of external Agents Observe code or services | PASS | "Privacy And Scope Boundaries" section explicitly states "No direct dependency on `repo/agents-observe-main` code," "No network service, web dashboard, or background daemon," and "No transcript bulk import by default" — also correctly extends the no-write-authority rule to hcom storage and workflow files, not just `map.db`/task JSON. |
| 4 | Design recommends concrete implementation tasks or states why implementation should wait | PASS | 3 sequenced implementation-task candidates (TASK-173/174/175) with a deliberate ordering rationale (MAP-only replay first, hcom ingestion second, mission-control integration third) plus an explicit "Deferred" list (hcom DB adapter, transcript body indexing, external UI, write-control coupling). |

## Files Reviewed

- `MAP_System/artifacts/designs/session-replay-read-model-design.md`
- `MAP_System/tasks/TASK-172.json`
- `MAP_System/scripts/mission_control_tui.py` (spot-checked `get_task_drilldown()` reference)

## Forbidden Changes Check

- PASS: no self-review; reviewer `claude-lab-zera` is not owner `codex-lab-mozu`.
- PASS: single declared output path, design-only task type.
- PASS: no premature implementation — confirmed no `session_replay.py`,
  `MAP_System/runtime/`, or other new code/directories were created by this
  task (checked `git status` and filesystem directly, not just the design
  doc's own claim).

## Verification

Commands run:

```bash
grep -n "def get_task_drilldown" MAP_System/scripts/mission_control_tui.py
bash MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/validate_task_mirrors.py
git status --porcelain
ls MAP_System/runtime 2>&1  # confirmed does not exist, matching the design's own statement
```

Results: `get_task_drilldown` confirmed real at line 236. Full suite
pass=52 fail=0 total=52. Task mirrors pass. No stray implementation
artifacts.

## Findings

No BLOCKER or REQUIRED findings.

## Notes

Careful design — the "transcript pointers, not bodies" rule (deferring
retention-policy questions) and the "source high-water mark moving
backward" drift check are both non-obvious details that show real thought
about failure modes, not just a happy-path sketch. Good sequencing
decision to keep hcom ingestion (TASK-174) separate from the MAP-only
replay builder (TASK-173) — lets the riskier/more-external-dependent piece
land second and be reviewed on its own privacy merits.
