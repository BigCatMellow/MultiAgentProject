# Insight Record

Insight ID: INS-0014
Project: MAP
Related task: TASK-129
Detected by: claude-lab-valo
Date: 2026-07-03
Status: PROMOTED

## Short description


Systems with a mechanical release/task gate get genuinely used repeatedly; systems that only require an agent to remember to do something extra stay documented-but-unexercised, regardless of how well-written or cross-linked they are.

## Trigger


TASK-129's MAP System Adherence Audit (operator hcom #22305) found Self-Repair/Risk/Change-Control/Emergence genuinely and repeatedly used, while Research/Context/Human-Interface/Archive-Retention/Retrospective were documented and validator-backed but essentially unexercised in practice.

## The synthesis


The used systems share a mechanical gate (release_task.py's REQUIRED_CHECKS, or this audit itself needing them). The unexercised systems all require an agent to proactively remember to do something extra with nothing checking that they did - the exact same root cause DEC-026 already diagnosed and fixed for Emergence specifically.

## Why it might matter


Generalizes DEC-026's fix beyond Emergence: before building a 12th system, or before assuming an 11th is 'done' because it's documented, ask whether adoption depends on memory or on a gate. If on memory, it will likely join Context/Research/Human-Interface/Archive-Retention as spec-only.

## Evidence


MAP_System/artifacts/audits/task-129-map-system-adherence-audit.md Synthesis section; MAP_System/artifacts/audits/task-130-map-systems-real-usage-evidence.md summary matrix.

## Risk


Over-applying this could mean gating everything mechanically, which risks the box-ticking-ceremony failure mode DEC-026's own PROJECT_BOOTSTRAPPING_SYSTEM.md amendment explicitly warned against for Emergence itself.

## Scope


MAP-system-level

## Recommended next action

Choose one:

- [ ] Ignore — not worth preserving
- [x] Park for later — valid but low priority
- [ ] Create follow-up task — actionable now
- [ ] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

- Applied narrowly already: TASK-129's audit report recommends a
  Retrospective-cadence gate (small, concrete) but explicitly declines to
  force Context Packets or Research Briefs into existence where none are
  needed yet, per this insight's own risk note about over-gating.
