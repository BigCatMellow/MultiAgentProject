# Source Mining Audit: Guidelines/6.13 + repo/ Downloads vs Implemented MAP State

- Date: 2026-07-14
- Auditor: claude-lab-toku (read-only recon helper)
- Owner: claude-lab-mira
- Directive: find value in `Guidelines/6.13/` and `repo/` not yet implemented or deliberately closed.
- Method: every concept cross-checked against `shared/current-state.md`, TASK-147..186 records, `*_SYSTEM.md` docs, `scripts/`, `tests/`, and the prior audits (`repo-reference-map-runtime-audit.md` TASK-171, `local-repo-drop-survey-2026-07-14.md`, `map-613-master-implementation-plan.md`).
- Statuses: IMPLEMENTED / CLOSED (deliberately, with a recorded decision) / PARTIAL / UNEXPLOITED. Next steps sized S/M/L, only for PARTIAL/UNEXPLOITED.
- Note: TASK-184 (intake-as-default), TASK-185 (map_repair CLI), TASK-186 (RnS suppression) are IN_PROGRESS and excluded from proposals.

## A. Guidelines/6.13 core corpus

| source | concept | status | evidence path | next step |
|---|---|---|---|---|
| MAP-System/00-11 + Thesis/Synthesized-System docs | Core doctrine (shared-state coordination, eager halt, single entry, validator split, resilience layer) | IMPLEMENTED | Synthesized into `artifacts/planning/map-613-master-implementation-plan.md`; built as TASK-147..163 (`scripts/halt_state.py`, `command_center_intake.py`, `resilience_controls.py`, etc.) | — |
| MAP-Gap-Register.md §3.1 | **Calibrate driving parameters on the real repo** ("THE highest-value gap") | PARTIAL | Plan only: `artifacts/audits/map-real-parameter-calibration.md` says "this is the measurement plan, not the measurement itself." Only compression ratio/churn measured (TASK-174: `map-library-viability-measurement-results-2026-07-14.md`). Defect-vs-false-halt cost, local-vs-cloud defect rate, misattribution rate, latency, operator load: unmeasured | Run the remaining measurements now that trace/event infra (TASK-170) exists (M) |
| MAP-Gap-Register.md §2a | Semantic validator spec + measured false-positive rate | PARTIAL | Spec: `artifacts/planning/map-semantic-validator-spec.md` (TASK-152); L1 wiring + halt store implemented (TASK-162, `scripts/validate_layer1.py`, `halt_state.py`). L2 fuzzy-judge false-positive measurement never run | Blocked on calibration data; fold into the calibration run (M) |
| MAP-Gap-Register.md §2b | Decomposer specified + tested | PARTIAL | Spec: `artifacts/planning/map-decomposer-spec.md` (TASK-147); intake classification implemented (`scripts/command_center_intake.py`, `intake_request.py`, `tests/test_runner_task_classification.py`); full intent→subtasks-with-edges decomposition not mechanized | Acceptable as-is while intake-as-default (TASK-184) lands; revisit after (—) |
| MAP-Gap-Register.md §3.2 | Committed poisoned-state recovery | IMPLEMENTED | `SELF_REPAIR_SYSTEM.md`, chaos probe for poisoned state (`tests/test_chaos_resilience.py`, TASK-161), `scripts/map_repair.py` (TASK-185 in progress) | — |
| MAP-Gap-Register.md §3.4 | Threat model | IMPLEMENTED | `artifacts/audits/map-threat-model.md` (TASK-156), `SECURITY_PERMISSIONS_SYSTEM.md` | — |
| MAP-Gap-Register.md §3.7/3.8 | Multi-project readiness, roster composition | IMPLEMENTED | `artifacts/audits/map-multi-project-readiness.md`, `map-roster-composition.md` (TASK-157) | — |
| MAP-Gap-Register.md meta-hole | External red-team of assumptions | IMPLEMENTED | `artifacts/audits/map-613-assumption-red-team.md` (TASK-157) | — |
| MAP-Extension-Plan.md #1 | Cost governance + kill switch | IMPLEMENTED | `scripts/cost_governance.py`, `tests/test_cost_governance.py` (TASK-151/159) | — |
| MAP-Extension-Plan.md #2 | **Outcome feedback** (outcome event type, validator blind-spot rate; "the single most important addition") | UNEXPLOITED (spec only) | Spec exists: `artifacts/planning/map-outcome-feedback-spec.md` (TASK-154), self-declared "design artifact only." No outcome event type in `events/events.jsonl`, no code in `scripts/` handles outcomes, no blind-spot metric in `map_metrics.py` | Implement outcome_pass/outcome_fail event + blind-spot metric per the existing spec (M) |
| MAP-Extension-Plan.md #3 | Dependency DAG + cycle detection | IMPLEMENTED | `workflow/task_graph.json` tasks carry `dependencies`; `scripts/validate_task_graph.py` `detect_cycle()` | — |
| MAP-Extension-Plan.md #4 | Durable/resumable execution | IMPLEMENTED | `scripts/durable_execution.py`, `tests/test_durable_execution.py` (TASK-161) | — |
| MAP-Extension-Plan.md #5 | Heartbeats/liveness reaper | IMPLEMENTED | `scripts/liveness_reaper.py` (TASK-150/158/177), `tests/test_liveness_reaper.py` | — |
| MAP-Extension-Plan.md #6 | Degradation policy (decision table + enforcement at dispatch) | PARTIAL | Table exists: `artifacts/planning/map-degradation-policy.md` (TASK-155). Validator fail-closed is enforced via halt state; but no dispatch-point code references the other policy rows (grep "degrad/fail_open/fail_closed" over `scripts/` is empty outside the doc) | Wire remaining policy rows (cloud-down, store-locked, operator-absent) into `pre_dispatch_policy.py` when those paths become real (S/M, low urgency) |
| MAP-Simulation-TestDrive.md | Probe 2: validator can actually halt dispatch | IMPLEMENTED | `tests/test_halt_state.py`, `test_runner_policy_gate.py` (TASK-162) | — |
| MAP-Simulation-TestDrive.md | Probe 1: measure shared-state vs point-to-point-relay coordination on real tasks | UNEXPLOITED | No measurement artifact; master plan Wave 2.6 listed it; nothing in `artifacts/audits/` measures it | One-shot audit over `events/events.jsonl` + hcom transcripts for a sample of released tasks (S) |
| files/ files2/ files4-6/ files8/ (map_v1-7.py, chaos.py, breaker_fair.py, knowledge_layer.py, emergence_dynamics2.py, sensitivity.py, diagnose_v1.py) | Simulation prototypes + results rounds 1-6 | CLOSED (harvested) | Conclusions extracted into the master plan's "Corrections From Synthesized And Simulation Docs" and Gap-Register buckets; the code is throwaway model-of-MAP, not MAP | — |
| files8/ + master plan Wave 2.5 | Sensitivity/robustness grading: method **plus a first grading report** | PARTIAL | Method exists: `artifacts/audits/map-sensitivity-robustness-method.md` (TASK-149). No graded report exists (no conclusion labeled robust/conditional/unsupported anywhere in `artifacts/audits/`) | Produce first grading report as part of the calibration run (S, bundled) |
| files7/ MAP-Validator-Specification.md + validator_design.py | Two-layer validator design | IMPLEMENTED | `artifacts/planning/map-semantic-validator-spec.md`, `map-protocol-validator-spec.md`, `scripts/validate_protocol.py`, `validate_layer1.py` (TASK-152/162) | — |
| files3/ MAP-Tool-Evaluation-Appendix.md | LLMLingua "study first / strongest candidate" for MATOCP; DSPy for emergence/validator prompts; LangFuse vs hand-rolled tracing | UNEXPLOITED (LLMLingua, DSPy) / CLOSED (LangFuse) | Zero mentions of LLMLingua or DSPy anywhere in `MAP_System/` (grep). LangFuse alternative closed in practice: MAP hand-rolled `scripts/event_trace.py` + `session_replay.py` (TASK-170/172/173) | LLMLingua/DSPy study only if the Library pilot or L2 validator calibration proceeds; note in backlog, don't start now (M, gated) |
| Claude Notes (chat transcript) | Landscape framing: orchestration is commodity; MAP's value is correctness-under-concurrency plumbing | CLOSED (absorbed) | Same conclusion recorded in Tool-Evaluation-Appendix Cluster 3 and reflected in DEC posture (no framework adoption); no distinct untaken concept | — |
| MAP-Repo-Review-List.md priority reads #1 | claude-bedrock + agentcairn as librarian blueprints | IMPLEMENTED | Evaluated (BRIEF/SUMMARY-0002, TASK-154; confirmed on real source in `local-repo-drop-survey-2026-07-14.md`); librarian built: `scripts/librarian.py`, 118 wikilinks, backlink index (TASK-174/179) | — |
| MAP-Repo-Review-List.md #2 | RKAG hop-limit + token-budget-cap traversal pattern | UNEXPLOITED (deliberately parked) | SUMMARY-0002: "keep the pattern... until rechecked"; `librarian.py` has no traversal budget yet (backlink index is flat, no multi-hop) | Apply hop/token caps only when librarian grows graph traversal (S, gated) |
| MAP-Repo-Review-List.md #3, #4 | agent-collab-skills acceptance-gate comparison; codexia worktree/locking lessons | UNEXPLOITED | Listed as open questions in SUMMARY-0002 ("Does agent-collab-skills acceptance-gate structure catch defects MAP's gates don't?"); neither repo is in `repo/` downloads (only a `.desktop` shortcut for WenyuChiou) | Optional S study each; low value — MAP's gate stack is already deeper |

