# Insight Record

Insight ID: INS-0004
Project: MAP
Related task: TASK-056
Detected by: claude-lab-taro
Date: 2026-07-01
Status: PROMOTED

## Short description


Fail-safe identity pattern (CommandCenterUI's browser-mode default) beats guessing an owner identity

## Trigger


First backend draft hardcoded '--name maki' for all hcom sends/lists, so any human or agent using the web UI would be misattributed as codex-lab-maki in the audit trail. Fix made the default identity 'browser' with sends explicitly blocked (403 + plain-language explanation) until a real registered hcom name is configured via flag/env var.

## The synthesis


Fail-safe identity pattern (CommandCenterUI's browser-mode default) beats guessing an owner identity

## Why it might matter


Any tool that acts on behalf of a human/agent through a shared multi-agent bus (hcom) should fail closed on identity - block the action with a clear message - rather than default to a plausible-but-wrong identity. Silent misattribution corrupts the audit trail in a way that's hard to notice after the fact.

## Evidence


MAP_System/events/events.jsonl TASK-056/057 REVIEW_APPROVED entries; Projects/CommandCenterUI/app/server.py HCOM_AGENT_NAME handling

## Risk


Acting without promotion could bypass HPOM governance.

## Scope


Only the files and artifacts named in this record.

## Recommended next action

Choose one:

- [ ] Ignore — not worth preserving
- [ ] Park for later — valid but low priority
- [ ] Create follow-up task — actionable now
- [ ] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

-

## Lifecycle close-out (2026-07-02, TASK-078)

Promoted via IDEA-0004 / PROMO-0004 into the 'Security Second Pass' Review Standard addition in MAP_System/AGENTS.md (TASK-078, pending peer review).
