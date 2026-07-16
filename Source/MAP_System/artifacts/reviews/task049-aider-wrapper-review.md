# Review Record: TASK-049

## Header

```
task_id:      TASK-049
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
| 1 | script fails if git working tree has uncommitted changes to the target files | PASS | `dirty_target_files()` runs `git status --porcelain -- <targets>`; raises `AiderWrapperError` if any line returned; `test_dirty_target_fails_before_note` confirms exit 1 and no helper note created |
| 2 | script fails if any target file is outside the task output_paths in TASK-NNN.json | PASS | `validate_targets()` calls `path_in_scope()` per target; checks prefix match against all `output_paths`; `test_out_of_scope_target_fails` confirms exit 1 and no event written |
| 3 | helper note created in inbox/helpers/ before Aider launches | PASS | `write_helper_note()` is called before `launch_aider()` in `run()`; if note write fails, Aider never starts; test asserts note file and content present |
| 4 | Aider is launched interactively (no --yes-always or headless flags) | PASS | `subprocess.call()` inherits the operator's terminal (stdin/stdout/stderr unredirected); `validate_aider_args()` blocks `--yes-always`, `--yes`, `--auto-commits`; test asserts `--yes-always` not in the Aider command |
| 5 | script runs standalone: python3 MAP_System/scripts/aider_wrapper.py --help | PASS | argparse parser works; `--` separator for Aider pass-through args is documented in help |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Do not run Aider with --yes-always | NOT DONE — `validate_aider_args()` blocks it and `test_forbidden_aider_flag_fails` verifies |
| Do not auto-apply changes | NOT DONE — `subprocess.call()` is interactive; operator controls accept/reject |
| Do not modify local_runner.py | NOT CHANGED |

---

## Files Reviewed

- `MAP_System/scripts/aider_wrapper.py`
- `MAP_System/tests/test_aider_wrapper.py`
- `MAP_System/artifacts/tests/aider-wrapper-test.md`
- `MAP_System/tasks/TASK-049.json`

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/scripts/aider_wrapper.py` | YES |
| `MAP_System/tests/test_aider_wrapper.py` | YES |
| `MAP_System/scripts/run_tests.sh` | YES — test wiring |
| `MAP_System/artifacts/tests/aider-wrapper-test.md` | YES |

All changes inside scope.

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| `path_in_scope()` compares normalized relative paths — if an absolute path is passed as `--target`, it won't match any relative `output_paths` and will be blocked | LOW | Correct conservative behavior; document that `--target` expects relative paths |
| `subprocess.call()` returns Aider's exit code directly — if Aider exits non-zero (user abort, error), `main()` returns non-zero; callers should not treat non-zero as a wrapper error | LOW | Acceptable; the distinction between wrapper failure and Aider exit is meaningful for the caller |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| RECOMMENDED | `aider_wrapper.py:19` | `FORBIDDEN_AIDER_FLAGS` | `--no-auto-commits` is in the blocked set, but it is a *safety* flag that prevents Aider from auto-committing — blocking it prevents the operator from adding an extra guard. Only `--auto-commits` is dangerous here. | Remove `--no-auto-commits` from `FORBIDDEN_AIDER_FLAGS`; keep `--auto-commits` blocked |
| OPTIONAL | `aider_wrapper.py:144` | `split_wrapper_and_aider_args` | `argv = sys.argv[1:]` when `argv is None` means the function mutates a local that shadows the parameter — works correctly but the pattern is slightly confusing; could use `argv if argv is not None else sys.argv[1:]` inline | Cosmetic |

No BLOCKER or REQUIRED findings.

---

## Notes

The `subprocess.call()` choice for Aider is exactly right — it gives the operator full terminal control, unlike `subprocess.run(capture_output=True)` which would swallow the session. The `--` separator for pass-through args is clean and familiar to CLI users. The `--dry-run` flag makes testing and pre-flight checks possible without needing a live Aider installation. The `dirty_target_files` check before helper note creation is the correct order — fail before creating any artifacts if the git state is wrong. Suite 12/12.
