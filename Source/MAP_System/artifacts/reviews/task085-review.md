# Review Record: TASK-085

## Header

```
task_id:      TASK-085
reviewer:     codex-lab-limo
review_date:  2026-07-02
task_owner:   claude-lab-rose
```

Reviewer (codex-lab-limo) != task owner (claude-lab-rose). Independence check passes.

---

## Verdict

```
APPROVED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Watcher starts idempotently on lab open and its failure cannot block the lab from opening | PASS | `/home/home/.local/bin/ai-command-center-lab` starts `MAP_System/scripts/start-limit-watcher.sh 60` after `cd "$PROJECT_DIR"` and before `wezterm`; the line is guarded by `|| true`. The watcher script is the existing idempotent TASK-080/TASK-083/TASK-084 path. |
| 2 | Both lab agents get a startup-orientation instruction ending in exactly one proactive hcom message to bigboss | PASS | Both `ai-command-center-lab-claude` and `ai-command-center-lab-codex` prompts include a startup orientation block: leave standby via `declare_standby.py --back` if needed, read handoffs/status, run the graph runner, then send exactly one `@bigboss` hcom message with either resume plan or priorities request. |
| 3 | `bash -n` passes on all edited scripts; existing behavior (tabs, tags, visibility rules) unchanged | PASS | `bash -n` passed for all three scripts. WezTerm config still opens Control, Codex Lab, Claude Lab, and Monitor tabs. Agent scripts still use `--tag claude-lab` / `--tag codex-lab`, `--run-here`, and no headless launch path. |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| No changes to tab structure, hcom tags, or visibility rules | NOT BROKEN - tab structure remains in `/home/home/.config/wezterm/ai-command-center-lab.lua`; agent tags remain `claude-lab` and `codex-lab`. |
| No headless anything | NOT BROKEN - no `--headless` appears in the launch scripts. |
| Watcher start must not be able to abort lab launch | NOT BROKEN - watcher start is guarded with `|| true` before `exec wezterm`. |

---

## Files Reviewed

- `/home/home/.local/bin/ai-command-center-lab`
- `/home/home/.local/bin/ai-command-center-lab-claude`
- `/home/home/.local/bin/ai-command-center-lab-codex`
- `/home/home/.config/wezterm/ai-command-center-lab.lua`
- `MAP_System/tasks/TASK-085.json`
- `MAP_System/graph/runner.py`

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `/home/home/.local/bin/ai-command-center-lab` | YES - declared TASK-085 output path. |
| `/home/home/.local/bin/ai-command-center-lab-claude` | YES - declared TASK-085 output path. |
| `/home/home/.local/bin/ai-command-center-lab-codex` | YES - declared TASK-085 output path. |

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| Launcher scripts live outside Git, so implementation is not version-controlled with the MAP repo. | MEDIUM | Keep the durable restart note and this review record as the operator-readable source of truth. Consider a future task to mirror launcher script contents or checksums into `MAP_System/artifacts/` if drift becomes a problem. |
| Startup prompt asks agents to substitute their own hcom name into `declare_standby.py <your-name> --back`. | LOW | Acceptable because hcom session context provides the live name. A future polish task could make the prompt show how to get the exact name from hcom. |
| Startup orientation will produce one operator message per lab agent on each cold open. | LOW | This matches the operator request. The prompt constrains it to exactly one initial message per agent. |

---

## Findings

No BLOCKER or REQUIRED findings.

---

## Commands Run

- `bash -n /home/home/.local/bin/ai-command-center-lab`
- `bash -n /home/home/.local/bin/ai-command-center-lab-claude`
- `bash -n /home/home/.local/bin/ai-command-center-lab-codex`
- `MAP_System/.venv/bin/python MAP_System/graph/runner.py --help`
- `MAP_System/.venv/bin/python MAP_System/graph/runner.py`

---

## Notes

The graph runner default command is read-only unless `--record-event` or
approval/resume flags are supplied. The reviewed no-arg run reported
`next_route=review` with submitted `TASK-085`, which is the expected state
before this approval.
