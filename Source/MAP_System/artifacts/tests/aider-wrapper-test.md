# TASK-049 Aider Wrapper Test

Date: 2026-06-29
Owner: codex-live

## Scope

Verified supervised Aider setup wrapper behavior without launching a real Aider session.

## Commands

```bash
python3 MAP_System/tests/test_aider_wrapper.py
python3 MAP_System/scripts/aider_wrapper.py --help
python3 -m py_compile MAP_System/scripts/aider_wrapper.py MAP_System/tests/test_aider_wrapper.py
MAP_System/scripts/run_tests.sh
```

## Results

- Out-of-scope target files are rejected before helper notes/events.
- Dirty target files are rejected before helper notes/events.
- Helper note and `HELPER_INVOKED` event are created before interactive launch.
- Aider launch is interactive via `subprocess.call`; tests assert no `--yes-always`.
- Forbidden automation flags are rejected.
- Full MAP test wrapper passed with `SUMMARY pass=12 fail=0 total=12`.
