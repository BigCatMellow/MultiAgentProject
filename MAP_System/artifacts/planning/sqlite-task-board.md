# SQLite Task Board Migration Design — TASK-003

**Author:** claude  
**Date:** 2026-06-18  
**Status:** Draft — awaiting review  
**Source references:** `general-purpose-multi-agent-project-system-v2.md §22`, `workflow/task_graph.json`, `shared/decisions.md`

---

## Overview

This document designs the SQLite storage layer that replaces the current file-backed task board. The goal is atomic task claims, queryable state, and durable event history without requiring a separate server. The file-backed layer (JSON, Markdown, JSONL) stays in place for human-readable project truth; SQLite becomes the runtime coordination layer.

---

## 1. File-to-Table Mapping

| Current file-backed state | Future SQLite table |
|---------------------------|---------------------|
| `tasks/TASK-NNN.json` (one file per task) | `tasks` |
| `workflow/task_graph.json` (task list + dependencies) | `tasks` + `task_dependencies` |
| `agents/status.json` (availability) | `agents` |
| `events/events.jsonl` (activity log) | `events` |
| `inbox/helpers/*.md` (helper notes) | `helpers` |
| `handoffs/HANDOFF-*.md` (structured handoffs) | `messages` |
| `artifacts/` directory (durable work products) | `artifacts` + `artifact_versions` |
| `shared/decisions.md` (decision log) | `decisions` |
| `shared/unresolved-questions.md` (open questions) | `decisions` (with `status = open`) |

File artifacts, reviews, and decisions remain human-readable in their directories. SQLite stores references and metadata, not the file content itself.

---

## 2. Schema

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ─── AGENTS ───────────────────────────────────────────────────────────────

