# Idea Card

Idea ID: IDEA-0009
Project: MAP
Source insight or synthesis: TASK-090 post-restart reconciliation
Owner: codex-lab-limo
Date: 2026-07-02
Status: CANDIDATE

## Idea


RnS should ignore superseded and disposable sessions

## Problem or opportunity


RnS cannot distinguish dead-on-purpose sessions from limit-stopped sessions unless every disposable/superseded session is manually written into durable agent state.

## Why now


The restarted watcher surfaced the gap by probing scratch-peso and attempting to recover old lab identities after the lab-open workflow changed.

## Expected benefit


Fewer false wake-ups, less monitor noise, and lower risk of resurrecting obsolete context.

## Cost


Requires a small RnS v2.2 design pass around session lifecycle tags, disposable helper metadata, and incident suppression rules.

## Reversibility

Can this be undone easily?

- [ ] Yes
- [ ] No
- [x] Partially — explain: suppression rules can be reverted, but any skipped
  wake-up during the experiment must be visible in dry-run output before release.

## Smallest safe experiment


Add a dry-run-only suppression check that treats inactive/session_superseded and inactive/disposable_session_ended as terminal, then replay the current watcher state and hcom snapshot.

## Decision needed

Who must approve this before it can be promoted?

- [ ] Task DRI — within current task scope
- [ ] Review DRI — requires review gate
- [x] State Steward — changes shared state
- [ ] Project DRI — changes project direction
- [ ] Human Owner — changes MAP-level rules or governance

## Recommendation

- [ ] Park — valid but not the right time
- [ ] Reject — not worth pursuing
- [x] Test — run the smallest safe experiment
- [ ] Promote to task — evidence is sufficient, ready for HPOM
