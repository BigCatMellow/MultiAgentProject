#!/usr/bin/env python3
"""Durable checkpoint/resume helpers (TASK-161, from map-resilience-controls-spec.md).

Records a durable checkpoint after each meaningful step boundary
(claim/handler/submit/event/export) so a killed process can resume from the
last completed step instead of re-running from scratch or silently
double-applying a partial retry. Append-only JSONL store, mirroring the
shape of dead_letter_queue.py and liveness_reaper.py's dead-letter log.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKPOINT_LOG = ROOT / "shared" / "durable-checkpoints.jsonl"

# Ordered so resume_step() can tell what comes next; a task's real steps are
# a subset/superset of these in practice, but this is the canonical
# vocabulary named in the spec ("claim/handler/submit/event/export
# boundaries").
STEP_ORDER = ("claim", "handler", "submit", "event", "export")


class DurableExecutionError(RuntimeError):
    """Raised on an out-of-order or duplicate checkpoint that would double-apply a step."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_checkpoints(log: Path) -> list[dict]:
    if not log.exists():
        return []
    return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]


def get_last_checkpoint(task_id: str, log: Path = DEFAULT_CHECKPOINT_LOG) -> dict | None:
    matches = [r for r in _read_checkpoints(log) if r["task_id"] == task_id]
    return matches[-1] if matches else None


def record_checkpoint(
    task_id: str,
    step: str,
    *,
    idempotency_key: str | None = None,
    detail: str = "",
    log: Path = DEFAULT_CHECKPOINT_LOG,
) -> dict:
    """Records that `step` completed for `task_id`. Enforces monotonic step
    order: recording a step at or before the latest recorded step's
    STEP_ORDER position is rejected, not just an exact repeat. Without
    this, a resumed/retried process could regress from a later completed
    boundary (e.g. 'handler') back to an earlier one (e.g. 'claim'),
    which would replay an already-completed write boundary -- caught by
    TASK-161's review as a real defect (isolated probe: claim -> handler
    -> claim was incorrectly accepted before this fix).
    """
    if step not in STEP_ORDER:
        raise DurableExecutionError(f"unknown step: {step} (must be one of {STEP_ORDER})")

    last = get_last_checkpoint(task_id, log)
    if last is not None:
        try:
            last_idx = STEP_ORDER.index(last["step"])
        except ValueError:
            raise DurableExecutionError(f"checkpoint log has unknown step: {last['step']}")
        new_idx = STEP_ORDER.index(step)
        if new_idx <= last_idx:
            raise DurableExecutionError(
                f"step '{step}' (position {new_idx}) is not after the latest recorded "
                f"step '{last['step']}' (position {last_idx}) for {task_id} -- "
                f"checkpoint {last['checkpoint_id']} already covers this or a later "
                "boundary; resume_step() should be used instead of regressing"
            )

    checkpoint_id = f"CKPT-{task_id}-{step}-{len(_read_checkpoints(log))}"
    record = {
        "checkpoint_id": checkpoint_id,
        "task_id": task_id,
        "step": step,
        "idempotency_key": idempotency_key,
        "detail": detail,
        "recorded_at": _now_iso(),
    }
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def resume_step(task_id: str, log: Path = DEFAULT_CHECKPOINT_LOG) -> str:
    """Returns the next step a resumed process should perform: the step
    immediately after the last recorded checkpoint, or the first step if
    nothing was ever checkpointed. This is the direct fix for "killed
    handler mid-task" and "mid-task resume" -- a resumed process asks this
    function what to do next instead of restarting from step 1 or
    guessing.
    """
    last = get_last_checkpoint(task_id, log)
    if last is None:
        return STEP_ORDER[0]
    try:
        idx = STEP_ORDER.index(last["step"])
    except ValueError:
        raise DurableExecutionError(f"checkpoint log has unknown step: {last['step']}")
    if idx + 1 >= len(STEP_ORDER):
        return "complete"
    return STEP_ORDER[idx + 1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    record_cmd = sub.add_parser("record")
    record_cmd.add_argument("task_id")
    record_cmd.add_argument("step", choices=STEP_ORDER)
    record_cmd.add_argument("--detail", default="")

    resume_cmd = sub.add_parser("resume")
    resume_cmd.add_argument("task_id")

    args = parser.parse_args()
    if args.command == "record":
        print(record_checkpoint(args.task_id, args.step, detail=args.detail))
    else:
        print(resume_step(args.task_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