CREATE TABLE agents (
    agent_id        TEXT PRIMARY KEY,          -- e.g. "codex", "claude", "antigravity"
    label           TEXT NOT NULL,             -- human-readable display name
    agent_type      TEXT NOT NULL DEFAULT 'core', -- "core" | "helper"
    helper_tag      TEXT,                      -- e.g. "helper-research-01" (null for core agents)
    status          TEXT NOT NULL DEFAULT 'available',
                                               -- "available" | "busy" | "standby" | "offline"
    reason          TEXT,                      -- reason for non-available status
    resume_after    TEXT,                      -- ISO-8601 or null
    last_heartbeat  TEXT,                      -- ISO-8601
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ─── TASKS ────────────────────────────────────────────────────────────────

CREATE TABLE tasks (
    task_id         TEXT PRIMARY KEY,           -- e.g. "TASK-001"
    project_id      TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    task_type       TEXT NOT NULL,              -- "implementation" | "review" | "architecture" | "maintenance"
    role            TEXT NOT NULL,              -- "implementer" | "reviewer" | "architect"
    status          TEXT NOT NULL DEFAULT 'BACKLOG',
                                                -- BACKLOG | READY | IN_PROGRESS | SUBMITTED | REVIEW
                                                -- | CHANGES_REQUESTED | BLOCKED | DONE
    priority        INTEGER NOT NULL DEFAULT 3, -- 1 (high) to 5 (low)
    required_agent  TEXT REFERENCES agents(agent_id),
    owner           TEXT REFERENCES agents(agent_id),
    claimed_by      TEXT REFERENCES agents(agent_id),
    lease_expires_at TEXT,                      -- ISO-8601; null when unclaimed
    heartbeat_at    TEXT,                       -- ISO-8601; updated by owner while working
    attempt         INTEGER NOT NULL DEFAULT 1,
    max_attempts    INTEGER NOT NULL DEFAULT 3,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE task_dependencies (
    task_id         TEXT NOT NULL REFERENCES tasks(task_id),
    depends_on      TEXT NOT NULL REFERENCES tasks(task_id),
    PRIMARY KEY (task_id, depends_on)
);

CREATE TABLE task_output_paths (
    task_id         TEXT NOT NULL REFERENCES tasks(task_id),
    path            TEXT NOT NULL,              -- relative to MAP_System/
    PRIMARY KEY (task_id, path)
);

CREATE TABLE task_acceptance_criteria (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT NOT NULL REFERENCES tasks(task_id),
    criterion       TEXT NOT NULL,
    met             INTEGER NOT NULL DEFAULT 0  -- 0 = pending, 1 = met
);

-- ─── HELPERS ──────────────────────────────────────────────────────────────

CREATE TABLE helpers (
    helper_id       TEXT PRIMARY KEY,           -- e.g. "helper-research-01"
    owner_agent_id  TEXT NOT NULL REFERENCES agents(agent_id),
    task_id         TEXT REFERENCES tasks(task_id),
    scope           TEXT NOT NULL,              -- what this helper was asked to do
    note_path       TEXT,                       -- path to inbox/helpers/ note file
    status          TEXT NOT NULL DEFAULT 'active', -- "active" | "stopped" | "stale"
    started_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    stopped_at      TEXT
);

-- ─── MESSAGES / HANDOFFS ──────────────────────────────────────────────────

CREATE TABLE messages (
    message_id      TEXT PRIMARY KEY,
    message_type    TEXT NOT NULL,              -- PROGRESS | QUESTION | ANSWER | BLOCKED |
                                                -- HANDOFF | SUBMISSION | REVIEW_REQUESTED |
                                                -- CHANGES_REQUESTED | APPROVED |
                                                -- DECISION_PROPOSED | DECISION_RECORDED
    task_id         TEXT REFERENCES tasks(task_id),
    sender_id       TEXT NOT NULL REFERENCES agents(agent_id),
    recipient_id    TEXT REFERENCES agents(agent_id), -- null = broadcast
    subject         TEXT,
    body            TEXT NOT NULL,
    handoff_path    TEXT,                       -- path to handoffs/ file, if applicable
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ─── ARTIFACTS ────────────────────────────────────────────────────────────

CREATE TABLE artifacts (
    artifact_id     TEXT PRIMARY KEY,
    task_id         TEXT REFERENCES tasks(task_id),
    artifact_type   TEXT NOT NULL,              -- "review" | "planning" | "code" | "test" | "draft" | "final"
    path            TEXT NOT NULL UNIQUE,       -- relative to MAP_System/artifacts/
    title           TEXT,
    created_by      TEXT REFERENCES agents(agent_id),
    status          TEXT NOT NULL DEFAULT 'draft', -- "draft" | "submitted" | "approved" | "superseded"
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE artifact_versions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id     TEXT NOT NULL REFERENCES artifacts(artifact_id),
    version         INTEGER NOT NULL DEFAULT 1,
    path            TEXT NOT NULL,              -- versioned copy path
    created_by      TEXT REFERENCES agents(agent_id),
    change_summary  TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE (artifact_id, version)
);

-- ─── REVIEWS ──────────────────────────────────────────────────────────────

CREATE TABLE reviews (
    review_id       TEXT PRIMARY KEY,
    task_id         TEXT NOT NULL REFERENCES tasks(task_id),
    artifact_id     TEXT REFERENCES artifacts(artifact_id),
    reviewer_id     TEXT NOT NULL REFERENCES agents(agent_id),
    verdict         TEXT,                       -- "APPROVED" | "CHANGES_REQUESTED" | null (pending)
    summary         TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    completed_at    TEXT
);

CREATE TABLE review_findings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id       TEXT NOT NULL REFERENCES reviews(review_id),
    severity        TEXT NOT NULL,              -- "BLOCKER" | "REQUIRED" | "RECOMMENDED" | "OPTIONAL"
    area            TEXT,
    description     TEXT NOT NULL
);

-- ─── DECISIONS ────────────────────────────────────────────────────────────

CREATE TABLE decisions (
    decision_id     TEXT PRIMARY KEY,           -- e.g. "DEC-001"
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'open', -- "open" | "proposed" | "approved" | "superseded"
    proposed_by     TEXT REFERENCES agents(agent_id),
    task_id         TEXT REFERENCES tasks(task_id),
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    resolved_at     TEXT
);

-- ─── EVENTS ───────────────────────────────────────────────────────────────

CREATE TABLE events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type      TEXT NOT NULL,              -- mirrors AGENTS.md message types
    task_id         TEXT REFERENCES tasks(task_id),
    sender_id       TEXT REFERENCES agents(agent_id),
    summary         TEXT NOT NULL,
    artifact_paths  TEXT,                       -- JSON array of strings
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ─── APPROVAL GATES ───────────────────────────────────────────────────────

CREATE TABLE approval_gates (
    gate_id         TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    required_after_task TEXT REFERENCES tasks(task_id),
    status          TEXT NOT NULL DEFAULT 'pending', -- "pending" | "approved" | "rejected"
    approved_by     TEXT,                       -- human operator or agent id
    approved_at     TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE approval_gate_resume_tasks (
    gate_id         TEXT NOT NULL REFERENCES approval_gates(gate_id),
    task_id         TEXT NOT NULL REFERENCES tasks(task_id),
    PRIMARY KEY (gate_id, task_id)
);

-- ─── INDEXES ──────────────────────────────────────────────────────────────

CREATE INDEX idx_tasks_status          ON tasks(status);
CREATE INDEX idx_tasks_owner           ON tasks(owner);
CREATE INDEX idx_tasks_lease_expires   ON tasks(lease_expires_at);
CREATE INDEX idx_events_task_id        ON events(task_id);
CREATE INDEX idx_events_created_at     ON events(created_at);
CREATE INDEX idx_messages_recipient    ON messages(recipient_id);
CREATE INDEX idx_artifacts_task_id     ON artifacts(task_id);
CREATE INDEX idx_helpers_status        ON helpers(status);
```

---

## 3. Atomic Task Claims

### Problem

The current file-backed system has no atomic claim mechanism. Two agents could read a task as `READY`, both decide to claim it, and both begin work simultaneously. This is tolerable at bootstrap scale with one active agent, but breaks when multiple agents run concurrently.

### Solution: SQLite `UPDATE ... WHERE` with implicit row lock

SQLite serializes writes. A claim is a single `UPDATE` statement that succeeds only when the task is still unclaimed:

```sql
UPDATE tasks
SET
    status          = 'IN_PROGRESS',
    claimed_by      = :agent_id,
    lease_expires_at = datetime('now', '+30 minutes'),
    heartbeat_at    = datetime('now'),
    attempt         = attempt + 1,
    updated_at      = datetime('now')
WHERE
    task_id         = :task_id
    AND (status = 'READY' OR (status = 'IN_PROGRESS' AND lease_expires_at < datetime('now')))
    AND attempt < max_attempts;
```

The agent then checks `sqlite3_changes()` (or the Python equivalent `cursor.rowcount`). If it returns `0`, the claim failed — another agent got there first or the task exceeded its retry limit.

### Lease renewal (heartbeat)

While working, the owner sends a heartbeat every N seconds:

```sql
UPDATE tasks
SET heartbeat_at    = datetime('now'),
    lease_expires_at = datetime('now', '+30 minutes'),
    updated_at      = datetime('now')
WHERE task_id = :task_id AND claimed_by = :agent_id;
```

### Lease expiration (reconciliation)

The LangGraph runner (or a periodic reconciler) releases expired leases:

```sql
UPDATE tasks
SET
    status           = 'READY',
    claimed_by       = NULL,
    lease_expires_at = NULL,
    heartbeat_at     = NULL,
    updated_at       = datetime('now')
WHERE
    status           = 'IN_PROGRESS'
    AND lease_expires_at < datetime('now')
    AND claimed_by IS NOT NULL;
```

This matches the `task_lease_seconds: 1800` value in `workflow/runtime_policy.yaml`.

### Releasing a task normally

```sql
UPDATE tasks
SET
    status           = 'SUBMITTED',
    lease_expires_at = NULL,
    heartbeat_at     = NULL,
    updated_at       = datetime('now')
WHERE task_id = :task_id AND claimed_by = :agent_id;
```

---

## 4. Migration Path from File-Backed to SQLite

### Phase 0 (current) — file-backed only

All state lives in JSON, Markdown, and JSONL files. The LangGraph runner reads these files and routes read-only. Claims are manual and enforced by convention.

### Phase 1 — SQLite as shadow log (no behavior change)

- Run `migration/seed_from_files.py` to populate SQLite from current file state.
- LangGraph runner writes events to SQLite in addition to `events.jsonl`.
- No agent reads from SQLite yet. SQLite is a queryable audit trail only.

### Phase 2 — SQLite as the claim coordinator

- Agents perform claims through SQLite instead of manually editing task JSON files.
- File-backed task JSON continues to exist but is regenerated from SQLite on each runner cycle.
- Lease expiration and reconciliation run in the LangGraph runner.

### Phase 3 — SQLite as the canonical source

- Task JSON files become generated exports for human readability and Git history.
- `events.jsonl` becomes a generated export from the `events` table.
- `shared/decisions.md` becomes a generated export from the `decisions` table.
- File-backed inboxes and handoff notes may stay human-authored but are indexed in SQLite.

---

## 5. Migration Seed Script (outline)

`MAP_System/migration/seed_from_files.py` should:

1. Open (or create) `MAP_System/map.db`.
2. Run the schema DDL from this document.
3. Load `workflow/task_graph.json` → insert rows into `tasks`, `task_dependencies`, `task_output_paths`, `task_acceptance_criteria`.
4. Load `agents/status.json` → insert rows into `agents`.
5. Load `events/events.jsonl` line by line → insert rows into `events`.
6. Load `shared/decisions.md` → parse `## DEC-NNN` sections → insert into `decisions`.
7. Scan `artifacts/` for `.md` files → insert stubs into `artifacts`.
8. Run in idempotent mode: `INSERT OR IGNORE` for all rows to allow re-seeding.

---

## 6. Open Questions (from `shared/unresolved-questions.md`)

| Question | Recommended answer |
|----------|--------------------|
| Should the next version use SQLite for atomic claims and leases? | **Yes** — this document is the design. Phase 1 can start when Codex resumes. |
| Should Codex and Claude use separate branches/worktrees once Git is initialized? | Separate worktrees preferred for parallel work; one branch per task is a reasonable convention. |
| What model/provider should the future LangGraph runtime call for each role? | Default to `claude-sonnet-4-6` for implementation and review; use `claude-haiku-4-5` for routing and classification. Revisit when costs are measured. |
| Should the first real workflow target writing, software, research, or general project management? | General project management (this workspace itself) is already the first workflow. Keep it and add a second template only when the runtime is stable. |

These should be moved to `shared/decisions.md` as proposed decisions for operator approval.

---

## 7. Acceptance Criteria Check

| Criterion | Met? |
|-----------|------|
| Defines tables for agents, tasks, claims, messages, artifacts, reviews, decisions, and events | Yes — see Section 2 |
| Explains atomic task claims and lease expiration | Yes — see Section 3 |
| Maps current file-backed state to future SQLite tables | Yes — see Section 1 and Section 4 |
