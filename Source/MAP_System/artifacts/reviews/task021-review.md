# Review — TASK-021: Autonomous Claim Loop

Reviewer: claude  
Date: 2026-06-19  
Verdict: CHANGES_REQUESTED

## Findings

| ID | Severity | Area | Finding |
|---|---|---|---|
| R-01 | REQUIRED | `choose_after_claim` | Routes to `END` for `claim_failed`/`no_ready_task` unconditionally. In daemon mode (`--once=False`, no iteration cap), a claim race or empty-ready-list terminates the loop. Fix: route to `"reconcile"` unless `config.once` or iteration cap reached. |
| R-02 | WARN | `run_loop` | When `operator_interrupt` fires, `invoke()` returns with `__interrupt__` but `run_loop` ignores it and returns 0. Daemon exits silently with no indication it paused. Acceptable for V1 if documented, but operator won't know to restart. |
| R-03 | MINOR | `submit_node` L231-234 | `if config.dry_run: release_task(...)` block is unreachable — `claim_node` with `dry_run=True` returns `"dry_run_no_claim"`, which routes to `"end"` before reaching `submit`. Dead code; remove. |

## Required Fix (R-01)

```python
def choose_after_claim(state: LoopState, config: Config) -> Literal["submit", "reconcile", "end"]:
    if state.get("last_result") == "claimed":
        return "submit"
    if config.once or reached_iteration_cap(state, config):
        return "end"
    return "reconcile"
```

And update `build_loop_graph`:
```python
graph.add_conditional_edges(
    "claim",
    lambda state: choose_after_claim(state, config),
    {"submit": "submit", "reconcile": "reconcile", "end": END},
)
```

## Passing Checks

- `py_compile` clean
- `validate_task_graph` passes
- `--once --dry-run`: runs single cycle, exits cleanly
- Claim, heartbeat, submit, export: flow correct
- Handler failure → release → exception propagated: correct
- Shutdown → release: correct
- Claim race: claim_failed logged, task unchanged
- Graph structure: reconcile → poll → claim → submit → reconcile: correct when claimed

## Verification Command

After R-01 fix, verify daemon mode loops through claim race:

```python
# Simulate: claim_failed, once=False, no cap
config = Config(..., once=False, max_iterations=0)
state = {"last_result": "claim_failed", "iterations": 1}
assert choose_after_claim(state, config) == "reconcile"
```
