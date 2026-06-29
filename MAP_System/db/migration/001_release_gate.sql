-- HPOM-006 release gate: APPROVED review and RELEASED integration are distinct.
-- SQLite does not constrain task.status to an enum, so RELEASED is introduced
-- by the release path and backed by a required checklist completion record.

CREATE TABLE IF NOT EXISTS task_release_records (
    task_id         TEXT PRIMARY KEY REFERENCES tasks(task_id),
    checklist_path  TEXT NOT NULL,
    released_by     TEXT NOT NULL REFERENCES agents(agent_id),
    summary         TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
