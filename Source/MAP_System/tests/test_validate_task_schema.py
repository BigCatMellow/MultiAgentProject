#!/usr/bin/env python3
"""Tests for tasks/TASK-NNN.json structural schema validation (TASK-196)."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_task_schema.py"
spec = importlib.util.spec_from_file_location("validate_task_schema", SCRIPT)
assert spec and spec.loader
vts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vts)


def valid_task(**overrides) -> dict:
    task = {
        "task_id": "TASK-999",
        "title": "Fixture task",
        "task_type": "implementation",
        "role": "implementer",
        "status": "READY",
        "dependencies": [],
        "owner": "test-owner",
        "description": "desc",
        "input_paths": [],
        "output_paths": ["out.md"],
        "acceptance_criteria": ["criterion"],
    }
    task.update(overrides)
    return task


def write_task(tmp: Path, task_id: str, data) -> None:
    (tmp / f"{task_id}.json").write_text(json.dumps(data), encoding="utf-8")


def test_valid_task_passes():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        write_task(base, "TASK-999", valid_task())
        assert vts.validate(base) == []


def test_missing_required_field_fails():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        task = valid_task()
        del task["description"]
        write_task(base, "TASK-999", task)
        errors = vts.validate(base)
        assert any("missing required field 'description'" in e for e in errors), errors


def test_wrong_type_for_list_field_fails():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        write_task(base, "TASK-999", valid_task(dependencies="TASK-001"))
        errors = vts.validate(base)
        assert any("field 'dependencies' must be a list" in e for e in errors), errors


def test_list_field_with_non_string_items_fails():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        write_task(base, "TASK-999", valid_task(output_paths=[1, 2]))
        errors = vts.validate(base)
        assert any("must be a list of strings" in e for e in errors), errors


def test_bad_status_vocabulary_fails():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        write_task(base, "TASK-999", valid_task(status="ALMOST_DONE"))
        errors = vts.validate(base)
        assert any("not in the canonical vocabulary" in e for e in errors), errors


def test_task_id_mismatch_with_filename_fails():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        write_task(base, "TASK-999", valid_task(task_id="TASK-111"))
        errors = vts.validate(base)
        assert any("does not match filename" in e for e in errors), errors


def test_malformed_task_id_shape_fails():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        write_task(base, "TASK-ABC", valid_task(task_id="TASK-ABC"))
        errors = vts.validate(base)
        assert any("does not match TASK-NNN shape" in e for e in errors), errors


def test_invalid_json_reported_without_crash():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "TASK-999.json").write_text("{not json", encoding="utf-8")
        errors = vts.validate(base)
        assert any("invalid JSON" in e for e in errors), errors


def test_real_task_files_all_pass():
    """The 190+ real task files in MAP_System/tasks/ are the acceptance gate
    itself: real drift here should fail the suite, not be silently allowed."""
    errors = vts.validate(ROOT / "tasks")
    assert errors == [], errors


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} task-schema tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
