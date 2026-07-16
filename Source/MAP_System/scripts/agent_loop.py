#!/usr/bin/env python3
"""LangGraph-driven autonomous task claim loop."""

from __future__ import annotations

import argparse
import atexit
import errno
import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
if VENV_PYTHON.exists() and Path(sys.executable) != VENV_PYTHON:
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])

from langgraph.graph import END, START, StateGraph  # noqa: E402
from langgraph.types import Command, interrupt  # noqa: E402

sys.path.insert(0, str(ROOT))

from db.checkpointer import MapSqliteSaver  # noqa: E402
from db.claims import DEFAULT_DB, claim_task_with_reason, heartbeat, release_task, submit_task  # noqa: E402
from db.claims import expire_leases  # noqa: E402


RUNNER = ROOT / "graph" / "runner.py"
EXPORTER = ROOT / "migration" / "export_to_files.py"
PYTHON = VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)
LOCK_DIR = ROOT / ".locks" / "agent_loop"


class LeaseRevoked(RuntimeError):
    pass


class LockHeld(RuntimeError):
    pass


@dataclass
class Config:
    agent_id: str
    db_path: Path
    once: bool
    dry_run: bool
    handler: str | None
    heartbeat_interval: float
    lease_seconds: int
    export_after_submit: bool
    max_iterations: int
    retry_cooldown: int
    resume: bool = False


@dataclass
class LoopLock:
    path: Path
    fd: int


class LoopState(TypedDict, total=False):
    agent_id: str
    db_path: str
    route: str
    ready_tasks: list[str]
    current_task: str | None
    current_task_id: str | None
    last_result: str
    last_route: str
    iterations: int
    attempt_count: int
    expired_task_ids: list[str]
    retry_cooldowns: dict[str, float]
    events: list[str]


class Shutdown:
    requested = False


SHUTDOWN = Shutdown()


def request_shutdown(_signum: int, _frame: object) -> None:
    SHUTDOWN.requested = True


def lock_path_for(agent_id: str, db_path: Path) -> Path:
    resolved_db = str(db_path.expanduser().resolve())
    safe_agent = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in agent_id)
    db_key = hashlib.sha256(resolved_db.encode("utf-8")).hexdigest()[:16]
    return LOCK_DIR / f"{safe_agent}-{db_key}.lock"


def pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_lock_pid(path: Path) -> int | None:
    try:
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
    except (FileNotFoundError, IndexError):
        return None
    try:
        return int(first_line)
    except ValueError:
        return None


def acquire_loop_lock(config: Config) -> LoopLock:
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    path = lock_path_for(config.agent_id, config.db_path)
    payload = (
        f"{os.getpid()}\n"
        f"agent_id={config.agent_id}\n"
        f"db_path={config.db_path.expanduser().resolve()}\n"
    ).encode("utf-8")

    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            pid = read_lock_pid(path)
            if pid and pid_is_running(pid):
                raise LockHeld(
                    f"agent_loop already running for agent_id={config.agent_id} "
                    f"db={config.db_path} pid={pid} lock={path}"
                )
            try:
                path.unlink()
                print(f"removed stale lock path={path}")
            except FileNotFoundError:
                pass
            except OSError as exc:
                if exc.errno != errno.ENOENT:
                    raise
            continue
        os.write(fd, payload)
        os.fsync(fd)
        return LoopLock(path=path, fd=fd)


def release_loop_lock(lock: LoopLock | None) -> None:
    if lock is None:
        return
    try:
        os.close(lock.fd)
    except OSError:
        pass
    try:
        if read_lock_pid(lock.path) == os.getpid():
            lock.path.unlink()
    except FileNotFoundError:
        pass


def run_runner(db_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [str(PYTHON), str(RUNNER), "--db", str(db_path)],
        cwd=ROOT.parent,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def run_export(db_path: Path) -> None:
    subprocess.run(
        [str(PYTHON), str(EXPORTER), "--db", str(db_path)],
        cwd=ROOT.parent,
        check=True,
    )


def run_handler(task_id: str, config: Config) -> None:
    if config.dry_run:
        print(f"dry_run: handler skipped for {task_id}")
        return
    if not config.handler:
        raise RuntimeError("handler is required unless --dry-run is set")
    process = subprocess.Popen(config.handler.format(task_id=task_id), shell=True, cwd=ROOT.parent)
    while process.poll() is None:
        if SHUTDOWN.requested:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise KeyboardInterrupt(f"shutdown requested while handling {task_id}")
        time.sleep(0.1)
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, config.handler.format(task_id=task_id))


def heartbeat_until_done(task_id: str, config: Config, done: threading.Event) -> None:
    while not done.wait(config.heartbeat_interval):
        if not heartbeat(task_id, config.agent_id, lease_seconds=config.lease_seconds, db_path=config.db_path):
            done.set()
            raise LeaseRevoked(task_id)
        print(f"heartbeat task_id={task_id}")


