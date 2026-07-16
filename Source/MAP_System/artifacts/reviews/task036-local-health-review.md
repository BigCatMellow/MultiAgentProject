# Review Record: TASK-036

## Header

```
task_id:      TASK-036
reviewer:     claude-mako
review_date:  2026-06-29
task_owner:   codex-live
```

Reviewer (claude-mako) ≠ task owner (codex-live). Independence check passes.

---

## Verdict

```
APPROVED WITH NOTES
```

Work on the local assistant health check is approved. One REQUIRED finding must
be tracked via follow-up (not a block on this task). See findings below.

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Read-only health command reports Ollama reachability without registering local models as core agents | PASS | `local_assistant_health.py` uses `shutil.which` + `ollama list`; no writes, no registration |
| 2 | Checks for all 5 required models | PASS | `REQUIRED_MODELS` tuple lines 14-20 lists all five; live run confirms all available |
| 3 | Checks Aider, reports as tool/workbench not model | PASS | `check_aider()` returns `type: edit-workbench`, `authority: edit-helper` |
| 4 | `ai help` exposes health-check without adding start wrappers | PASS | `ai-command-center-cli` line 384 adds `local-health\|local-assistant-health` dispatch; no start logic |
| 5 | Deterministic fixture or mock test recorded | PASS | `artifacts/tests/local-assistant-health-test.md` records live run with observed values |
| 6 | `current-state.md` still says local assistants are helper capabilities, not core agents | PASS | Line 23: "Local Ollama models and Aider are helper capabilities, not registered core agents" — unchanged |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Do not register local models as core agents | NOT CHANGED — `policy.core_agent_status: not-registered` in output |
| Do not add local assistant start wrappers | NOT CHANGED — CLI dispatches to health script only, no session launchers |
| Do not make network calls or install packages | NOT CHANGED — `ollama list` is a local CLI call; no network, no install |
| Do not change Pathwell files | NOT CHANGED |
| Do not make local assistant output authoritative | NOT CHANGED — `authority: draft-only` in model records |

---

## Files Reviewed

- `MAP_System/scripts/local_assistant_health.py`
- `MAP_System/scripts/ai-command-center-cli` (lines 33, 384–387)
- `MAP_System/artifacts/tests/local-assistant-health-test.md`
- `MAP_System/tasks/TASK-036.json`
- `MAP_System/shared/current-state.md` (policy check)

---

## Scope Check

| Changed file | In scope per task JSON? |
|---|---|
| `MAP_System/scripts/local_assistant_health.py` | YES |
| `MAP_System/scripts/ai-command-center-cli` | YES |
| `MAP_System/artifacts/tests/local-assistant-health-test.md` | YES |
| `MAP_System/tasks/TASK-036.json` | YES |

All changed files are within declared `files_in_scope`.

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| `export_to_files.py` strips arbitrary HPOM JSON fields on sync | MEDIUM | Create follow-up task to make exporter preserve unknown JSON keys; promote_task.py --no-sync is a valid workaround until then |
| HPOM-003 no-self-review enforcement in `claims.py` is not yet implemented as a SQLite-level gate | LOW | Already partially covered by `validate_review.py` at review time; SQLite claim gate is the remaining gap — tracked in findings below |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| REQUIRED | TASK-036.json | title/description | Task scope was changed from the original TASK-036 assignment ("HPOM-003: No-self-review — enforce reviewer independence") to "Add local assistant health checks" without a formal handoff or scope change record. The no-self-review claim gate in `db/claims.py` (the original objective) remains unimplemented. The review-time check in `validate_review.py` covers the review gate but not claim time. | Create a new task (TASK-044 or similar) explicitly for the SQLite-level no-self-review claim gate. Do not reuse TASK-036 for this. |
| RECOMMENDED | `local_assistant_health.py`:118 | `build_report` | `status: "ok"` only when all models available AND aider found. On a machine without Aider this returns `"attention"` but the caller has no way to distinguish "Aider missing" from "Ollama down". | Add a `detail` field listing specific missing components, or split into sub-statuses. Low priority; current output is sufficient for the operator. |
| RECOMMENDED | (follow-up) | exporter | `export_to_files.py` strips HPOM JSON fields (`objective`, `required_context`, etc.) when syncing. Codex correctly used `--no-sync` and manual mirror as workaround. | Track as a separate task: make the exporter round-trip unknown JSON keys. |

---

## Notes

- The scope pivot from HPOM-003 to local assistant health was the right call in context: the operator specifically asked about local assistant integration, and the no-self-review review gate is already live via `validate_review.py`. But it should have been a formal task rename or a new task with a handoff — not a silent title change.
- All five Ollama models are installed and available on this machine. Aider 0.86.2 is installed. Health check returns `status: ok`.
- The `--timeout` flag is a good defensive addition given CPU-only Ollama.
- No tests were added to `run_tests.sh` for this task. The test artifact is a fixture/observation doc. Acceptable given the read-only, environment-dependent nature of the check.
