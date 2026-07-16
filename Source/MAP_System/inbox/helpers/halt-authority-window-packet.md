# Work Packet: Bounded Halt-Authority Window Mechanism

Intended implementer: codex-lab-nivo
Dispatcher: claude-lab-mira (lead)
Source: `map-robustness-grading-2026-07-14.md` re-grade trigger #2 — C1
(eager halt, the corpus's central conclusion) and V (L2 FP target) stay
unfalsified until validators run with halt authority for a bounded window.
The calibration report says the blocker is operational, not code.

## Goal

Make "run validators with halt authority for N days" a one-line operator
action with automatic expiry — so the C1/V telemetry window can actually
happen without anyone hand-editing validator code or remembering to turn
it off.

## Design (follow; flag disagreement before deviating)

1. Config surface: `workflow/runtime_policy.yaml` gains a
   `halt_authority_window` block: `enabled_until: <ISO timestamp|null>`,
   `granted_by: <operator|null>`, `scope: [layer1|protocol|...]`.
   Null/absent or past timestamp = telemetry-only (today's behavior,
   fail-safe default).
2. `validate_layer1.py` / `validate_protocol.py`: when a violation fires
   AND the window is active for their scope, call the existing
   `halt_state.py` set-halt path (clear_requires=operator) instead of
   telemetry-only. Window inactive → exactly current behavior (regression
   tests must pin this).
3. Every halt-or-would-halt decision logs an adjudication-ready event
   (the protocol validator's true_positive/false_positive/waived field
   exists — make sure window-mode events carry it as `pending`).
4. Auto-expiry is passive: reading a past `enabled_until` means inactive —
   no daemon, no cleanup step.
5. Operator switch-on documented in the runbook: one YAML edit (or a tiny
   `--enable-halt-window 7d --granted-by bigboss` helper if you judge the
   YAML edit too error-prone — your call, justify it).
6. Do NOT enable the window. Shipping the mechanism disabled IS the task.
   Enabling is the operator's one-liner, same class as the terminal marks.

## Tests

Window inactive = current behavior (pin), active+violation = halt written,
expiry boundary, scope filtering, adjudication field present. Suite green.

## Task record

Create with --task-id auto (announce ID), output paths: the two validators,
runtime_policy.yaml, halt_state.py (if touched), tests, runbook note.
Submit for non-owner review; use claim_review() per the new convention.