def do_work(task_id: str, config: Config) -> None:
    done = threading.Event()
    failure: list[BaseException] = []

    def beat() -> None:
        try:
            heartbeat_until_done(task_id, config, done)
        except BaseException as exc:
            failure.append(exc)

    thread = threading.Thread(target=beat, daemon=True)
    thread.start()
    try:
        run_handler(task_id, config)
    finally:
        done.set()
        thread.join(timeout=max(config.heartbeat_interval, 0.1) + 1)
    if failure:
        raise failure[0]


def reconcile_node(state: LoopState, config: Config) -> LoopState:
    if SHUTDOWN.requested:
        raise KeyboardInterrupt("shutdown requested")
    expired = list(expire_leases(db_path=config.db_path))
    print("reconciled=" + (",".join(expired) if expired else "none"))
    return {
        **state,
        "expired_task_ids": expired,
        "events": [*state.get("events", []), f"reconciled {len(expired)} leases"],
    }


def poll_node(state: LoopState, config: Config) -> LoopState:
    if SHUTDOWN.requested:
        raise KeyboardInterrupt("shutdown requested")
    runner_state = run_runner(config.db_path)
    route = str(runner_state.get("next_route"))
    ready_tasks = filter_cooldown_tasks(list(runner_state.get("ready_tasks", [])), state)
    iterations = int(state.get("iterations", 0)) + 1
    print(f"route={route}")
    return {
        **state,
        "route": route,
        "last_route": route,
        "ready_tasks": ready_tasks,
        "iterations": iterations,
        "events": [*state.get("events", []), f"polled route={route}"],
    }


def filter_cooldown_tasks(ready_tasks: list[str], state: LoopState) -> list[str]:
    cooldowns = state.get("retry_cooldowns", {})
    if not cooldowns:
        return ready_tasks
    now = time.time()
    active = {task_id: retry_at for task_id, retry_at in cooldowns.items() if retry_at > now}
    skipped = [task_id for task_id in ready_tasks if task_id in active]
    for task_id in skipped:
        remaining = max(0, int(active[task_id] - now))
        print(f"retry_cooldown task_id={task_id} remaining_seconds={remaining}")
    return [task_id for task_id in ready_tasks if task_id not in active]


def choose_after_poll(state: LoopState, config: Config) -> Literal["claim", "reconcile", "operator_interrupt", "end"]:
    route = state.get("route")
    if route == "claim_or_assign" and state.get("ready_tasks"):
        return "claim"
    if route in {"review", "propose_helper"}:
        return "operator_interrupt"
    if config.once or reached_iteration_cap(state, config):
        return "end"
    return "reconcile"


def claim_node(state: LoopState, config: Config) -> LoopState:
    task_id = state.get("ready_tasks", [None])[0]
    if not task_id:
        return {**state, "last_result": "no_ready_task", "current_task": None, "current_task_id": None}
    if config.dry_run:
        print(f"dry_run: would_claim task_id={task_id}")
        return {
            **state,
            "last_result": "dry_run_no_claim",
            "current_task": None,
            "current_task_id": None,
            "attempt_count": int(state.get("attempt_count", 0)) + 1,
        }
    claimed, reason = claim_task_with_reason(
        task_id,
        config.agent_id,
        lease_seconds=config.lease_seconds,
        db_path=config.db_path,
    )
    if not claimed:
        print(f"claim_failed task_id={task_id} reason={reason or 'not_claimable'}")
        return {
            **state,
            "last_result": f"claim_blocked_by_{reason or 'not_claimable'}",
            "current_task": None,
            "current_task_id": None,
            "attempt_count": int(state.get("attempt_count", 0)) + 1,
        }
    print(f"claimed task_id={task_id}")
    return {
        **state,
        "last_result": "claimed",
        "current_task": task_id,
        "current_task_id": task_id,
        "attempt_count": int(state.get("attempt_count", 0)) + 1,
    }


def choose_after_claim(state: LoopState, config: Config) -> Literal["submit", "reconcile", "end"]:
    if state.get("last_result") == "claimed":
        return "submit"
    if config.once or reached_iteration_cap(state, config):
        return "end"
    return "reconcile"


