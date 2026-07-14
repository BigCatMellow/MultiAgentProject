# Insight Record

Insight ID: INS-0016
Project: MAP
Related task: TASK-144
Detected by: codex-lab-veto
Date: 2026-07-04
Status: PROMOTED

## Short description


Validator coverage must include live command surfaces, not only docs

## Trigger


Stale /home/home/Downloads/MultiAgentProject paths remained in ai-command-center launch scripts even though validate_canonical_repo_paths.py covered primary docs.

## The synthesis


Validator coverage must include live command surfaces, not only docs

## Why it might matter


Agents and operators follow launchers as executable truth. If validators scan only prose, live scripts can drift after decisions change.

## Evidence


TASK-144 fixed ai-command-center-cli, ai-command-center-shell, ai-command-center-antigravity, and agent-deck, then expanded validate_canonical_repo_paths.py to scan those live surfaces.

## Risk


A future canonical path, approval-mode, or helper-safety change could appear correct in docs while launchers still start agents in the wrong repo or with stale instructions.

## Scope


Only the files and artifacts named in this record.

## Recommended next action

Choose one:

- [ ] Ignore — not worth preserving
- [x] Park for later — valid but low priority
- [ ] Create follow-up task — actionable now
- [ ] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

Resolved 2026-07-14 (claude-lab-zera), found via `map_emergence.py stale`.
The concrete fix already shipped in TASK-144 (the launch-script scan
expansion this record cites as evidence); the remaining value is the
durable principle itself ("validator coverage must include live command
surfaces, not only docs"), parked here as precedent. No new follow-up task
needed — this session's own validator work (TASK-152's `validate_layer1.py`
aggregation, TASK-160/164's read-only mission-control surfaces) already
follows this principle by construction (composing existing live-state
checks rather than re-scanning docs only).
