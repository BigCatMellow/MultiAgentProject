# map-status Test

Task: TASK-029  
Tester: codex  
Date: 2026-06-19

## Commands

```bash
python3 -m py_compile MAP_System/scripts/map_status.py
python3 MAP_System/scripts/map_status.py
```

Temp fixture:

```bash
python3 - <<'PY'
import sqlite3, subprocess, sys, tempfile
from pathlib import Path
schema = Path('MAP_System/migration/schema.sql').read_text(encoding='utf-8')
with tempfile.TemporaryDirectory() as td:
    db = Path(td) / 'status.db'
    conn = sqlite3.connect(db)
    conn.executescript(schema)
    conn.executemany("INSERT INTO agents (agent_id,label,agent_type,status,reason,resume_after,last_heartbeat) VALUES (?,?,?,?,?,?,?)", [
        ('codex','Codex','core','available',None,None,'2026-06-19T10:00:00Z'),
        ('claude','Claude','core','busy','reviewing','soon',None),
    ])
    conn.executemany("INSERT INTO tasks (task_id,project_id,title,description,task_type,role,status,owner,claimed_by,lease_expires_at,heartbeat_at,attempt,max_attempts) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", [
        ('T-1','P','Claimed','', 'implementation','implementer','IN_PROGRESS','codex','codex','2030-01-01T00:00:00Z','2026-06-19T10:00:00Z',2,3),
        ('T-2','P','Submitted','', 'review','reviewer','SUBMITTED','claude',None,None,None,1,3),
    ])
    conn.execute("INSERT INTO approval_gates (gate_id,name,required_after_task,status) VALUES (?,?,?,?)", ('G-1','Gate','T-2','pending'))
    conn.commit(); conn.close()
    result = subprocess.run([sys.executable, 'MAP_System/scripts/map_status.py', '--db', str(db)], text=True, capture_output=True)
    assert result.returncode == 0
    for text in ['IN_PROGRESS claims', 'T-1', 'SUBMITTED awaiting review', 'T-2', 'Pending approval gates', 'G-1', 'Agent statuses', 'claude']:
        assert text in result.stdout, text
PY
```

## Results

- Real `map.db` run exits `0` and shows current TASK-029 claim.
- Temp fixture covers `IN_PROGRESS`, `SUBMITTED`, pending gate, and agent status sections.
- No project DB/files mutated by fixture.