def submit_node(state: LoopState, config: Config) -> LoopState:
    task_id = state.get("current_task")
    if not task_id:
        return {**state, "last_result": "no_current_task"}
    try:
        do_work(task_id, config)
        if not submit_task(task_id, config.agent_id, db_path=config.db_path):
            print(f"submit_failed task_id={task_id}")
            return {**state, "last_result": "submit_failed", "current_task": None, "current_task_id": None}
        print(f"submitted task_id={task_id}")
        if config.export_after_submit:
            run_export(config.db_path)
            print("exported state")
        return {**state, "last_result": "submitted", "current_task": None, "current_task_id": None}
    except subprocess.CalledProcessError as exc:
        release_task(task_id, config.agent_id, status="READY", db_path=config.db_path)
        retry_cooldowns = dict(state.get("retry_cooldowns", {}))
        if config.retry_cooldown > 0:
            retry_cooldowns[task_id] = time.time() + config.retry_cooldown
            print(
                f"released task_id={task_id} status=READY reason={type(exc).__name__} "
                f"retry_cooldown={config.retry_cooldown}"
            )
        else:
            retry_cooldowns.pop(task_id, None)
            print(f"released task_id={task_id} status=READY reason={type(exc).__name__}")
        return {
            **state,
            "last_result": "handler_failed",
            "current_task": None,
            "current_task_id": None,
            "retry_cooldowns": retry_cooldowns,
        }
    except BaseException as exc:
        release_task(task_id, config.agent_id, status="READY", db_path=config.db_path)
        print(f"released task_id={task_id} status=READY reason={type(exc).__name__}")
        raise


def choose_after_submit(state: LoopState, config: Config) -> Literal["reconcile", "end"]:
    return "end" if config.once or reached_iteration_cap(state, config) else "reconcile"


def operator_interrupt_node(state: LoopState, _config: Config) -> LoopState:
    route = state.get("route", "unknown")
    interrupt(f"operator input required for route={route}")
    return {**state, "last_result": "interrupted"}


def reached_iteration_cap(state: LoopState, config: Config) -> bool:
    return bool(config.max_iterations and int(state.get("iterations", 0)) >= config.max_iterations)


def build_loop_graph(config: Config):
    graph = StateGraph(LoopState)
    graph.add_node("reconcile", lambda state: reconcile_node(state, config))
    graph.add_node("poll", lambda state: poll_node(state, config))
    graph.add_node("claim", lambda state: claim_node(state, config))
    graph.add_node("submit", lambda state: submit_node(state, config))
    graph.add_node("operator_interrupt", lambda state: operator_interrupt_node(state, config))

    graph.add_edge(START, "reconcile")
    graph.add_edge("reconcile", "poll")
    graph.add_conditional_edges(
        "poll",
        lambda state: choose_after_poll(state, config),
        {
            "claim": "claim",
            "reconcile": "reconcile",
            "operator_interrupt": "operator_interrupt",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "claim",
        lambda state: choose_after_claim(state, config),
        {"submit": "submit", "reconcile": "reconcile", "end": END},
    )
    graph.add_conditional_edges(
        "submit",
        lambda state: choose_after_submit(state, config),
        {"reconcile": "reconcile", "end": END},
    )
    graph.add_edge("operator_interrupt", END)
    return graph.compile(checkpointer=MapSqliteSaver(config.db_path))


def run_loop(config: Config) -> int:
    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)
    lock = acquire_loop_lock(config)
    atexit.register(release_loop_lock, lock)
    try:
        app = build_loop_graph(config)
        state: LoopState = {
            "agent_id": config.agent_id,
            "db_path": str(config.db_path),
            "current_task": None,
            "iterations": 0,
            "retry_cooldowns": {},
            "events": [],
        }
        thread_cfg = {"configurable": {"thread_id": f"agent-loop-{config.agent_id}"}}
        initial = Command(resume=True) if config.resume else state
        result = app.invoke(initial, config=thread_cfg)
        interrupts = result.get("__interrupt__", [])
        if interrupts:
            message = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
            print(json.dumps({"interrupted": True, "message": message}, separators=(",", ":")))
        return 0
    finally:
        release_loop_lock(lock)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-id", default="codex")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--handler", help="Shell command template; {task_id} is replaced")
    parser.add_argument("--heartbeat-interval", type=float, default=300)
    parser.add_argument("--lease-seconds", type=int, default=1800)
    parser.add_argument("--no-export-after-submit", action="store_true")
    parser.add_argument("--max-iterations", type=int, default=0, help="0 means no explicit cap")
    parser.add_argument("--retry-cooldown", type=int, default=300,
                        help="Seconds to skip a task after handler failure; 0 disables")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from a previous operator_interrupt checkpoint for this agent-id")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = Config(
        agent_id=args.agent_id,
        db_path=args.db,
        once=args.once,
        dry_run=args.dry_run,
        handler=args.handler,
        heartbeat_interval=args.heartbeat_interval,
        lease_seconds=args.lease_seconds,
        export_after_submit=not args.no_export_after_submit,
        max_iterations=1 if args.once else args.max_iterations,
        retry_cooldown=args.retry_cooldown,
        resume=args.resume,
    )
    try:
        return run_loop(config)
    except LockHeld as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
