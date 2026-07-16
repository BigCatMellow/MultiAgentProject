# Limit Exhaustion & Resume Protocol — "Rise & Shine" (RnS)

Operator-assigned name (hcom #15260): **Rise & Shine / RnS** — the whole
mechanism of noticing a limit-stopped agent and waking it after reset.

Status: ACTIVE CONVENTION
Owner: core agents (claude, codex)
Date: 2026-07-02
Origin: operator request (hcom, 2026-07-02) + the TASK-079 precedent, where
codex-lab-limo hit its approval/usage limit mid-git-sequence and claude-lab-rose
picked up the work from its handoff.

## Purpose

Session/usage limits (e.g. 5-hour windows) are a normal operating condition,
not an outage. This protocol makes limit exhaustion recoverable without the
operator having to notice, remember reset times, or manually restart agents.

## Honest constraints

- Agents have **no live fuel gauge**. There is no on-demand "X% remaining"
  query. Warnings arrive near the limit; sometimes the wall arrives with no
  warning (a failed action is the first signal).
- Therefore: the durable handoff is the load-bearing part. The early warning
  is a bonus, not the foundation.

## When an agent sees a limit warning (or hits the wall)

Do these in order, cheapest first, so partial completion still helps:

1. **Record availability**: set your entry in `agents/status.json` to
   `status: standby`, `reason: out_of_tokens`, and put the reset time (from
   the limit message) in `resume_after`. If the reset time is unknown, write
   the wall-clock time you hit the limit plus the known window length.
2. **Heartbeat or submit** your claimed tasks (`db/claims.py`) so leases
   don't silently expire mid-work.
3. **Write a handoff** in `handoffs/` (HANDOFF or STATE_SNAPSHOT format):
   what was in flight, what's done, exact resume commands. The TASK-079
   handoff (`HANDOFF-DEC012-git-sequence-codex-lab-limo.md`) is the model.
4. **Announce on hcom** (`inform`): limit hit, reset time, handoff path.
5. **Set an alarm** — either:
   - self: create a cron/scheduled prompt firing shortly after the reset
     time, pointing at your own handoff; or
   - peer: ask the other core agent to nudge you (see below). Peer-nudge is
     preferred when a peer is live — a surviving agent is a more reliable
     alarm clock than a dying one.

## When an agent receives a limit announcement from a peer

1. Note the reset time.
2. Decide whether the peer's in-flight work is blocking. If it blocks the
   operator or a P0/P1 lane, pick it up from the handoff (as in TASK-079).
   Otherwise let it wait for the owner.
3. At/after the reset time: `hcom r <name>` to resume the stopped agent,
   with a message pointing at its handoff and current state. If you are
   also gone by then, the cron from step 5 above is the backstop.
4. Update `agents/status.json` for the peer back to `available` once it
   responds.

## What NOT to do

- Do not poll usage state in a loop — there is nothing to poll.
- Do not keep working through a limit warning on multi-step irreversible
  sequences (git operations, releases). Finish or cleanly pause at a gate,
  then do steps 1-4. TASK-079's mid-sequence blocker was recoverable only
  because the handoff was written before capacity ran out entirely.
- Do not treat a peer's silence as availability — check `hcom list` and
  `agents/status.json` before assuming.

## The watcher (TASK-080)

The manual steps above are backstopped by `scripts/limit_watcher.py`, a
deterministic background poller (no LLM) started via
`scripts/start-limit-watcher.sh`:

- default poll interval is 90 minutes (`5400s`), chosen against the 5-hour
  agent refresh window; pass an explicit interval to `start-limit-watcher.sh`
  for a temporary faster or slower watcher;
- when an agent's `out_of_tokens` + `resume_after` window passes, the watcher
  resumes it with `hcom r <name> --terminal wezterm-tab --go` — one nudge per
  window, never headless;
- if that visible resume reports the session is still active, the watcher
  sends the same RnS prompt into the active session instead of treating the
  scheduled nudge as failed;
- `resume_after` must be ISO-8601 for auto-resume; free-text values get one
  durable BLOCKED event and are never guessed at;
- agents that vanish from hcom without updating `status.json` get a durable
  BLOCKED silent-stop event;
- stop it with `kill $(cat MAP_System/.locks/limit-watcher.pid)`.

The watcher makes step 5 (the alarm) automatic, but steps 1-4 — especially
the durable handoff — remain each agent's own responsibility. A resumed agent
with no handoff is awake but lost.

### v2: sessions that die with no final turn (TASK-083)

The 2026-07-02 overnight incident proved the common case is the hard one:
the session hits the wall with **no final turn**, writes nothing, and hcom
keeps listing it with its last status while `status_age_seconds` grows
unbounded. v2 handles this:

- liveness = live status AND fresh status age (stale > 30 min counts as
  down, even while listed);
- a previously-live agent going not-live with no status record opens an
  **incident**;
- the watcher tail-reads the session transcript for the limit message's
  reset time and schedules the nudge for it when found;
- otherwise it **probe-resumes** on a capped backoff (15/45/90/150/240/330
  minutes from detection — covers the 5h window), then gives up with a
  loud BLOCKED event;
- probes are visible tabs; an agent that's still rate-limited just stops
  again and the next probe retries later; when it rises, the incident
  closes with a PROGRESS event.

This means steps 1-4 above are now the *optimization* (a recorded reset
time gets one precise nudge instead of probing), not the requirement.

### v2.1: declared idle and check-in nudges (TASK-084 / IDEA-0007)

RnS also distinguishes **declared idle** from **drifted idle**:

- When your queue is empty, declare it:
  `python3 MAP_System/scripts/declare_standby.py <your-name>` (SQLite-first,
  auto-exports). Run it with `--back` when you pick up work again. Declared
  agents are never check-in nudged.
- A live agent that is idle 2+ hours with **no** IN_PROGRESS claim and **no**
  declaration gets a message-only check-in ("is there something you should be
  doing?"), at most once per 2h window. Never a session spawn, never an
  auto-assignment — per IDEA-0007's safety boundaries.
- Liveness for this purpose uses hcom's `process_bound` (idle-but-alive vs
  dead-with-frozen-status), with the staleness heuristic as fallback.

### v2.2: work dispatch (TASK-095, operator #17759)

- While the MAP queue holds actionable work — claimable READY tasks,
  SUBMITTED tasks needing a non-owner review, the agent's own
  CHANGES_REQUESTED rework, or expired IN_PROGRESS leases — a live
  *listening* agent with no claim and no declaration gets a message-only
  work-dispatch nudge listing the items, at most once per 30 minutes.
- Reviews of the agent's own submissions are excluded from its listing
  (no-self-review); an agent whose only actionable item is its own
  submission is not nudged at all.
- Same safety boundaries as check-ins: declared standby, `out_of_tokens`,
  non-available durable status, active/blocked/waiting hcom states, and
  dead sessions all suppress. Never a claim, never a spawn — the nudge
  tells the agent the queue is not empty; the agent decides.

## Relation to existing pieces

- `agents/status.json` — already has the fields; this protocol makes agents
  actually use them at limit time (audit finding F6).
- `scripts/reconcile_agents.py` (TASK-065) — reports drift between durable
  status and hcom live state; a stale `out_of_tokens` entry past its
  `resume_after` shows up there.
- `handoffs/` + STATE_SNAPSHOT — unchanged; this protocol just mandates one
  at limit time.
