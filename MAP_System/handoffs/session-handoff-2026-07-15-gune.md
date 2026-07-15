# Session Handoff — 2026-07-15 (gune, orchestrator)

Clean top-level "where are we." Detailed running log lives in
`handoffs/ei-wave-external-benchmark-2026-07-15.md`.

## Done this session

1. **E/I external benchmark wave.** Researched the 2026 multi-agent landscape +
   innovator business-model philosophy. Captured 5 emergence records
   (INS-0022/0023, IDEA-0018/0019/0020); authored
   `artifacts/reports/ei-external-benchmark-2026-07-15.md` and
   `notes/agent-incident-taxonomy.md` (helper: soho).
   - Core finding: MAP's durable-blackboard + mechanical gates are a real edge
     vs 2026 frameworks, but MAP had been building inward with no real
     deliverable flowing through the gates.

2. **TASK-204 RELEASED** — optional `hcom run debate` pre-escalation step for the
   conflict-freeze / decision-authority path (promoted IDEA-0019 via PROMO-0009).
   Doc-only, opt-in, non-breaking. Built by soho, reviewed by claude-lab-toku.

3. **DEC-028 — chose MAP's first standing proving workflow: SOFTWARE DELIVERY.**
   Ran a working-backwards exercise
   (`artifacts/planning/working-backwards-proving-workflow-2026-07-15.md`);
   operator selected software delivery. Resolved the long-standing
   `shared/unresolved-questions.md` item.

4. **TASK-205 RELEASED** — first software-delivery feature: full-fidelity JSON
   backup Export/Import for ProjectUpdater (completes IDEA-0015's deferred import
   half; closes the localStorage data-loss risk). Built by codex-lab-nivo,
   independently reviewed by claude-lab-zera (from-scratch harness, byte-identical
   round-trip + malformed-input edge cases). IDEA-0015 closed out.

## Where we are now

- **Two tasks RELEASED** (204, 205). All gates green: task mirrors, shared state
  (22 files), decisions (28), emergence (54 artifacts).
- **The software-delivery proving workflow (DEC-028) is live and proven
  end-to-end** — the Codex-build / Claude-review / gune-release cadence works.
- **Working tree is uncommitted and NOT pushed.** It carries this session's
  records + TASK-204/205 outputs alongside other agents' in-flight files
  (halt-authority window, etc.). Pushing is operator-named only.
- Latest MAP task ID is **TASK-205**.

## What's left / next moves

- **Commit + push** (operator must name it explicitly — the harness blocks broad
  autonomous pushes). This session's work is release-gated but not yet in git
  history.
- **Software-delivery track (DEC-028): build a real feature queue.** ProjectUpdater
  is the current proving vehicle; pick the next real feature(s) and run them
  through the same cadence. Candidate sources: ProjectUpdater `ideas/` and
  `risks/RISK_REGISTER.md`.
- **Optional second track:** the recurring "MAP Intelligence Brief" (research
  product) — candidate B from the working-backwards brief; lowest-risk, compounds.
- **Open emergence ideas not yet promoted:** IDEA-0018 (three-layer eval
  discipline; seed = `notes/agent-incident-taxonomy.md`), IDEA-0020 (two-pizza
  per-agent ownership metrics). Both CANDIDATE; promote via the standard gate
  when ready.
- **Housekeeping already tracked:** RnS watcher follow-ups and the
  limit-watcher-state 10 open incidents (IDEA-0009 dry-run suppression
  experiment, EXP-0001) remain in `improvement-backlog.md` / current-state.

## Operating notes for whoever continues

- Orchestrator pattern held: lead does research/design/promotion/verification/
  release; helpers (Haiku) and core agents (Codex implement, Claude review) do
  file work; reviewer is always a different core agent than the owner
  (no-self-review gate enforces it).
- For claim/liveness questions read `map.db` directly, not the file mirrors
  (they export-lag). If you bypass `map_task.py` for status transitions, resync
  mirrors with `migration/export_to_files.py --db <abs path>/MAP_System/map.db`.
