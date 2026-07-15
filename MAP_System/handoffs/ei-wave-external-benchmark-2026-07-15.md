# Handoff: E/I Wave — External Benchmark + Business-Model Research (2026-07-15)

- Lead: gune (orchestrator)
- Helper: soho (Haiku, tag ei-report) — authoring the report + taxonomy files
- Type: E/I (Emergence/Insight) research wave, operator-requested

## Goal

Benchmark MAP against best-in-class 2026 multi-agent systems and against
innovator business-model philosophy, then turn findings into durable emergence
records and (recommended) tasks — orchestrated, with file-heavy authoring
delegated to a lower-model helper.

## What's been done

- Research (gune, WebSearch): 2026 framework landscape (LangGraph/CrewAI/
  AutoGen/Agents SDK), the "5 orchestration patterns that work," agent
  observability/eval state, and Amazon working-backwards / two-pizza / Day-1
  philosophy. Sources captured in the report packet.
- Emergence records created (gune):
  - INS-0022 — MAP = supervisor + durable-blackboard + swarm hybrid; durability
    + mechanical gates are the real differentiator vs ephemeral-state frameworks.
  - INS-0023 — MAP is building inward without a working-backwards proving
    workflow; the OPEN backlog item "decide first real general workflow target"
    is the Day-1 risk.
  - IDEA-0018 — three-layer eval discipline + agent-incident taxonomy.
  - IDEA-0019 — promote `debate` to a first-class review/decision mode (hcom
    already ships `hcom run debate`).
  - IDEA-0020 — two-pizza per-agent ownership metrics in map_metrics.py + UI.
  - `emergence/INDEX.md` rebuilt.
- Work packet written: `inbox/helpers/ei-external-benchmark-report-packet.md`
  (carries the full synthesis; helper formats it into two files).
- Helper soho spawned to author:
  - `artifacts/reports/ei-external-benchmark-2026-07-15.md`
  - `notes/agent-incident-taxonomy.md`

## Next (recommended, ranked)

1. Working-backwards PR/FAQ to pick MAP's first real proving workflow — closes
   the standing OPEN `improvement-backlog.md` item. Highest leverage; needs an
   operator/core-agent decision, so route through HPOM, not a solo task.
2. Promote IDEA-0019 (debate mode) — lowest cost, existing hcom workflow; good
   first promotion via the standard promotion gate.
3. Formalize IDEA-0018 eval discipline starting from the incident-taxonomy note.
4. Pilot IDEA-0020 two-pizza metrics in map_metrics.py.

## Follow-on: IDEA-0019 promoted (operator "go for it", 2026-07-15)

- PROMO-0009 created and APPROVED (decision owner: operator; direction approved,
  deliverable review routed to a separate core agent per no-self-promotion).
- TASK-204 created (READY, HPOM-complete): "Optional debate pre-escalation step
  for conflict-freeze / decision-authority path." Doc + convention only,
  additive/opt-in; files_in_scope = DECISION_AUTHORITY_SYSTEM.md +
  notes/review-guide.md; flag_conflict.py untouched.
- IDEA-0019 → PROMOTED_TO_TASK; emergence index rebuilt, validate clean (54).
- Implementer packet: inbox/helpers/task-204-debate-preescalation-implementer.md
  (verbatim text blocks). Dispatched to helper soho.
- soho drafted both edits (verbatim, in-scope, flag_conflict.py untouched);
  gune verified. gune claimed+submitted TASK-204 (now SUBMITTED); mirrors
  resynced via the exporter.
- claude-lab-toku claimed + APPROVED (review: artifacts/reviews/task204-review-toku.md;
  all 3 criteria pass, flag_conflict.py empty diff). gune released TASK-204
  (checklist: artifacts/releases/task-204-release-checklist.md). Status: RELEASED.
- One cosmetic reviewer note (DAS last_verified header not bumped) — non-blocking,
  file not gated; left as-is to keep released artifact == reviewed artifact.
- No commits/pushes (operator names pushes explicitly). Uncommitted working tree
  now carries this wave's records + TASK-204 docs, alongside other agents'
  in-flight files.

## Follow-on 2: MAP's first proving workflow chosen (DEC-028)

- Ran the working-backwards exercise (INS-0023 → brief at
  `artifacts/planning/working-backwards-proving-workflow-2026-07-15.md`): 3
  candidate proving workflows as mini PR/FAQs + recommendation.
- Operator selected **Software delivery** as MAP's first STANDING proving
  workflow. Recorded as **DEC-028** (validators green); resolved the standing
  `shared/unresolved-questions.md` item; brief marked DECIDED.
- First slice = **TASK-205** (READY, owner codex-lab-nivo): full-fidelity JSON
  backup Export/Import for ProjectUpdater — completes IDEA-0015's deferred
  import half and closes the registered localStorage data-loss risk. Surfaced
  the real subtlety that the existing "Export status" is lossy and can't
  restore, so the task builds a separate full-backup pair.
- Packet: `inbox/helpers/task-205-projectupdater-backup-implementer.md`.
  Dispatched to codex-lab-nivo (Codex = implementation per capability matrix);
  a Claude core agent reviews (cross-model, not gune, not the implementer).
- SHIPPED: nivo implemented → zera independently reviewed (from-scratch Node/vm
  harness, byte-identical round-trip on all 8 previously-lossy fields + malformed
  /wrong-shape edge cases) → APPROVED (artifacts/reviews/task205-review-zera.md)
  → gune released (artifacts/releases/task-205-release-checklist.md).
  **TASK-205 RELEASED.** First software-delivery feature shipped end-to-end;
  IDEA-0015 fully closed (export TASK-136 + import TASK-205).

## Status — E/I research wave COMPLETE; TASK-204 RELEASED; DEC-028 set; TASK-205 IN FLIGHT

- soho authored both files; gune reviewed and accepted them (fixed one
  packet-internal "(FILE 2)" leak in the report). Emergence validate clean
  (53 checked). Wave deliverables done.
- No commits/pushes (operator must name pushes explicitly per session rule).
- Next E/I step queued: promote IDEA-0019 (debate mode) through the standard
  promotion gate — lowest-cost, existing hcom workflow.
