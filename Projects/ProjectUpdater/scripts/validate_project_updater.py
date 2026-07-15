#!/usr/bin/env python3
"""Browser regression checks for the standalone ProjectUpdater app.

Run with a Python environment that has Playwright installed, for example:

    /tmp/pw_venv/bin/python Projects/ProjectUpdater/scripts/validate_project_updater.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


STORE_KEY = "projectUpdater.v1"


def iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def date_days_from_now(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).date().isoformat()


def seed_data() -> dict[str, Any]:
    return {
        "projects": [
            {
                "id": "test_stale",
                "name": "Validator stale project",
                "area": "Work",
                "goal": "Should appear in stale filters.",
                "goals": ["Should appear in stale filters."],
                "nextAction": "Refresh stale task",
                "referencePath": "/tmp/validator-stale",
                "status": "Active",
                "priority": "High",
                "progress": 20,
                "points": 10,
                "streak": 0,
                "reminderDays": 3,
                "lastVisited": iso_days_ago(10),
                "dueDate": None,
            },
            {
                "id": "test_due",
                "name": "Validator due project",
                "area": "Home",
                "goal": "Should appear in due-soon filters.",
                "goals": ["Should appear in due-soon filters."],
                "nextAction": "Prepare due task",
                "referencePath": "/tmp/validator-due",
                "status": "Active",
                "priority": "Medium",
                "progress": 45,
                "points": 15,
                "streak": 1,
                "reminderDays": 14,
                "lastVisited": iso_days_ago(1),
                "dueDate": date_days_from_now(3),
            },
            {
                "id": "test_healthy",
                "name": "Validator healthy project",
                "area": "Side Project",
                "goal": "Should remain on track.",
                "goals": ["Should remain on track."],
                "nextAction": "Keep moving",
                "referencePath": "",
                "status": "Active",
                "priority": "Low",
                "progress": 70,
                "points": 20,
                "streak": 3,
                "reminderDays": 14,
                "lastVisited": iso_days_ago(0),
                "dueDate": None,
            },
            {
                "id": "test_finished",
                "name": "Validator finished project",
                "area": "Work",
                "goal": "Should appear only in finished/all.",
                "goals": ["Should appear only in finished/all."],
                "nextAction": "None",
                "referencePath": "",
                "status": "Finished",
                "priority": "Low",
                "progress": 100,
                "points": 30,
                "streak": 0,
                "reminderDays": 14,
                "lastVisited": iso_days_ago(20),
                "dueDate": None,
            },
            {
                "id": "test_archived",
                "name": "Validator archived project",
                "area": "Archive",
                "goal": "Should appear only in archived/all.",
                "goals": ["Should appear only in archived/all."],
                "nextAction": "None",
                "referencePath": "",
                "status": "Archived",
                "priority": "Low",
                "progress": 100,
                "points": 5,
                "streak": 0,
                "reminderDays": 14,
                "lastVisited": iso_days_ago(30),
                "dueDate": None,
            },
        ],
        "notes": [
            {
                "id": "note_seed",
                "projectId": "test_stale",
                "projectName": "Validator stale project",
                "noteType": "Note",
                "energy": "Medium",
                "text": "Seed note",
                "nextAction": "",
                "timestamp": iso_days_ago(1),
            }
        ],
    }


def visible_unlabeled_controls(page: Any) -> list[dict[str, str]]:
    return page.evaluate(
        """
        () => Array.from(document.querySelectorAll('input, select, textarea'))
          .filter((el) => {
            const style = getComputedStyle(el);
            const rect = el.getBoundingClientRect();
            return style.display !== 'none' && style.visibility !== 'hidden' &&
              rect.width > 0 && rect.height > 0 && !el.closest('[hidden]');
          })
          .filter((el) => {
            const id = el.id;
            const hasForLabel = id && document.querySelector(`label[for="${CSS.escape(id)}"]`);
            const ariaLabel = el.getAttribute('aria-label');
            const labelledBy = el.getAttribute('aria-labelledby');
            const hasLabelledBy = labelledBy && labelledBy.split(/\\s+/).every((part) => document.getElementById(part));
            return !(hasForLabel || ariaLabel || hasLabelledBy);
          })
          .map((el) => ({ tag: el.tagName.toLowerCase(), id: el.id || '', type: el.type || '' }))
        """
    )


def assert_true(results: list[str], condition: bool, message: str) -> None:
    if not condition:
        results.append(message)


def run_checks(app_path: Path, headed: bool) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Playwright is required. Run with an environment that has it installed, "
            "for example /tmp/pw_venv/bin/python."
        ) from exc

    failures: list[str] = []
    evidence: dict[str, Any] = {}
    url = app_path.resolve().as_uri()
    seed = seed_data()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.set_default_timeout(7000)
        console_errors: list[str] = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(url)
        page.evaluate(
            "(payload) => localStorage.setItem(payload.key, JSON.stringify(payload.data))",
            {"key": STORE_KEY, "data": seed},
        )
        page.reload()

        status_left = page.locator("#statusLeft").inner_text()
        evidence["desktop_status"] = status_left
        assert_true(failures, "3 active projects" in status_left, "Dashboard active count did not match seeded active projects.")
        assert_true(failures, "1 stale" in status_left, "Dashboard stale count did not match seeded stale project.")
        assert_true(failures, "1 due soon" in status_left, "Dashboard due-soon count did not match seeded due project.")
        assert_true(failures, page.locator(".banner").count() == 1, "Stale reminder banner was not shown for seeded stale project.")

        page.locator('.sb-item[data-view="projects"]').first.click()
        filters = page.locator(".filter-chip").all_inner_texts()
        evidence["filters"] = filters
        for label in ["Open", "Stale", "Due soon", "On track", "Finished", "Archived", "All"]:
            assert_true(failures, label in filters, f"Missing Projects filter: {label}.")
        sidebar_headings = page.locator("#sidebar .sb-heading").all_inner_texts()
        evidence["sidebar_headings"] = sidebar_headings
        assert_true(failures, "Areas" not in sidebar_headings, "Sidebar still shows the removed Areas section.")
        assert_true(failures, page.locator("#areaList").count() == 0, "Removed area shortcut container still exists.")

        page.get_by_text("Stale", exact=True).click()
        stale_text = page.locator("#content").inner_text()
        assert_true(failures, "Validator stale project" in stale_text, "Stale filter did not show seeded stale project.")
        assert_true(failures, "Validator due project" not in stale_text, "Stale filter included non-stale due project.")

        stale_pressed = page.get_by_text("Stale", exact=True).get_attribute("aria-pressed")
        open_pressed = page.get_by_text("Open", exact=True).get_attribute("aria-pressed")
        evidence["filter_aria_after_stale"] = {"Stale": stale_pressed, "Open": open_pressed}
        assert_true(failures, stale_pressed == "true" and open_pressed == "false", "Filter aria-pressed state did not update.")

        page.get_by_text("Due soon", exact=True).click()
        due_text = page.locator("#content").inner_text()
        assert_true(failures, "Validator due project" in due_text, "Due-soon filter did not show seeded due project.")

        page.get_by_text("Finished", exact=True).click()
        assert_true(
            failures,
            "Validator finished project" in page.locator("#content").inner_text(),
            "Finished filter did not show finished project.",
        )

        page.get_by_text("Archived", exact=True).click()
        assert_true(
            failures,
            "Validator archived project" in page.locator("#content").inner_text(),
            "Archived filter did not show archived project.",
        )

        page.locator('.sb-item[data-view="add"]').first.click()
        page.locator("#newName").fill("Validator added project")
        page.locator("#newArea").fill("Validation")
        page.locator("#newPrioritySeg button[data-val='High']").click()
        priority_states = page.locator("#newPrioritySeg button").evaluate_all(
            "(buttons) => buttons.map((b) => [b.textContent.trim(), b.getAttribute('aria-pressed')])"
        )
        evidence["priority_aria_after_high"] = priority_states
        assert_true(
            failures,
            ["High", "true"] in priority_states and ["Medium", "false"] in priority_states,
            "Priority segmented aria-pressed state did not update.",
        )
        page.locator("#newGoals").fill("Added by validator and persisted across reload.\nSecond validator goal")
        page.locator("#newNextAction").fill("Confirm persistence")
        page.locator("#newReferencePath").fill("/tmp/validator-added")
        page.locator("#newReminderDays").fill("5")
        page.locator("#addProjectBtn").click()
        page.reload()
        page.locator("#search").fill("Validator added project")
        page.wait_for_timeout(100)
        assert_true(
            failures,
            "Validator added project" in page.locator("#content").inner_text(),
            "Added project did not persist across reload/search.",
        )

        page.locator('[data-edit]').first.click()
        page.locator("#editName").fill("Validator edited project")
        page.locator("#editArea").fill("Edited Area")
        page.locator("#editGoals").fill("Edited primary goal\nEdited second goal")
        page.locator("#editNextAction").fill("Edited next action")
        page.locator("#editReferencePath").fill("/tmp/validator-edited")
        page.locator("#editReminderDays").fill("9")
        page.locator("#editStatus").select_option("In progress")
        page.locator("#editProgress").fill("64")
        page.locator("#saveProjectBtn").click()
        page.reload()
        stored_after_edit = page.evaluate(f"() => JSON.parse(localStorage.getItem('{STORE_KEY}'))")
        edited_project = next((project for project in stored_after_edit["projects"] if project["name"] == "Validator edited project"), None)
        evidence["edited_project"] = edited_project
        assert_true(failures, edited_project is not None, "Edited project name did not persist.")
        if edited_project:
            assert_true(failures, edited_project["area"] == "Edited Area", "Edited area did not persist.")
            assert_true(failures, edited_project["goals"] == ["Edited primary goal", "Edited second goal"], "Edited multi-goal list did not persist.")
            assert_true(failures, edited_project["goal"] == "Edited primary goal", "Single-goal compatibility field was not updated.")
            assert_true(failures, edited_project["nextAction"] == "Edited next action", "Edited next action did not persist.")
            assert_true(failures, edited_project["referencePath"] == "/tmp/validator-edited", "Edited reference path did not persist.")
            assert_true(failures, edited_project["status"] == "In progress", "Edited status did not persist.")
            assert_true(failures, edited_project["progress"] == 64, "Edited progress did not persist.")

        page.locator("#search").fill("Validator edited project")
        page.wait_for_timeout(100)
        page.locator('[data-open-ref]').first.click()
        page.wait_for_timeout(100)
        ref_text = page.locator("#statusToast").inner_text()
        evidence["reference_status"] = ref_text
        assert_true(failures, "Opened folder" in ref_text and "/tmp/validator-edited" in ref_text, "Open folder action did not expose the stored project reference.")

        page.locator("#search").fill("Validator stale project")
        page.wait_for_timeout(100)
        page.once("dialog", lambda dialog: dialog.accept())
        page.locator('[data-delete]').first.click()
        page.reload()
        stored_after_delete = page.evaluate(f"() => JSON.parse(localStorage.getItem('{STORE_KEY}'))")
        deleted_project = next((project for project in stored_after_delete["projects"] if project["id"] == "test_stale"), None)
        stale_notes = [note for note in stored_after_delete["notes"] if note["projectId"] == "test_stale"]
        evidence["delete_result"] = {"project_exists": deleted_project is not None, "remaining_notes": len(stale_notes)}
        assert_true(failures, deleted_project is None, "Deleted project remained in localStorage.")
        assert_true(failures, stale_notes == [], "Deleting a project did not remove its related notes.")

        page.locator("#search").fill("")
        page.locator('.sb-item[data-view="note"]').first.click()
        page.locator("#noteProject").select_option("test_due")
        page.locator("#noteText").fill("Validator archive note")
        page.locator("#noteStatus").select_option("Archived")
        page.locator("#noteProgress").fill("77")
        page.locator("#saveNoteBtn").click()
        page.reload()
        stored = page.evaluate(f"() => JSON.parse(localStorage.getItem('{STORE_KEY}'))")
        archived_due = next((project for project in stored["projects"] if project["id"] == "test_due"), None)
        notes = [note for note in stored["notes"] if note["projectId"] == "test_due"]
        evidence["archived_due_status_after_reload"] = archived_due["status"] if archived_due else None
        evidence["notes_for_due_after_reload"] = len(notes)
        assert_true(failures, archived_due is not None and archived_due["status"] == "Archived", "Quick Note status update did not persist.")
        assert_true(failures, bool(notes), "Quick Note did not persist a note for the selected project.")
        page.locator('.sb-item[data-view="projects"]').first.click()
        page.get_by_text("Archived", exact=True).click()
        archived_text = page.locator("#content").inner_text()
        page.get_by_text("Open", exact=True).click()
        open_text = page.locator("#content").inner_text()
        assert_true(failures, "Validator due project" in archived_text, "Archived status update did not appear in Archived filter.")
        assert_true(failures, "Validator due project" not in open_text, "Archived status update still appeared in Open filter.")

        unlabeled = visible_unlabeled_controls(page)
        evidence["visible_unlabeled_controls_desktop"] = unlabeled
        assert_true(failures, unlabeled == [], f"Visible unlabeled controls found: {unlabeled}")

        mobile = browser.new_page(viewport={"width": 390, "height": 800})
        mobile_console_errors: list[str] = []
        mobile.on("console", lambda msg: mobile_console_errors.append(msg.text) if msg.type == "error" else None)
        mobile.goto(url)
        mobile.evaluate(
            "(payload) => localStorage.setItem(payload.key, JSON.stringify(payload.data))",
            {"key": STORE_KEY, "data": seed},
        )
        mobile.reload()
        mobile_nav_visible = mobile.locator("#mobileViewNav").is_visible()
        sidebar_visible = mobile.locator("#sidebar").is_visible()
        options = mobile.locator("#mobileViewNav option").all_inner_texts()
        evidence["mobile"] = {
            "mobile_nav_visible": mobile_nav_visible,
            "sidebar_visible": sidebar_visible,
            "options": options,
        }
        assert_true(failures, mobile_nav_visible and not sidebar_visible, "Mobile layout did not expose mobile nav while hiding sidebar.")
        assert_true(failures, options == ["Dashboard", "Projects", "Quick Note", "Add Project"], "Mobile navigation options changed.")
        mobile.locator("#mobileViewNav").select_option("projects")
        assert_true(failures, mobile.locator("#crumb").inner_text() == "Projects", "Mobile nav did not navigate to Projects.")
        mobile_unlabeled = visible_unlabeled_controls(mobile)
        evidence["visible_unlabeled_controls_mobile"] = mobile_unlabeled
        assert_true(failures, mobile_unlabeled == [], f"Visible unlabeled mobile controls found: {mobile_unlabeled}")

        evidence["console_errors"] = console_errors + mobile_console_errors
        assert_true(failures, evidence["console_errors"] == [], f"Browser console errors: {evidence['console_errors']}")
        browser.close()

    return {"ok": not failures, "failures": failures, "evidence": evidence}


def parse_args() -> argparse.Namespace:
    default_app = Path(__file__).resolve().parents[1] / "app" / "index.html"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=default_app, help="Path to ProjectUpdater app/index.html")
    parser.add_argument("--headed", action="store_true", help="Run browser headed for local debugging")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.app.exists():
        print(f"error: app file not found: {args.app}", file=sys.stderr)
        return 2
    result = run_checks(args.app, args.headed)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
