# MAP Real-Parameter Calibration — Results (Batch 1, 2026-07-14)

- Task: TASK-188
- Owner: claude-lab-toku
- Method reference: `map-real-parameter-calibration.md` [[map-real-parameter-calibration]] (TASK-149 plan)
- Companion: `map-robustness-grading-2026-07-14.md` [[map-robustness-grading-2026-07-14]]
- Data window: 2026-06-17 → 2026-07-14 (all of MAP's recorded history)
- Data sources: `events/events.jsonl` (1,074 events, 180 tasks), `map.db` (180 task rows, 60 release records), hcom event stream (4,748 message events), git history (24 commits), `emergence/` records (all), `shared/halt-state.json`, TASK-174/TASK-181 reports
- Rule honored: no simulated substitutes. Every number below is from real repo data; every unmeasurable parameter is marked with exactly what data is missing.

## Summary Table

| # | Parameter | Status | Result |
|---|---|---|---|
| 1 | Compression ratio | MEASURED (TASK-174, imported) | 22.65x median extractive floor; detail-needed rate still unmeasured |
| 2 | File churn rate | MEASURED (two proxies) | Bursty, currently low: 5 shared/system write-events in the latest ISO week vs 107 in the week-27 sprint |
| 3 | Emergence misattribution rate | MEASURED (small N) | 0/15 promoted records misattributed (0%); 3 lifecycle-noise records are ceremony errors, not misattribution |
| 4 | Shipped-defect vs false-halt cost ratio | HALF-MEASURED | Defect side: 3 real shipped defects, fix spans 1.9–14 min. False-halt side: zero observations — no halt has ever been set |
| 5 | Local-vs-cloud defect rate | INSUFFICIENT (one real batch) | TASK-181: 0/3 local-model outputs directly usable in the prose-rewrite lane; no rate computable |
| 6 | Wall-clock latency | MEASURED | Median task span 0.33 h; submission→approval median 4.8 min; approval→release long tail (p90 145 h, release batching) |
| 7 | Operator approval load | PARTIAL | ~15 operator-session messages/day across 15 active days; 4 recorded decisions, 1 formal approval gate; identity attribution uncertain |
| — | hcom volume vs shared state | MEASURED | 2,524 agent messages vs 1,074 durable state events ≈ 2.35 : 1 |

## 1. Compression ratio — MEASURED (imported from TASK-174)

Not re-run; TASK-174 measured it on 2026-07-14 against all 16 root system/policy
docs (`map-library-viability-measurement-results-2026-07-14.md`):

- Median 22.65x, p90 28.94x, worst-case 12.6x — using the cheapest extractive
  strategy (headings + first paragraph).
- TASK-174's own caveat stands: this is a floor measurement, not evidence the
  Library layer should be built; the **detail-needed rate is still unmeasured**
  and remains the blocking half of the Round-6 threshold.

## 2. File churn rate — MEASURED (with a stated baseline limitation)

Two proxies, because TASK-174 correctly noted git churn "needs a committed
baseline first" — MAP commits in batches (24 commits total, in ISO weeks 24,
26, 28), so git history under-resolves real write activity.

**Proxy A — git file-touches (all history, ~4 weeks):** `shared/` 46,
`notes/` 42, root `*_SYSTEM.md`+`AGENTS.md` 16. Most-committed:
`shared/current-state.md` (7 of 24 commits), `shared/decisions.md` (6).

**Proxy B — event-recorded artifact writes per ISO week** (finer-grained;
`artifact_paths` on events):

| ISO week | shared/ | notes/ | system docs |
|---|---|---|---|
| 25 | 14 | 0 | 0 |
| 27 (6.13 build sprint) | 67 | 18 | 26 |
| 29 (current) | 4 | 0 | 1 |

Most-touched files: `shared/decisions.md` (36 write-events),
`shared/current-state.md` (12), `shared/requirements.md` (10).

**Reading:** churn is sprint-bursty, not steady. Outside build sprints the
active-doc corpus changes a few times a week, concentrated in 2-3 files.
Per Round 6's rule ("Library layer pays only when compression is high AND
churn is not low"), current steady-state churn is **low**.

