# Review Record: TASK-048

## Header

```
task_id:      TASK-048
reviewer:     claude-mako
review_date:  2026-06-29
task_owner:   codex-live
```

Reviewer (claude-mako) ≠ task owner (codex-live). Independence check passes.

---

## Verdict

```
APPROVED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | script fails if requested model is not in the required models list | PASS | `validate_model()` checks against `REQUIRED_MODELS` from `local_assistant_health.py` before any I/O; `test_unknown_model_rejected` confirms exit 1 and no output file |
| 2 | output is written to the --output path, not only stdout | PASS | `output_path.write_text(response)` writes model output; JSON on stdout is only a path reference |
| 3 | a helper note is created in inbox/helpers/ with task_id, model, scope, output_path | PASS | `write_helper_note()` creates a timestamped `.md` file; test asserts all four fields present |
| 4 | a HELPER_INVOKED event is appended to events.jsonl | PASS | `append_event()` writes `type: HELPER_INVOKED`; test reads and asserts `task_id` and `output_path` in `artifact_paths` |
| 5 | script runs standalone: python3 MAP_System/scripts/local_runner.py --help | PASS | `argparse` parser works; `--help` prints usage cleanly |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Do not modify local_assistant_health.py or claims.py | NOT CHANGED — only imported from |
| Do not register Ollama models as core agents | NOT DONE — helper note explicitly states model has no task authority |
| Do not use --yes-always or headless invocation | NOT APPLICABLE here (Ollama, not Aider) |

---

## Files Reviewed

- `MAP_System/scripts/local_runner.py`
- `MAP_System/tests/test_local_runner.py`
- `MAP_System/artifacts/tests/local-runner-test.md`
- `MAP_System/tasks/TASK-048.json`

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/scripts/local_runner.py` | YES |
| `MAP_System/tests/test_local_runner.py` | YES |
| `MAP_System/scripts/run_tests.sh` | YES — test wiring |
| `MAP_System/artifacts/tests/local-runner-test.md` | YES |

All changes inside scope.

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| `validate_model` checks the static `REQUIRED_MODELS` list from the health script — if a model is allowed by the list but not actually installed, `check_health` catches it; dual-check is correct | NONE | By design |
| The `try/except ModuleNotFoundError` import pattern at the top works but is fragile — if either import fails for a different reason (syntax error, etc.) the real error is masked | LOW | Acceptable for now; could be replaced with explicit `sys.path` insertion |
| `subprocess.TimeoutExpired` is caught and re-raised as `LocalRunnerError`, but the base `OSError` (e.g., `ollama` not on PATH) is caught by the outer `except (LocalRunnerError, OSError)` in `main` — correct behavior | LOW | Acceptable |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| OPTIONAL | `local_runner.py:137` | `run()` | `if output_path is None: raise LocalRunnerError(...)` is unreachable — `--output` has `required=True` in argparse | Remove the dead guard in a cleanup pass |
| OPTIONAL | `local_runner.py:13` | import block | `try/except ModuleNotFoundError` dual-import could be replaced with a single `sys.path.insert(0, str(ROOT.parent))` before the import | Non-blocking |

No BLOCKER or REQUIRED findings.

---

## Notes

The execution order is correct: validate_model (static list check) → read_prompt → check_health (live Ollama check) → run_ollama → write output → write helper note → append event. Failing before any I/O on an unknown model is the right design. The helper note explicitly carries the disclaimer that the local model has no task authority, which is the key HPOM-003 invariant for local assistants. Tests don't require a live Ollama instance — subprocess and `build_report` are both mocked. Suite 11/11.
