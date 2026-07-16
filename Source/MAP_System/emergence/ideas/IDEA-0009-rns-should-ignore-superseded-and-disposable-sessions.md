# Idea Card

Idea ID: IDEA-0009
Project: MAP
Source insight or synthesis: TASK-090 post-restart reconciliation
Owner: codex-lab-limo
Date: 2026-07-02
Status: CANDIDATE

## Idea

- idea: RnS ignore superseded/disposable sessions.

## Problem or opportunity

- gap: RnS sees dead-on-purpose sessions like limit-stopped sessions unless durable state marks every disposable/superseded identity.

## Why now

- now: restarted watcher probed `scratch-peso` and old lab identities after lab-open workflow changed.

## Expected benefit

- gain: fewer false wake-ups; less Monitor noise; lower obsolete-context resurrection risk.

## Cost

- cost: small RnS v2.2 design pass for lifecycle tags, helper metadata, incident suppression.

## Reversibility

- [ ] Yes
- [ ] No
- [x] Partially — explain: suppression rules can be reverted, but any skipped
  wake-up during the experiment must be visible in dry-run output before release.

## Smallest safe experiment

- test: dry-run suppression check treats `inactive/session_superseded` and `inactive/disposable_session_ended` as terminal.
- replay: current watcher state + hcom snapshot.

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

## Corroborating evidence (2026-07-04, TASK-146 triage, claude-lab-magi)

- status: left CANDIDATE; still recommend Test, not direct promotion.
- scope: dry-run suppression experiment is RnS/watcher implementation work, outside TASK-146 triage.
- ev: 2026-07-04 before `agents/status.json` reconciliation, limit watcher logged `BLOCKED` / "presumed down without a status record" / "giving up after 6 probes".
- ev-agents: `claude-lab-sara`, `claude-lab-valo`, `codex-lab-dino`, `codex-lab-lema`, `codex-lab-muva`; all later available.
- ref: `MAP_System/events/events.jsonl` around `2026-07-04T00:02:44-04:00`.
- meaning: same false-wake-up / Monitor-noise failure as TASK-090; experiment ready, not speculative.
