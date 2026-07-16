#!/usr/bin/env python3
"""Minimal SQLite checkpointer for LangGraph, backed by MAP_System/map.db."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_checkpoint_id,
)

DEFAULT_DB = Path(__file__).resolve().parents[1] / "map.db"


DDL = """
CREATE TABLE IF NOT EXISTS lg_checkpoints (
    thread_id   TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    checkpoint  TEXT NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
CREATE TABLE IF NOT EXISTS lg_checkpoint_writes (
    thread_id     TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id       TEXT NOT NULL,
    task_path     TEXT NOT NULL DEFAULT '',
    idx           INTEGER NOT NULL,
    channel       TEXT NOT NULL,
    type          TEXT,
    value         TEXT,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
"""


def _config_ids(config: RunnableConfig) -> tuple[str, str, str | None]:
    cfg = config.get("configurable", {})
    thread_id = str(cfg.get("thread_id", "default"))
    ns = str(cfg.get("checkpoint_ns", ""))
    checkpoint_id = cfg.get("checkpoint_id") or cfg.get("thread_ts")
    return thread_id, ns, checkpoint_id


class MapSqliteSaver(BaseCheckpointSaver):
    """LangGraph checkpointer backed by the existing map.db SQLite database."""

    def __init__(self, db_path: str | Path = DEFAULT_DB) -> None:
        super().__init__()
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(DDL)

    # ── required sync interface ───────────────────────────────────────────────

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        thread_id, ns, checkpoint_id = _config_ids(config)
        with self._connect() as conn:
            if checkpoint_id:
                row = conn.execute(
                    """
                    SELECT checkpoint_id, parent_checkpoint_id, checkpoint, metadata
                    FROM lg_checkpoints
                    WHERE thread_id=? AND checkpoint_ns=? AND checkpoint_id=?
                    """,
                    (thread_id, ns, checkpoint_id),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT checkpoint_id, parent_checkpoint_id, checkpoint, metadata
                    FROM lg_checkpoints
                    WHERE thread_id=? AND checkpoint_ns=?
                    ORDER BY created_at DESC, checkpoint_id DESC
                    LIMIT 1
                    """,
                    (thread_id, ns),
                ).fetchone()
            if row is None:
                return None
            writes = conn.execute(
                """
                SELECT task_id, task_path, idx, channel, type, value
                FROM lg_checkpoint_writes
                WHERE thread_id=? AND checkpoint_ns=? AND checkpoint_id=?
                ORDER BY task_id, idx
                """,
                (thread_id, ns, row["checkpoint_id"]),
            ).fetchall()

        checkpoint: Checkpoint = json.loads(row["checkpoint"])
        metadata: CheckpointMetadata = json.loads(row["metadata"])
        parent_config: RunnableConfig | None = (
            {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": ns,
                    "checkpoint_id": row["parent_checkpoint_id"],
                }
            }
            if row["parent_checkpoint_id"]
            else None
        )
        pending_writes = [
            (w["task_id"], w["channel"], self.serde.loads_typed((w["type"], w["value"])))
            for w in writes
        ]
        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": ns,
                    "checkpoint_id": row["checkpoint_id"],
                }
            },
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=parent_config,
            pending_writes=pending_writes or None,
        )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Any,
    ) -> RunnableConfig:
        thread_id, ns, _ = _config_ids(config)
        checkpoint_id = checkpoint["id"]
        parent_id = get_checkpoint_id(config)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lg_checkpoints
                    (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id,
                     checkpoint, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    ns,
                    checkpoint_id,
                    parent_id,
                    json.dumps(checkpoint),
                    json.dumps(metadata),
                ),
            )
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: list[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id, ns, checkpoint_id = _config_ids(config)
        if not checkpoint_id:
            return
        with self._connect() as conn:
            for idx, (channel, value) in enumerate(writes):
                type_, serialized = self.serde.dumps_typed(value)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO lg_checkpoint_writes
                        (thread_id, checkpoint_ns, checkpoint_id, task_id, task_path,
                         idx, channel, type, value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, ns, checkpoint_id, task_id, task_path,
                     idx, channel, type_, serialized),
                )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        thread_id = (config or {}).get("configurable", {}).get("thread_id", "default")
        ns = (config or {}).get("configurable", {}).get("checkpoint_ns", "")
        query = """
            SELECT checkpoint_id, parent_checkpoint_id, checkpoint, metadata
            FROM lg_checkpoints
            WHERE thread_id=? AND checkpoint_ns=?
            ORDER BY created_at DESC, checkpoint_id DESC
        """
        params: list[Any] = [thread_id, ns]
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        for row in rows:
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": ns,
                        "checkpoint_id": row["checkpoint_id"],
                    }
                },
                checkpoint=json.loads(row["checkpoint"]),
                metadata=json.loads(row["metadata"]),
                parent_config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": ns,
                        "checkpoint_id": row["parent_checkpoint_id"],
                    }
                }
                if row["parent_checkpoint_id"]
                else None,
                pending_writes=None,
            )
