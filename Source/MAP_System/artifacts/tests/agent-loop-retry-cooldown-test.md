# Agent Loop Retry Cooldown Test

Task: TASK-032  
Tester: codex  
Date: 2026-06-23

## Commands

```bash
python3 -m py_compile MAP_System/scripts/agent_loop.py
MAP_System/scripts/run_tests.sh
```

Temp DB fixtures also exercised:

```bash
agent_loop.py --handler false --max-iterations 2 --retry-cooldown 60
agent_loop.py --handler false --max-iterations 2 --retry-cooldown 0
```

## Results

With `--retry-cooldown 60`, the failing task was claimed once, released to `READY`, and skipped on the next poll:

```text
claimed task_id=TASK-FAIL
released task_id=TASK-FAIL status=READY reason=CalledProcessError retry_cooldown=60
retry_cooldown task_id=TASK-FAIL remaining_seconds=59
ROW ('READY', None, 1)
```

With `--retry-cooldown 0`, cooldown was disabled and the same task was reclaimed on the next cycle:

```text
claimed task_id=TASK-FAIL
released task_id=TASK-FAIL status=READY reason=CalledProcessError
claimed task_id=TASK-FAIL
released task_id=TASK-FAIL status=READY reason=CalledProcessError
ROW ('READY', None, 2)
```

Full runner:

```text
SUMMARY pass=3 fail=0 total=3
```
