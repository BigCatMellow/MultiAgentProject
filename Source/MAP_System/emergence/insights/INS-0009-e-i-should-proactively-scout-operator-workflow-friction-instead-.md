# Insight Record

Insight ID: INS-0009
Project: MAP
Related task: TASK-093
Detected by: codex-lab-lema
Date: 2026-07-02
Status: LINKED

## Short description

- obs: E/I should proactively scout operator workflow friction instead of waiting for the operator to name obvious CommandCenterUI affordances

## Trigger

- src: Operator said quote/reply, attention inbox, approvals, and auto-mode are exactly the kind of things the Emergence/Insight layer should think about without being prompted.

## The synthesis

- synth: E/I should proactively scout operator workflow friction instead of waiting for the operator to name obvious CommandCenterUI affordances

## Why it might matter

- why: The system's purpose is to reduce operator orchestration burden. If agents only convert explicit operator requests into tasks, the discovery layer is not doing its job.

## Evidence

- ev: The operator had to ask for chat replies, needs-attention inbox, approval controls, and auto-mode explanation after several CommandCenterUI tasks had already exposed the need for conversation ergonomics and approval routing.

## Risk

- risk: Unbounded proactive work could create scope creep or unsafe automation; findings must remain candidates until shaped into HPOM tasks or explicit operator decisions.

## Scope

- scope: Capture recurring operator-friction patterns and propose bounded UI/process improvements.

## Recommended next action

- [ ] Ignore — not worth preserving
- [ ] Park for later — valid but low priority
- [ ] Create follow-up task — actionable now
- [x] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

- Follow-up idea: IDEA-0010.
