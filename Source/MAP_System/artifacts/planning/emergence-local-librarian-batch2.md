# Idea Card
### Idea ID: IDEA-0009
### Project: MAP
### Source insight or synthesis: TASK-090 post-restart reconciliation
### Owner: codex-lab-limo
### Date: 2026-07-02
### Status: CANDIDATE

## Idea
RnS should ignore superseded and disposable sessions
### Problem or opportunity
RnS cannot distinguish dead-on-purpose sessions from limit-stopped sessions[8D[K
sessions unless every disposable/superseded session is manually written int[3D[K
into durable agent state.
### Why now
The restarted watcher surfaced the gap by probing scratch-peso and attempti[8D[K
attempting to recover old lab identities after the lab-open workflow change[6D[K
changed.
### Expected benefit
Fewer false wake-ups, less monitor noise, and lower risk of resurrecting ob[2D[K
obsolete context.

## Cost
Requires a small RnS v2.2 design pass around session lifecycle tags, dispos[6D[K
disposable helper metadata, and incident suppression rules.

## Reversibility
Can this be undone easily?
- Yes (suppression rules can be reverted)
- No (skipped wake-up during experiment must be visible in dry-run output b[1D[K
before release)

## Smallest safe experiment
Add a dry-run-only suppression check that treats inactive/session_supersede[26D[K
inactive/session_superseded and inactive/disposable_session_ended as termin[6D[K
terminal, then replay the current watcher state and hcom snapshot.

## Decision needed
Who must approve this before it can be promoted?
- Task DRI — within current task scope
- Review DRI — requires review gate
- State Steward — changes shared state
- Project DRI — changes project direction
- Human Owner — changes MAP-level rules or governance

## Recommendation
- Park — valid but not the right time
- Reject — not worth pursuing
- Test — run the smallest safe experiment
- Promote to task — evidence is sufficient, ready for HPOM

