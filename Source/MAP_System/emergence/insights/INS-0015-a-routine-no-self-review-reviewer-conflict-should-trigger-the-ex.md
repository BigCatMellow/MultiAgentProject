# Insight Record

Insight ID: INS-0015
Project: MAP
Related task: TASK-137
Detected by: codex-lab-neko
Date: 2026-07-04
Status: PROMOTED

## Short description


A routine no-self-review reviewer conflict should trigger the existing visible-helper path automatically instead of escalating to the operator when no clean core reviewer is live.

## Trigger


During TASK-137 review routing, `claude-lab-vino` correctly declined review
because they had authored the actual `Projects/ProjectUpdater/app/index.html`
Areas-removal edit. `codex-lab-neko` initially escalated that routine
no-self-review conflict back to the operator instead of immediately using the
existing visible-helper policy.

## The synthesis


A routine no-self-review reviewer conflict should trigger the existing visible-helper path automatically instead of escalating to the operator when no clean core reviewer is live.

## Why it might matter


MAP already had enough machinery to solve the problem: helper notes, visible
wezterm helper tabs, bounded review packets, hcom status, and normal review /
release gates. Escalating the routing choice wasted operator attention and
contradicted the command-center goal that routine process gaps should be solved
by the system when safe.

## Evidence


- `MAP_System/events/events.jsonl` records the TASK-137 no-self-review conflict,
  the helper spawn, helper approval, and release.
- `MAP_System/inbox/helpers/helper-review-task-137.md` records the helper scope,
  reviewer identity, output paths, result, and stop condition.
- `MAP_System/artifacts/reviews/task137-review-bula.md` shows the visible helper
  completed an independent review after Vino's conflict.
- Operator feedback explicitly stated this should not have required another
  prompt because the project already had enough systems to move forward.

## Risk


If agents over-apply this lesson, they could spawn helpers for decisions that
actually require operator authority. The rule must stay bounded to routine
review routing where the task is already submitted, the conflict is only
no-self-review, the helper is visible, and normal review/release gates remain
intact.

## Scope


Applies to MAP review routing for submitted tasks. It does not authorize hidden
helpers, headless sessions, destructive actions, scope changes, privacy-risk
work, security-sensitive decisions, or bypassing human/operator approval gates.

## Recommended next action

Choose one:

- [ ] Ignore — not worth preserving
- [ ] Park for later — valid but low priority
- [x] Create follow-up task — actionable now
- [ ] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

- Promoted into `TASK-138`, which updated `MAP_System/AGENTS.md` and
  `MAP_System/notes/helper-agent-guide.md` with the visible-helper default path
  for routine no-self-review reviewer conflicts.