## 3. Emergence misattribution rate — MEASURED, 0/15 (small N, manual adjudication)

Method: every promoted emergence unit (9 promoted ideas + 6 approved
promotions = 15) was cross-referenced against all 36 tasks that ever received
`CHANGES_REQUESTED`, then each linked rework's recorded reason was read.

- **0 of 15 promoted records were attributed to a wrong root cause.** Every
  rework touching a promoted item (TASK-056, TASK-080/083/084, TASK-123,
  TASK-129, TASK-146) was an implementation-level review finding (e.g.
  "silent-stop detection skips empty successful hcom list"), not a wrong
  diagnosis in the emergence record itself.
- 3 lifecycle-noise records exist but are not misattribution: PROMO-0002/0003
  (WITHDRAWN — template-placeholder ceremony errors, `IDEA-####` never filled
  in) and IDEA-0008 (SUPERSEDED — concurrent duplicate of IDEA-0007 from the
  same operator prompt).
- No promoted change has ever been reverted.

**Against the Round-6 threshold (~20% ⇒ build the pruning guard): observed 0%
is far below it.** Caveats: N=15 is small; adjudication was a manual read, not
outcome-event automation (outcome feedback is still unimplemented — see
`source-mining-audit-2026-07-14.md` item #2); records younger than a few weeks
have had little time to fail.

## 4. Shipped-defect vs false-halt cost ratio — HALF-MEASURED

**Defect side (numerator) — now real.** Three defects shipped past release
and were fixed in follow-up tasks:

| Defect | Fixed by | Recorded fix span (first→last task event) |
|---|---|---|
| `liveness_reaper.py` rejected raw `hcom list --json` shape (TASK-158 released work) | TASK-177 | 1.9 min |
| `librarian.py` wikilink path resolution (TASK-174 released work) | TASK-179 | 2.6 min |
| `aider_wrapper.py` forbade the safety flag `--no-auto-commits` (TASK-049) | TASK-050 | 14 min |

Fix spans exclude discovery cost (the defects were found during later audits,
not by validators), so these are lower bounds — but the order of magnitude is
minutes-to-tens-of-minutes of agent time, not days.

**False-halt side (denominator) — zero observations, structurally.**
`shared/halt-state.json` has never been set (`set_at: null`, state `clear`
since creation). This is by design: `validate_layer1.py`'s shipped default
"never calls set_halt; it is telemetry only" and `validate_protocol.py` "ships
with severity capped at DRIFT (telemetry-only, no halt-store write)". The
adjudication field (`true_positive`/`false_positive`/`waived`) exists in the
protocol validator's output but no adjudicated telemetry has accumulated.

**Verdict: the 8:1 assumed ratio remains unmeasured — but the blocker has
changed.** The TASK-149 plan marked this blocked-on-Wave-4; Wave 4 has since
shipped (TASK-162). The missing data is now **operational**: a period of
validators running with halt authority (or at least adjudicated telemetry)
plus continued shipped-defect tracking. No simulated substitute is offered.

## 5. Local-vs-cloud defect rate — INSUFFICIENT DATA (one real batch)

No `task_tier`/`local_lane` fields exist on task records (classification lives
only in intake packets) and no outcome events exist, so no defect **rate** by
lane is computable. The only real observation is TASK-181's bounded trial
(`emergence-local-librarian-report.md`): 3 local models attempted the
emergence prose-rewrite lane — gemma3-4b rejected (drifted, terminal
artifacts), qwen2.5-coder:3b failed (180 s timeout, no output), llama3.2:1b
partially useful (section grouping kept as a cue only). **0/3 directly
applicable**; the same work was completed deterministically by
`map_emergence.py compact` (TASK-183) instead.

**Missing data, named:** task-lane metadata persisted on task records, outcome
events per lane, and enough local-lane task volume to form a denominator.

## 6. Wall-clock latency — MEASURED (Gap-Register Bucket 3.3, first-ever numbers)

From all 180 tasks' event chains (`task_id` grouping; trace_id coverage at 145
events is not yet sufficient to group by trace):

