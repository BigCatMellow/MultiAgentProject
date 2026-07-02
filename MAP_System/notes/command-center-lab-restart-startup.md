# AI Command Center Lab Restart And Startup Notes

Status: ACTIVE NOTE
Owner: command-center
Created: 2026-07-02
Applies-To: AI Command Center Lab launcher, RnS watcher, core lab agents
Related-Tasks: TASK-080, TASK-083, TASK-084, TASK-085

## Purpose

When the operator restarts the machine or opens the AI Command Center Lab from a
cold start, the lab should restore the command-center surfaces and the runtime
checks that keep Codex and Claude from silently going stale.

The durable behavior is:

- The AI Command Center Lab opens visible terminal tabs, not hidden sessions.
- The Rise & Shine watcher starts idempotently.
- Core agents orient themselves from MAP files and hcom state.
- If an agent is alive but idle too long without declaring standby, RnS sends a
  message-only check-in asking whether there is work it should be doing.
- If an agent hits a usage/session limit, RnS records or infers the reset window
  and resumes through a visible `wezterm-tab` session.

## Current Implementation State

- Canonical repo: `/home/home/Downloads/MultiAgentProject` (DEC-012).
- RnS watcher scripts:
  - `MAP_System/scripts/limit_watcher.py`
  - `MAP_System/scripts/start-limit-watcher.sh`
  - `MAP_System/scripts/declare_standby.py`
- RnS protocol note: `MAP_System/notes/limit-exhaustion-protocol.md`.
- Lab-open autostart wiring is approved in `MAP_System/tasks/TASK-085.json`.
- Launcher files for TASK-085 are outside the repo:
  - `/home/home/.local/bin/ai-command-center-lab`
  - `/home/home/.local/bin/ai-command-center-lab-claude`
  - `/home/home/.local/bin/ai-command-center-lab-codex`

Those launcher files are outside Git. Treat this note and
`MAP_System/artifacts/reviews/task085-review.md` as the durable repo-side
documentation for what they are expected to do.

As of 2026-07-02, repo policy changed the RnS default poll interval to 90
minutes (`5400s`). If an external launcher still passes `60`, update it to call
`MAP_System/scripts/start-limit-watcher.sh` with no interval argument, or pass
`5400` explicitly.

## Startup Contract

On lab open, the launcher does this in order:

1. Start the AI Command Center Lab terminal layout with visible tabs.
2. Start RnS with `MAP_System/scripts/start-limit-watcher.sh` (default
   interval: 90 minutes / 5400 seconds).
3. Ensure watcher startup failure does not block the lab from opening.
4. Start or resume Codex and Claude through visible hcom terminals.
5. Prompt each lab agent to run startup orientation before taking new work.

Startup orientation means:

- Read root `AGENTS.md`, `docs/agent-quickstart.md`,
  `docs/project-map.md`, and `MAP_System/AGENTS.md`.
- Read `MAP_System/shared/current-state.md` and
  `MAP_System/shared/decisions.md`.
- Check `MAP_System/handoffs/` for the newest relevant handoff or
  `STATE_SNAPSHOT-*`.
- Check live hcom state with `hcom list --name <agent-name>`.
- Check durable agent state in `MAP_System/agents/status.json`.
- Check active task graph state before claiming or asking for priorities.
- Send exactly one initial hcom message to `@bigboss`:
  - a resume plan if there is in-flight work;
  - otherwise a priorities request.

## RnS Behavior

RnS has three related behaviors:

- Recorded reset resume (TASK-080): if an agent records
  `status=standby`, `reason=out_of_tokens`, and ISO-8601 `resume_after`, the
  watcher resumes it after the reset window.
- Silent-stop recovery (TASK-083): if a previously live agent stops without a
  final turn, the watcher detects stale hcom liveness, tails the transcript for
  reset time, and uses capped visible probes when needed.
- Declared-idle check-ins (TASK-084): if a live hcom `listening` agent sits idle
  for 2+ hours with no `IN_PROGRESS` claim and no standby declaration, the
  watcher sends one hcom request message. It does not spawn a session, claim
  work, or assign tasks.

Declared standby is the intentional idle state:

```bash
python3 MAP_System/scripts/declare_standby.py <agent-name>
```

Return from standby before picking up work:

```bash
python3 MAP_System/scripts/declare_standby.py <agent-name> --back
```

## Normal Restart Path

After a reboot or full lab close, open the AI Command Center Lab. The launcher
starts the watcher and the visible lab tabs. Each agent prompt includes startup
orientation ending in exactly one proactive hcom message to `@bigboss`.

## Manual Fallback After Restart

Use this only if the lab launcher does not bring everything up.

```bash
cd /home/home/Downloads/MultiAgentProject
MAP_System/scripts/start-limit-watcher.sh
hcom list --name limo
```

Resume visible core sessions if needed:

```bash
hcom r claude-lab-rose --terminal wezterm-tab
hcom r codex-lab-limo --terminal wezterm-tab
```

Verify watcher state without sending real nudges:

```bash
python3 MAP_System/scripts/limit_watcher.py --once --dry-run
```

Optional reconciliation check:

```bash
hcom list --json --name limo > /tmp/map-hcom-live.json
python3 MAP_System/scripts/reconcile_agents.py --hcom-json /tmp/map-hcom-live.json
```

Core validators:

```bash
python3 MAP_System/scripts/validate_task_graph.py
python3 MAP_System/scripts/validate_events.py
python3 MAP_System/scripts/map_emergence.py validate
python3 MAP_System/scripts/map_emergence.py stale
```

## Important Boundaries

- Do not use `--headless` for agents or helpers unless the operator explicitly
  instructs it.
- Spawn helpers with `--terminal wezterm-tab`.
- Use `hcom send --intent request` only for operator decisions, approvals,
  blockers, conflicts, privacy/scope risks, or real questions.
- Use `hcom send --intent inform` for routine progress.
- Do not use hcom or RnS to auto-assign work. RnS can wake or ask; task claims
  still go through MAP task ownership and review rules.
- Do not silently modify files owned by another active task. TASK-085 owns the
  lab launcher implementation files while active.

## What "Right From The Get-Go" Means

There are two safe meanings:

- Boot orientation: every lab open causes each agent to orient and send one
  clear initial message to the operator.
- Idle check-in: after the configured 2h undeclared-idle threshold, RnS asks a
  live idle agent whether there is something it should be doing.

An immediate check-in sweep on every launch is a separate behavior. If added, it
should respect the same safety rules: no check-ins to declared-standby agents,
blocked/waiting agents, agents with `IN_PROGRESS` claims, or agents that already
sent a startup orientation message.