## B. repo/ downloads

Prior coverage: TASK-171 (`artifacts/audits/repo-reference-map-runtime-audit.md`) audited the runtime cluster; zera's survey (`artifacts/reports/local-repo-drop-survey-2026-07-14.md`) covered the wikilink/knowledge cluster. This table tracks what MAP actually took vs what remains.

| source | concept | status | evidence path | next step |
|---|---|---|---|---|
| agents-observe-main | Session replay read model from event logs (TASK-171 Priority 1) | IMPLEMENTED | `artifacts/designs/session-replay-read-model-design.md` (TASK-172), `scripts/session_replay.py` + `tests/test_session_replay.py` (TASK-173) | — |
| codeburn-main | **Cost/yield rollup**: "what did this task cost and did it produce released work?" (TASK-171 Priority 2) | UNEXPLOITED | `scripts/cost_governance.py` is dispatch-budget/kill-switch only — no per-task cost rollup, no productive/abandoned-spend split, no cost-by-released-output view (grep "rollup/yield/per-task" empty). No follow-on task exists in TASK-172..186 | Extend `cost_governance.py`/`map_metrics.py` with cost-by-task × task-outcome join, using codeburn's category vocabulary (`repo/codeburn-main/src/yield.ts`) as reference (M) |
| headroom-main, caveman-main | Library-layer viability measurement before building compression (TASK-171 Priority 3) | IMPLEMENTED (measured, verdict: don't build yet) | `artifacts/audits/map-library-viability-measurement-results-2026-07-14.md` (TASK-174): "Do not proceed to building the full Library layer yet"; recommends a bounded pilot (option b) as next step if operator wants it | Operator-gated: 3-5 doc pilot with logged full-source opens, per the results file's own recommendation (M, gated) |
| EverOS-main / MemOS-main / Memori-main / mem0-main | Markdown-source-of-truth + disposable derived index (TASK-171 Priority 4: MAP memory index design) | PARTIAL | The architectural shape already exists (SQLite-canonical + file mirrors; librarian backlink index is disposable/rebuildable). A dedicated "MAP memory index" design task was never created; TASK-171 marked it Priority 4 | Defer; current mirrors + librarian cover the load-bearing part. Revisit only if Library pilot proceeds (—) |
| haystack-main, MetaGPT-main | Pipeline components/snapshots/breakpoints; role frameworks | CLOSED | TASK-171 verdict: borrow only if runner complexity grows; MetaGPT "do not adopt" — consistent with DEC posture and TASK-145 LangGraph research | — |
| impeccable-main, universal/, awesome-claude-code-main | Cross-provider skill/plugin packaging; curated catalog model | CLOSED (deferred) | TASK-171: "Defer. When MAP has a stable installable collaboration system..." — deliberate | — |
| agentcairn-main | **Redaction before every write** (regex + entropy + URL-credential scrubbing) | UNEXPLOITED | zera's survey flagged it explicitly: "MAP has no equivalent anywhere in its emergence/event-capture path... worth flagging as a security gap." Confirmed: grep "redact/entropy" over `scripts/` is empty; not in `map-threat-model.md` mitigations either | Small redaction check (secrets/credential patterns) callable from `map_emergence.py`, `map_repair.py`, and event appends; reference `repo/agentcairn-main` scrubbing rules (S/M) |
| agentcairn-main | Reproducible benchmark harness with caveats | CLOSED (noted) | Survey: worth reading "if the Library layer is ever built" — gated on the same operator decision | — |
| callimachus-main | **Decision-conflict detection** ("Review conflicts" pass flagging contradicting decisions) | UNEXPLOITED | `scripts/validate_decisions.py` checks required fields/index only, not contradictions; survey called it "a striking precedent." Nothing in TASK-172..186 picked it up | Add a supersession/contradiction pass over `shared/decisions.md` + DECISIONS index (flag decisions touching the same subject where neither supersedes the other) (M) |
| callimachus-main | Thread-to-commit linking (file-overlap + time-window, no LLM) | UNEXPLOITED | Session replay (TASK-173) joins events/tasks/traces but not git commits; trace_id tagging is manual | Optional enrichment of `session_replay.py` with commit linking (M, low priority) |
| graphify-8 / graphifyy whl | **EXTRACTED vs INFERRED provenance tag on individual claims** | UNEXPLOITED | Survey: "a clean, adoptable idea for MAP's own emergence system... doesn't tag individual claims by provenance." Emergence templates (`templates/`, `map_emergence.py`) have no claim-level provenance field | Add optional `provenance: extracted|inferred` label to emergence record templates (S) |
| claude-bedrock-main | Librarian blueprint (single write point, healthcheck, dedup/compress) | IMPLEMENTED (as precedent) | SUMMARY-0002 + survey; MAP librarian (TASK-174) took the wikilink/validation/backlink core; single-write-point equivalent is `map_emergence.py`/`map_repair.py` CLIs | — |
| claude-code-memory-setup-main | Obsidian + Graphify combo setup | CLOSED (skimmed, TASK-196, confirmed nil) | See "claude-code-memory-setup-main Skim (TASK-196)" section below | — |
| headroom.js / react-headroom / svelte-headroom, Callimachus .deb, WenyuChiou .desktop | Name-collision UI libraries, binary packages, browser shortcut | CLOSED (noise) | TASK-171 Inventory Notes: unrelated to Headroom AI; packages retained as reference only | — |

## C. Gap review + command-center-later open items

| source | item | status | evidence path | next step |
|---|---|---|---|---|
| Guidelines/MAP_repo_systems_gap_review.md | (pointer file) full systems gap review | IMPLEMENTED | `artifacts/reports/MAP-repo-systems-gap-review.md`; `shared/current-state.md`: "all priority and secondary gaps now built" (TASK-103..118, DEC-015..025) | — |
| notes/command-center-later.md | Git baseline (uncommitted HPOM sprint) | CLOSED (overtaken) | Regular commits now exist (git log: 5ab8728, 92b186d, ... ; DEC-014 canonical repo) | — |
| notes/command-center-later.md | **First real workflow target** decision | UNEXPLOITED (operator decision) | Still open in `shared/unresolved-questions.md` line 17 and `shared/improvement-backlog.md` ("Decide first real general MAP workflow target") | Put the question to the operator with a recommendation; MAP keeps accumulating infrastructure without a proving workflow (S to decide, L to run) |
| notes/command-center-later.md | Single session-resume runbook | IMPLEMENTED | `notes/operations-runbook.md` | — |
| notes/command-center-later.md | Task JSON schema validation | PARTIAL | `promote_task.py` validates 8 HPOM fields; no structural schema validator for `tasks/TASK-NNN.json` (no jsonschema usage in `scripts/`) | Small schema check appended to `validate_task_mirrors.py` or standalone (S) |
| notes/command-center-later.md | Artifact naming consistency (taskNNN vs task-NNN) | UNEXPLOITED (cosmetic) | `artifacts/reviews/` still mixes patterns (e.g. `task171-review-zera.md` vs `task-182-release-checklist.md`) | Fold into next artifacts-directory review; not standalone-task-worthy (S) |
| artifacts/audits/map-failure-taxonomy-coverage.md | 7 named missing regression tests | PARTIAL | #1 covered (`tests/test_capability_whitelist.py`); #2/#3 substantially covered by `test_chaos_resilience.py` + `test_durable_execution.py`; **#4 decomposer dependency-edge cases, #5 context-summary drift, #6 multi-project isolation: no test files exist**; #7 deliberately gated on write-control decision (TASK-168) | Add tests #4-#6 (S each) |

## Ranked Top-5 Worth Doing Next

1. **Run the real-parameter calibration + first robustness grading** (A: Gap-Register §3.1 + Wave 2.5) — the corpus's own #1-ranked gap; plan and method artifacts already exist, trace infra landed (TASK-170), and every eager-halt/validator/routing conclusion stays "conditional" until it runs. (M)
2. **Implement outcome feedback** (A: Extension-Plan #2) — the one component the 6.13 corpus calls architectural and anti-gaming; the spec is finished and explicitly says implementation is follow-on work that never happened. Small event-type + metric change, closes the loop with #1's blind-spot measurement. (M)
3. **Cost/yield rollup** (B: codeburn, TASK-171 Priority 2) — the only TASK-171 priority (1-4) with no follow-on at all; converts existing cost-governance + event/task data into "what did this cost and did it ship," which the operator directly benefits from. (M)
4. **Redaction guard for capture pipelines** (B: agentcairn) — flagged as a real security gap by the zera survey and confirmed absent; cheap, bounded, and increasingly relevant as emergence/repair CLIs (TASK-185) become the default write paths. (S/M)
5. **Close the three missing regression tests** (C: taxonomy audit #4-#6) — MAP's own audit named them highest-value; each is small and two of them (multi-project isolation, context drift) guard areas the Gap Register calls the weakest. (S)

Operator-decision honorable mentions (not agent-startable): pick the first real workflow target (the oldest open strategic item in the corpus), and approve/decline the bounded Library pilot that the viability measurement itself recommends as the next step.

## claude-code-memory-setup-main Skim (TASK-196)

Closure of the one `repo/` item neither the TASK-171 runtime audit nor the
zera knowledge-cluster survey covered. Files inspected: `README.md` (table
of contents, Problem/Solution framing, savings tables, "Real Results" and
"Architecture" sections), `README.pt-BR.md` (confirmed a translation, not
independent content), `scripts/claude_to_obsidian.py` (chat-import →
Obsidian-note pipeline: frontmatter, keyword-to-tag mapping, wikilink
insertion), `scripts/sync_claude_obsidian.sh` (cron-driven wrapper calling
`claude-extract` + the Python script).

**Conclusion: nil marginal value for MAP, confirmed.** This is a setup guide
and two glue scripts for wiring `claude-conversation-extractor` + Obsidian +
Graphify + `/resume`/`/save` slash commands into a *single-operator, no-
harness* Claude Code workflow — a personal second-brain recipe, not a
library or pattern MAP doesn't already have a stronger version of:

- The Obsidian-vault-as-memory pattern is the same one `claude-bedrock-main`
  and `agentcairn-main` demonstrate more directly (TASK-171/SUMMARY-0002),
  and MAP's own `librarian.py` (TASK-174/179) already implements the
  wikilink/backlink mechanics natively against MAP's own Markdown, with no
  external vault or Obsidian dependency.
- The chat-import pipeline solves "insights lost in chat history" for a
  single human using the Claude Code app directly; MAP's equivalent problem
  (coordination history across many agents) is already covered more
  precisely by `session_replay.py` (TASK-172/173), which indexes MAP's own
  hcom/event/task sources rather than parsing chat exports.
- Graphify is separately covered (and already evaluated) in the TASK-171
  audit's Priority-adjacent notes and the zera survey's EXTRACTED/INFERRED
  provenance-tag finding (source-mining audit section A); this repo adds no
  new information about Graphify itself, only a personal setup wrapper
  around it.
- The 71.5x/499x token-savings claims are self-reported, single-project
  benchmarks (React+Supabase, 126 files) with no methodology beyond a
  results table — consistent with `MAP-Repo-Review-List.md`'s own warning
  that "token-savings percentages... are self-reported" and not something to
  import as evidence.

No further action. This closes the last unaudited `repo/` download; the
source-mining audit's coverage of `repo/` is now complete.
