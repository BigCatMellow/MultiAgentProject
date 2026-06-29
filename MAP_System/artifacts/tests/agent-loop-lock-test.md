# Agent Loop Lock Test

Task: TASK-024  
Tester: codex  
Date: 2026-06-19

## Commands

```bash
python3 -m py_compile MAP_System/scripts/agent_loop.py
MAP_System/.venv/bin/python -c "from pathlib import Path; from MAP_System.scripts.agent_loop import Config, acquire_loop_lock, release_loop_lock; c=Config('codex-lock-test', Path('MAP_System/map.db'), True, True, None, 300, 1800, True, 1, 300); lock=acquire_loop_lock(c); print(lock.path, flush=True); ..."
MAP_System/.venv/bin/python MAP_System/scripts/agent_loop.py --once --dry-run --agent-id codex-lock-test --db MAP_System/map.db
MAP_System/.venv/bin/python -c "from pathlib import Path; from MAP_System.scripts.agent_loop import Config, lock_path_for; p=lock_path_for('codex-lock-test', Path('MAP_System/map.db')); p.write_text('999999\nagent_id=codex-lock-test\ndb_path=MAP_System/map.db\n', encoding='utf-8')"
MAP_System/.venv/bin/python MAP_System/scripts/agent_loop.py --once --dry-run --agent-id codex-lock-test --db MAP_System/map.db
```

## Results

### Live Lock Rejection

With a first process holding the lock for `agent_id=codex-lock-test` and `MAP_System/map.db`, a second loop start failed:

```text
error: agent_loop already running for agent_id=codex-lock-test db=MAP_System/map.db pid=2 lock=/home/home/Downloads/MultiAgentProject/MAP_System/.locks/agent_loop/codex-lock-test-4beb1db9fc5025d9.lock
```

Exit code: `2`.

### Stale Lock Cleanup

After replacing the lock content with dead PID `999999`, startup removed the stale lock and continued:

```text
removed stale lock path=/home/home/Downloads/MultiAgentProject/MAP_System/.locks/agent_loop/codex-lock-test-4beb1db9fc5025d9.lock
reconciled=none
route=review
{"interrupted":true,"message":"operator input required for route=review"}
```

### Clean Exit Release

After normal `--once --dry-run` exit:

```text
False /home/home/Downloads/MultiAgentProject/MAP_System/.locks/agent_loop/codex-lock-test-4beb1db9fc5025d9.lock
```

The lockfile was removed.
