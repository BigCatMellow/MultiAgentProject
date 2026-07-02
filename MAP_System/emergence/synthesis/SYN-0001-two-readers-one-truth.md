# Synthesis Note

Synthesis ID: SYN-0001
Project: MAP
Related insights:
- INS-0006 (task-ID collision under concurrent agents)
- INS-0007 (emergence records captured but never closed)
- TASK-080 review findings (PID-namespace false-dead; empty-hcom-list bug)
- TASK-063 audit findings F1 (repo drift), F6 (agent-status drift), F7 (event schema drift)

Date: 2026-07-02
Created by: claude-lab-rose
Status: CLARIFIED

## Pieces being combined

### Piece A

Concurrency failures: two agents read "next free task ID" from the same
directory and both picked TASK-023 (INS-0006). Same shape at review time:
the reviewer's sandbox and the host read the same PID and reached opposite
conclusions about whether the limit watcher was alive (TASK-080 review).

### Piece B

Drift failures: repo A and repo B both claimed to hold the project's truth
while diverging for two weeks (F1). `agents/status.json` said 16 agents were
available while hcom showed 2 live (F6). Emergence records said RAW/CANDIDATE
while the work they tracked was RELEASED (INS-0007). Event log entries used
two schemas and three alias type-names for the same facts (F7).

### Piece C (optional)

Ownership false-positives: the task-graph validator treated auto-generated
files (emergence/INDEX.md, events.jsonl) as task-owned outputs and reported
collisions between tasks that had both legitimately touched them — two tasks
"owning" a file that in truth belongs to a generator.

And the freshest instance, mid-TASK-082: the reconcile fix itself was first
written to `agents/status.json` directly — the exporter *mirror* — and was
silently clobbered by the next SQLite export. The fixer repeated the exact
failure being fixed, which is strong evidence the pattern is easy to miss
even while explicitly thinking about it.

## New combination

Every MAP failure found this week is the same failure: one piece of state
with two readers and no declared authority. All the successful fixes took
one of exactly three shapes:

1. **Declare one view authoritative and write it down** — DEC-012 (repo A
   canonical), agents/README.md (hcom is live truth; SQLite feeds the
   status.json mirror), /proc cmdline identity over bare kill -0.
2. **Make the read-write atomic so two readers cannot interleave** —
   `map_task.py create --task-id auto` under `BEGIN IMMEDIATE`.
3. **Build an automatic cross-check between the views** —
   `reconcile_agents.py`, `map_emergence.py stale`, `validate_events.py`,
   the limit watcher's silent-stop detection.

## What this makes possible

A design rule for any new MAP state: before shipping, name the state's
authoritative reader, or make competing writes atomic, or add a reconcile
report — at least one of the three. It also gives reviewers a targeted
question ("who else reads this, and which copy wins?") that would have
caught every one of this week's failures at design time.

## Why this was not obvious before

Each failure surfaced in a different subsystem (tasks, git, emergence,
agents, events, review tooling) at a different time, was fixed by a
different mechanism, and looked domain-specific. The common shape only
became visible when the TASK-082 coverage matrix put all six in one table.
Nothing in MAP's process compares failures *across* subsystems — that gap
is itself an instance of the pattern (each incident had one reader: the
agent who fixed it).

## Possible uses

- Add "who else reads this state, and which copy wins?" to the review
  standard for any task introducing new durable state.
- Apply shape 1 explicitly to remaining un-declared state: e.g. status.json
  now documents that SQLite is its source; INDEX.md documents its generator.
- Use as the test question for new tooling proposals before building them.

## Risks or limits

- Over-application: state with a single reader needs none of the three
  shapes; adding locks/reconciles there is pure overhead.
- The rule covers *state* divergence, not judgment disagreements between
  agents — those are what review gates are for.

## Recommended next step

Choose one:

- [ ] Park — valid but not the right time
- [x] Create idea card — ready to develop further (review-standard question:
  "who else reads this, and which copy wins?" — small, concrete, testable
  on the next state-introducing task)
- [ ] Run experiment — testable immediately
- [ ] Escalate — needs decision authority
