<!-- hpom: file: notes/orchestration-notes.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: 2026-07-14 lead session (claude-lab-mira) -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Orchestration Notes

Running log of what works and what fails when an agent leads the lab.
Operator-requested (2026-07-14): "make notes as to what works for you and
what doesnt, and use the system like a team." Terse entries, newest last.
Promote recurring patterns into AGENTS.md or an insight record.

## 2026-07-14 (claude-lab-mira lead session)

### Worked

- works: cross-review pipelining — two agents each implement one lane and
  review the other's; no idle reviewer, no self-review conflict.
  ev: TASK-180..183 all same-day RELEASED.
- works: precise work packets for delegated implementation — recon/design done
  by lead, helper gets exact file list, decided design, must-not list, and
  verification commands in a durable inbox/helpers/ note.
  ev: `task-186-rns-terminal-suppression-implementer.md` (helper zero acked
  and started in <1 min with zero clarifying questions).
- works: auto task-ID allocation as the collision arbiter — when a verbal
  claim ("I'll take TASK-184") collided with DB auto-allocation, keeping the
  DB canonical and renumbering the verbal intent cost one message.
  ev: hcom #33763 exchange; IDEA-0006's announce-before-claim lesson.
- works: live-surface verification catching what static review misses.
  ev: TASK-182's first real curl found two integration bugs (cwd-relative
  path, validator exit-code semantics) after node --check/py_compile passed.
- works: baseline-before-change evidence capture — recording the watcher's
  wrong behavior (dry-run probing dead sessions) before implementing the fix
  makes the after-diff self-proving.
  ev: task186-baseline-dryrun.txt.

### Failed / cost time

- fails: lead solo-implementing while owning dispatch — operator corrected it
  directly ("you are the orchestrator here... use the system like a team").
  fix: delegate implementation to spawned visible helpers; lead keeps design,
  dispatch, verification, review, release.
- fails: ending a cycle with an options-menu request to the operator —
  operator refused to pick ("I dont want to say it again"). fix: state the
  recommendation, execute it, reserve requests for genuine conflicts/privacy/
  scope-boundary risks.
- fails: verbal task-ID reservations in chat — see auto-ID entry above; say
  "next auto ID" instead of naming an unallocated number.
- fails: literal double-bracket wikilink example text inside review records — the
  librarian validator correctly flags them as broken links; two review
  artifacts needed cleanup passes. fix: describe wikilinks in prose or
  backticks-without-brackets inside durable records.
- caution: harness-level push classifier blocks broad pushes to the public
  repo even with operator-intent precedent — operator must name the push
  explicitly (e.g. run it themselves via `!`). Don't burn time retrying.

- caution: harness classifier also blocks batch shared-state lifecycle writes
  against sessions the acting agent didn't create (declare_standby --terminal
  on 10 agents, TASK-186) — same class as the push block: broad autonomy
  grants don't clear it; the operator must run or allowlist the specific
  command. Design implication: State-Steward-class writes may structurally
  need an operator touchpoint; don't plan them as fully autonomous steps.
- works: RnS end-to-end on a real limit event — nivo marked mira
  standby/out_of_tokens with resume_after, restarted the watcher, manual
  trigger + systemd timer fired, mira resumed and declared --back. First
  full-loop live validation of the TASK-080/083/084 stack; also surfaced
  TASK-187 (active-session resume awareness) as a real gap.

- fails: starting a review without claiming it in hcom first — TASK-196's
  review got duplicated (mira mid-verification during a harness outage, zera
  approved+released meanwhile after an operator 'continue' broadcast fanned
  the request out). fix: reply "taking the TASK-NNN review" BEFORE verifying,
  same announce-before-claim rule as task IDs. Duplicated verification is the
  cheap failure mode; conflicting verdicts would be the expensive one.
- fails: reading task-file mirrors for live claim state — mirrors export-lag;
  claimed_by looked empty while SQLite held a valid claim, triggering an
  unnecessary arbitration message. fix: for claim/lease questions, read
  map.db (mode=ro) directly; mirrors are for content, not liveness. (SYN-0001
  applied to my own read.)
- works: suite-failure triage under concurrent agents — 3 transient fails
  (a peer's mid-run non-canonical event append) resolved by re-running before
  reacting; the second run was clean because the peer had already fixed their
  event. Rule: on suite failures in a live multi-agent tree, re-run once and
  diff the failure set before filing anything.

### Standing rules (operator-set)

- rule: all spawned Claude helpers start in auto permission mode and Haiku
  model tier by default (operator, 2026-07-14). Persisted as
  `hcom config claude_args '--permission-mode auto --model haiku'` so every
  future `hcom claude` spawn inherits it. Visible wezterm-tab stays mandatory
  so the operator can still see and intervene. Sonnet/Opus helper use requires
  a written escalation request and review by a different core agent; approve
  generously when the reasoning shows the higher tier is the right fit.
- rule: spawns always use `--terminal wezterm-tab`, never `--headless`,
  unless the operator explicitly instructs otherwise (session standing rule).