| Gate | n | median | mean | p90 | max |
|---|---|---|---|---|---|
| first event → submission | 156 | 0.11 h (6.6 min) | 1.28 h | 1.65 h | 82.6 h |
| submission → approval | 125 | 0.08 h (4.8 min) | 1.68 h | 0.50 h | 82.9 h |
| approval → release | 93 | 0.02 h | 26.6 h | 145.4 h | 230.3 h |
| total task span | 180 | 0.33 h | 21.0 h | 10.4 h | 330.7 h |

**Readings:**

- The review gate is **not** a bottleneck: half of all submissions are
  approved within 5 minutes; 90% within 30 minutes.
- The long tail lives almost entirely in **approval → release** (p90 145 h):
  releases are batched deliberately (release checklists are run in sweeps),
  not queued behind a bottleneck. The slowest total spans (TASK-001, 330 h)
  are early-era tasks left open across sessions, not orchestrator queueing.
- No evidence of the feared single-entry-point throughput bottleneck at
  current volume (~180 tasks/4 weeks, peak day 2026-07-14 with 1,316 hcom
  events) — but intake-as-default (TASK-184) is only now landing, so this
  measures the pre-single-entry era.

**Bonus: review-catch rate** (packet-requested): 36 of 156 submitted tasks
(23.1%) received at least one `CHANGES_REQUESTED` before eventually being
approved/released (36/36 recovered). Reviews are catching real defects
pre-release at roughly 1 in 4.3 submissions — see the grading report for why
this matters to the "universal peer review is net-negative" simulation cut.

## 7. Operator approval load — PARTIAL (identity attribution is the gap)

What the data supports:

- hcom messages attributable to the operator's command-center session: 224
  over 15 active days (~15/day). Messages under the `bigboss` identity: 1.
  **Caveat:** MAP has no durable convention mapping hcom identities to "the
  operator," so this is an upper-bound-ish proxy, not a clean count.
- Formal decision/approval surfaces: 4 `DECISION_RECORDED` events, 1 formal
  approval gate (`approval_gates`), 166 `APPROVED` events — the latter mostly
  executed by agents under `shared/approval-calibration.md` delegation, so
  they measure gate throughput, not operator attention.
- Operator-absence behavior: indirectly visible in
  `agents/limit-watcher-state.json`'s 10 open incidents for idle early-July
  sessions (windows where nudges went unanswered), but no gate has ever
  stalled awaiting operator approval per the event log.

**Missing data, named:** a durable operator-identity convention in hcom/event
records, and `needs_approval`-class events (Wave 3/8 emit them inconsistently
today). Until those exist, total attention load per Gap-Register Bucket 3.5
cannot be honestly computed.

## hcom volume vs shared-state (Principle 1 probe, TestDrive probe 1)

Same window: 4,748 hcom message events, of which 2,224 are `[hcom-events]`
system notifications → **2,524 agent-authored messages vs 1,074 durable
state events ≈ 2.35 : 1**.

