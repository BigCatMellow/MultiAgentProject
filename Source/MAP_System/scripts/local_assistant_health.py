#!/usr/bin/env python3
"""Read-only local assistant capability health check."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any


REQUIRED_MODELS = (
    "llama3.2:3b",
    "llama3.2:1b",
    "qwen2.5-coder:3b",
    "qwen2.5-coder:1.5b",
    "gemma3:4b",
)


@dataclass(frozen=True)
class CommandResult:
    found: bool
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    error: str | None = None


def run_command(argv: list[str], *, timeout: float = 5.0) -> CommandResult:
    executable = shutil.which(argv[0])
    if not executable:
        return CommandResult(found=False, error=f"{argv[0]} not found")
    try:
        result = subprocess.run(
            [executable, *argv[1:]],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            found=True,
            returncode=None,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            error=f"{argv[0]} timed out after {timeout:g}s",
        )
    return CommandResult(
        found=True,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def parse_ollama_models(text: str) -> list[str]:
    models: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("name "):
            continue
        models.append(stripped.split()[0])
    return models


def check_ollama(timeout: float) -> dict[str, Any]:
    result = run_command(["ollama", "list"], timeout=timeout)
    models = parse_ollama_models(result.stdout) if result.found and result.returncode == 0 else []
    installed = set(models)
    return {
        "tool": "ollama",
        "type": "model-runtime",
        "found": result.found,
        "reachable": result.found and result.returncode == 0,
        "returncode": result.returncode,
        "error": result.error,
        "models": [
            {
                "name": model,
                "required": True,
                "available": model in installed,
                "authority": "draft-only",
            }
            for model in REQUIRED_MODELS
        ],
    }


def check_aider(timeout: float) -> dict[str, Any]:
    result = run_command(["aider", "--version"], timeout=timeout)
    version = result.stdout.strip() or result.stderr.strip()
    return {
        "tool": "aider",
        "type": "edit-workbench",
        "found": result.found,
        "reachable": result.found and result.returncode == 0,
        "returncode": result.returncode,
        "version": version if result.returncode == 0 else "",
        "error": result.error,
        "authority": "edit-helper",
    }


def build_report(timeout: float) -> dict[str, Any]:
    ollama = check_ollama(timeout)
    aider = check_aider(timeout)
    missing_models = [
        model["name"]
        for model in ollama["models"]
        if not model["available"]
    ]
    return {
        "status": "ok" if ollama["reachable"] and not missing_models and aider["found"] else "attention",
        "policy": {
            "runtime_status": "helper-capability-only",
            "core_agent_status": "not-registered",
            "final_authority": "core-agents-and-command-center",
            "starts_sessions": False,
        },
        "ollama": ollama,
        "aider": aider,
        "missing_models": missing_models,
        "required_models": list(REQUIRED_MODELS),
    }


def print_text(report: dict[str, Any]) -> None:
    print("Local Assistant Health")
    print(f"status: {report['status']}")
    print(f"runtime_status: {report['policy']['runtime_status']}")
    print(f"core_agent_status: {report['policy']['core_agent_status']}")
    print(f"starts_sessions: {str(report['policy']['starts_sessions']).lower()}")
    print("")
    ollama = report["ollama"]
    print(f"ollama: {'reachable' if ollama['reachable'] else 'unavailable'}")
    if ollama.get("error"):
        print(f"  error: {ollama['error']}")
    for model in ollama["models"]:
        state = "available" if model["available"] else "missing"
        print(f"  {model['name']}: {state}")
    print("")
    aider = report["aider"]
    print(f"aider: {'available' if aider['found'] else 'missing'}")
    if aider.get("version"):
        print(f"  version: {aider['version']}")
    if aider.get("error"):
        print(f"  error: {aider['error']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--timeout", type=float, default=5.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.timeout)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
