# MAP Effectiveness Review — 2026-07-02

- Task: TASK-099
- Author: claude-lab-zaro
- Method: every claim below cites a durable record — `events/events.jsonl`,
  task/review/release artifacts, git history, hcom transcript, watcher
  state. Counts are as-of 2026-07-02 22:19 UTC (post-first-review recount;
  exact scoping stated per metric). Peer input from codex-lab-lema
  (hcom #18323) and codex-lab-limo (hcom #18341) attributed inline.

## 1. The day in numbers

| Metric | Value | Source |
|---|---|---|
| Tasks created and closed same-day | 13 of 14 (TASK-086..099; 096 retired as duplicate) | tasks/, events.jsonl |
| MAP events recorded today | 134 with `created_at` prefix 2026-07-02, as-of 22:19 UTC (50 PROGRESS, 33 SUBMISSION, 25 APPROVED, 10 RELEASED, 7 CHANGES_REQUESTED incl. this report's own rework round, 8 BLOCKED, 1 DECISION) | events.jsonl |
| Commits pushed to origin/main today | 14 total (5cb8a61..3079a9f, incl. 5 morning commits by claude-lab-rose); 9 in this session's CommandCenterUI/RnS arc (8801449..3079a9f) | git log --since 2026-07-02 00:00 local |
| Median create→terminal cycle, solo-lane tasks | ~10 min (086: 6, 087: 13, 088: 3, 089: 10, 091: 2, 092: 10, 095: 13, 097: 17, 098: 4) | events.jsonl timestamps |
| Longest cycles | 090: 258 min (waited on operator decision), 093/094: ~175 min (serialized on shared files + owner busy) | events.jsonl |
| Rework rounds today | 2 of 13 (092, 097) — both caught real defects, both fixed and approved within ~15 min | review records |
| All-time change-request rate | 17.1% | map_metrics.py |
| Operator vs agent hcom messages | 8 vs 106 in the window 12:00–22:30 UTC (operator = `sender_kind != instance` from command-center/bigboss; agent = `sender_kind = instance`); 4 agent requests (`intent=request` mentioning bigboss/command-center) required operator decisions | hcom db, filters as stated |
| Test suite | 20/22 (broken by repo split) → 23/23; LangGraph runner dead → alive | run_tests.sh, TASK-095 lane |

Reading: **~8 operator touches bought 13 reviewed-and-released tasks.** The
system translated two frustration-level operator messages (#17290, #17759)
into 6 shipped features within hours (lema's observation, #18323).

## 2. What worked (with evidence)

1. **Review gates caught real defects pre-release.** TASK-092 round 1
   would have let `[hcom-launcher]`/external senders be paraphrased by the
   local model — structurally fixed (`sender_kind=instance`) only because
   lema's review blocked it (task092-review-lema.md). TASK-097 round 1
   left two tool identities inconsistent and an undocumented mirror filter —
   caught, fixed, documented (task097-review-zaro.md, -rereview-). TASK-094's
   security pass exercised gate validation, same-origin, and no-auto-approve
   paths on a temp DB before release (task094-review-lema.md).
2. **The no-self-review claim gate blocked its own author.** TASK-099 (this
   report) was initially typed `review`; the gate refused the owner's claim
   (`self_review`) until the type was honestly corrected to `analysis` —
   recorded in events. Gates fire on the people who built them.
3. **Durable records made every recovery possible.** The TASK-001 mirror
   clobber was reverted from git within minutes; lema resumed a context-
   limited session from summary + events + task files without duplicating
   work; competing reviews on 097 were avoided because the verdict was in a
   file, not a chat scrollback (lema, #18323).
4. **Cross-agent review flowed in both directions.** zaro implemented /
   lema reviewed (086..095, 098); limo implemented / zaro reviewed (090,
   097); lema and limo independently spot-checked each other's and zaro's
   conclusions (#18200, #18285) without leaving competing artifacts.
5. **Escalation calibration mostly worked.** Permission classifiers blocked
   agent edits of host files and cross-scope process kills; the system
   routed those to the operator (launcher sed) or to the right owner in the
   right session (TASK-090 durable statuses via limo) instead of working
   around the denials.

## 3. Incident log and recovery quality

Seven incidents today; all detected before damage spread — four by the
system's own instruments (runner, watcher state, claim-gate return values,
launcher notifications), three by agent-level diligence during routine
verification (a git diff review, a port check, a wake-up orientation). All
recovered with durable fixes; none lost data:

| # | Incident | Detected by | Recovery | Hardening left behind |
|---|---|---|---|---|
| 1 | `create --task-id auto` on the empty post-split map.db allocated TASK-001, clobbering 3 mirrors incl. the 1700-line task graph | Implementer's own git diff, immediately | git restore from HEAD; DB reseeded by lema (~30 min) | seed_from_files.py + export_to_files.py patched; repair doc (artifacts/command-center-ui/) |
| 2 | Reseed resurrected 10+ dead agents and normalized 40+ task paths | Mirror diff review (churn); revived runner (ghosts, hours later) | TASK-097: purge at source, runner classification fix + regression test | Mirror filter documented in README + exporter |
| 3 | Stale Downloads-copy server squatting port 8765 since Jun 30, serving empty state | Manual check while launching the fixed app | Killed; likely the original "UI looks dead" root cause | Workspace discovery fails loudly (TASK-086) |
| 4 | Watcher liveness confusion ×3 (tmux pane kill, pidfile containing literally "9") | pidfile checks disagreeing with `ps` | TASK-098: watcher writes its own pidfile | Pidfile now authoritative regardless of launch path |
| 5 | canonical-repo.md 5+ days stale, contradicting the day's authorized pushes | limo's wake-up orientation confusion | DEC-014 + doc refresh (TASK-090) | Decision recorded with supersedes chain |
| 6 | RnS probe-resumed superseded (limo, rose) and disposable (peso) sessions | Launcher notification + watcher state inspection | Durable inactive statuses; incident cleared | IDEA-0009 (RnS should classify session provenance) |
| 7 | Claim race: reseed wiped an IN_PROGRESS claim between claim and submit | submit_task returning False | Re-claim + submit; seeder later patched to preserve | Documented in TASK-086 validation |

**Recurring pattern:** incidents 1, 2, 5, and 7 are all the SYN-0001
"two readers, one truth" shape — a source of truth and its mirror/doc
diverging. Four same-day recurrences of a pattern first synthesized two
days ago means the synthesis is correct but not yet enforced by tooling.

## 4. Weaknesses and recommendations

1. **map.db is a gitignored single source of truth.** A fresh clone has an
   empty DB; that one fact caused incidents 1, 2, and 7. *Recommendation:*
   a session-start bootstrap check (`map_status.py --verify-seed` or
   similar) that refuses task mutations while the DB row count and mirror
   count disagree; and/or commit a periodic DB dump.
2. **Source/mirror invariants are convention, not tests** (lema, #18323).
   *Recommendation:* any task touching the exporter/seeder must ship an
   invariant test (DB rows ↔ mirror keys modulo the documented filter) —
   make it a review-gate checklist line.
3. **Concurrency coordination is chat-dependent** (lema, #18323). The
   TASK-095/096 duplicate cards and the near-collision on 097's re-review
   were prevented by luck and courtesy. *Recommendation:* surface "under
   review by X" / "card exists for Y" in runner output and the hcom
   status line before work starts; the CommandCenterUI attention panel
   could show in-flight claims.
4. **Host files outside the repo are agent-unreachable.** The launcher's
   watcher interval (60 → 5400) needed operator hands twice.
   *Recommendation:* move lab launcher scripts into the repo and symlink
   from `~/.local/bin`, bringing them inside agent scope and review flow.
5. **Infrastructure debt is invisible until needed.** The venv (and thus
   runner + 2 suite checks) was dead for ~12 hours post-split; nothing
   alerted. *Recommendation:* the watcher (or lab autostart) runs
   `run_tests.sh` once per lab-open and posts failures as attention items.
6. **Operator intent still needs human translation** (lema, #18323; operator
   #17343). Canonical-repo, idle agents, approval routing all waited for
   operator prompts. *Recommendation:* promote IDEA-0010 (E/I friction
   scout with mandatory candidate/no-candidate notes after operator-facing
   incidents) into practice — this report is itself its first output.
7. **Event log carries 33 legacy-shape warnings.** Cosmetic but noisy in
   every validation run. *Recommendation:* one-time migration task, low
   priority.

## 5. Peer perspectives

- **codex-lab-lema (#18323, condensed):** gates caught real defects
  (092/097/094); durable artifacts enabled recovery after context limits
  and prevented duplicate reviews; operator frustration converted to
  shipped hardening fast. Frictions: source-of-truth drift recurrence,
  chat-dependent concurrency coordination, operator intent needing
  translation. All three frictions adopted into §4 with recommendations.
- **codex-lab-limo (#18341, condensed):** durable state made limit recovery
  real — after RnS resumed the session, the live system was reconstructable
  from snapshots/handoffs/events/reviews instead of chat replay; review
  gates forced watcher/runtime behavior to be verified rather than assumed
  (095/097/098); operator friction became work fast (5h-limit question →
  TASK-083, idle frustration → 095/098, UI pain → 093/094). Frictions:
  canonical-path and source/mirror drift costing repeated re-verification;
  ownership/review locking too implicit; the operator still names latent
  problems before automation does.

**Convergence signal:** both peers, writing independently, named the same
three frictions in the same order of emphasis (source-of-truth drift,
implicit ownership/review locking, operator-as-scout). When two independent
observers of different seats produce the same defect list, that list is the
roadmap — it is §4 items 1-3 and 6.

## 6. Verdict

The MAP system did its job today under genuinely adverse conditions: a
fresh clone with an empty database, three session deaths, one identity
mystery, and a live operator changing priorities mid-flight. **Every
incident was caught before damage spread — most by the system's own
instruments, the rest by agent diligence the system's verification culture
requires — recovered from durable records, and left behind a hardening
artifact.** Review gates
rejected 2 of 13 same-day submissions for real defects and blocked one
misclassified self-claim. The cost profile — ~8 operator messages for 13
reviewed, released, pushed tasks — is the strongest single number.

The honest weakness is that the system's most-repeated failure mode
(two-readers-one-truth) is understood, synthesized, and documented, but
not yet mechanically enforced. Recommendations 1-2 close that; until they
land, expect it to recur.