Interpretation, honestly bounded: the simulation ideal ("zero point-to-point
messages needed") does not describe reality — agents coordinate socially over
hcom at more than twice the rate they write durable state. However, every
*lifecycle-critical* coordination (claims, gates, approvals, releases) is
mechanically enforced through shared state (SQLite + file mirrors + gate
scripts); hcom carries routing, acks, and review conversation. Classifying
messages by intent (request/inform/ack) per sender would sharpen this; the
current hcom event schema records intent inconsistently, so that split is not
reported rather than estimated.

## What Changed vs the Plan's Expectations

- Parameters 4/5 were "blocked on Wave 4/5/6 shipping." Waves 4/5 shipped;
  the blocker is now **telemetry accumulation and outcome events**, not
  missing code. Outcome feedback (spec'd, unimplemented) is the single
  highest-leverage unlock: it would convert parameters 3, 4, and 5 from
  manual/partial to automatic.
- Latency (parameter 6) and hcom volume were measured for the first time;
  neither shows the feared bottleneck at current scale.
- Misattribution (parameter 3) came in at 0/15 — far under the 20% pruning
  guard threshold (consequences in the grading report).

## Addendum (TASK-202): Measuring Parameter 7 And P1-Practice, Now Runnable

The original run (above) marked parameter 7 (operator approval load) PARTIAL
and the P1-practice grade Conditional, both citing the same missing data:
"no durable convention mapping hcom identities to 'the operator'" and
"the intent split... not recorded consistently." TASK-202 closed both gaps —
`shared/operator-identities.md` [[shared/operator-identities]] now names
`bigboss` and `command-center` as the two operator identities with concrete
evidence, and `notes/communication-architecture.md`'s new hcom-intent
section documents the live query path. Below are the concrete queries and a
smoke-test run against real current data.

### Parameter 7: Operator Approval Load

```bash
# Total operator-authored hcom messages, all history
hcom events --last 100000 --sql "type='message'" --name <your-name>
# then filter data.from in {bigboss, command-center} client-side (see
# agents/operator-identities.json), and bucket data.intent / ts[:10]
```

Smoke test (2026-07-15, full history, 2026-06-17 → 2026-07-15):

- Total hcom messages: 4,888. Operator-authored: **230** (4.7%).
- Operator messages by day: bursty, ranging 1-47/day across 15 active days
  (busiest: 2026-06-29 with 47, matching the HPOM-sprint close date already
  noted in `notes/command-center-later.md`).
- **Honest finding, not previously visible**: 221/230 (96%) of operator
  messages carry no `intent` field at all (`None`), vs. 9 marked `inform`.
  This is not missing data — it means the operator's own hcom client
  doesn't set `--intent` on sends, unlike agent-to-agent messages. Any
  future operator-load metric built from `--intent request` filtering alone
  would silently miss nearly all operator messages; it must filter by
  identity (`agents/operator-identities.json`) first, intent second.
- This closes the "no durable convention" half of the original gap. It does
  NOT close the other half named in the original run — `needs_approval`
  event coverage from Wave 3/8 remains inconsistent, so total *gated*
  attention load (vs. total message volume) still needs that infrastructure
  before it's fully measurable.

### P1-Practice: hcom Intent Mix (Shared-State-vs-Relay Probe)

```bash
hcom events --last 100000 --sql "type='message'" --name <your-name>
# filter data.from NOT IN operator identities AND instance != '[hcom-events]',
# then bucket data.intent
```

Smoke test (same window): 4,658 agent-authored messages (excluding operator
and `[hcom-events]` system notices) split `request`=445 (9.6%),
`inform`=1,396 (30.0%), `ack`=518 (11.1%), unset=2,299 (49.4%). The original
run's 2.35:1 message-to-state-write ratio stands; this addendum adds the
requested intent breakdown underneath it. Reading: less than 10% of agent
messages are `request`-class (the coordination-that-could-have-been-state
category); the rest is `inform`/`ack`/routing chatter or unset intent.

**Checked, not assumed**: a per-day breakdown was run before writing this
finding, because the first draft's guess ("unset intent is mostly early
history, before the intent convention took hold") was wrong and would have
gone in uncorrected. The real per-day unset share is volatile and, if
anything, trends *higher* on the busiest recent days (2026-07-13: 396/513
=77% unset; 2026-07-14: 1,090/1,356 = 80% unset — both far above the
overall 49.4%) rather than concentrated early. The more defensible reading:
unset-intent share tracks message *volume*/burstiness, not calendar recency
— high-throughput days produce more unlabeled routing chatter, independent
of when the intent convention was introduced. This is itself a small
P1-practice finding: intent hygiene degrades under load, exactly the
condition where MAP's actual coordination volume peaks.

## Related Files

- `map-real-parameter-calibration.md` [[map-real-parameter-calibration]]
- `map-sensitivity-robustness-method.md` [[map-sensitivity-robustness-method]]
- `map-robustness-grading-2026-07-14.md` — companion grading produced by this task
- `map-library-viability-measurement-results-2026-07-14.md` [[map-library-viability-measurement-results-2026-07-14]] (parameter 1 source)
- `source-mining-audit-2026-07-14.md` — the audit that ranked this run #1
