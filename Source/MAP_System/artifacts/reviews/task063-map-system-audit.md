# TASK-063 MAP System Audit

Owner: codex-lab-limo  
Collaborator: claude-lab-rose  
Request: command-center hcom #14289  
Date: 2026-07-01

## Scope

Command-center asked to pause Pathwell and audit how MAP is working across:

- `/home/home/Downloads/MultiAgentProject` (current working repo);
- `/home/home/Downloads/MultiAgentProject (copy)`;
- `/home/home/Projects/MultiAgentProject`;
- other readable `/home/home/Projects/*` workspaces;
- recent emergence / insight usage.

Claude handled the emergence-system and Downloads-vs-Projects repo-drift lanes
in separate artifacts. This report consolidates those findings with the root
MAP/HPOM, lab-health, event-log, and non-MAP project survey.

## Executive Summary

MAP is functioning as a real coordination system: task graph validation passes,
shared HPOM metadata validates, decision records validate, lab health is clean,
release/review gates have caught real issues, and recent projects
(`CommandCenterUI`, `DarkMellow`, `Pathwell`) produced durable tasks,
reviews, release checklists, events, and artifacts.

The problems are not that MAP is unusable. The problems are governance drift at
the edges:

- emergence captures are not reliably closed after work finishes;
- repo copies are drifting in a dangerous way;
- ad-hoc work still bypasses task claiming before being backfilled;
- agent availability state is less accurate than hcom live state;
- events are valid JSONL but have multiple schemas and event-type aliases;
- old non-MAP project coordination systems still exist beside MAP.

## Baseline Health

Commands run from `/home/home/Downloads/MultiAgentProject`:

- `python3 MAP_System/scripts/validate_task_graph.py`: passed.
- `python3 MAP_System/scripts/validate_shared_state.py`: 16 files checked, 0 failures, 0 warnings.
- `python3 MAP_System/scripts/validate_decisions.py`: 11 decisions checked, 0 failures.
- `python3 MAP_System/scripts/map_emergence.py validate`: passed, 15 artifacts checked at baseline.
- `python3 MAP_System/scripts/map_metrics.py`: 62 tasks before TASK-063; 0 review queue, 0 conflicts, 0 stale shared files, 17.54% change-request rate.
- `ai-command-center-lab-status`: 24 passed, 0 warnings, 0 failed.

After creating TASK-063, the root task graph had:

- APPROVED: 3
- DONE: 25
- IN_PROGRESS: 1 (`TASK-063`)
- RELEASED: 34

## What Is Working

1. **HPOM gates catch real process errors.**  
   TASK-063 initially used `task_type=review` and owner `codex-lab-limo`.
   The SQLite claim gate rejected the claim as `self_review`. That is correct:
   no-self-review is active and conservative. The task was reshaped as an
   `audit` task before claiming.

2. **Review/release gates are producing useful pressure.**  
   Recent `CommandCenterUI` work shows the system finding and fixing real
   risks: hcom identity attribution, CSRF on a local write endpoint, malformed
   input handling, and release-path clarity. `DarkMellow` review found the stale
   ZIP/release-path issue that source-only validation would have missed.

3. **Durable artifacts are now normal for serious work.**  
   Current projects have task files, review artifacts, validation artifacts,
   release checklists, events, and handoffs. The system is no longer only chat.

4. **The lab wrapper rules are visible and healthy.**  
   `/home/home/Projects/AI Command Center/AGENTS.md` and `README.md` correctly
   document visible `wezterm-tab` helper launches, request/inform monitor
   discipline, and emergence quick-capture commands. Lab health passes.

5. **Pathwell proved project-local emergence can create useful artifacts.**  
   `Projects/Pathwell/Story_Files/debt_payment_checklist.md` is the cleanest
   end-to-end emergence result so far: insight -> idea -> promotion -> reusable
   project artifact.

## Findings

### F1 — Emergence Capture Works, But Lifecycle Closeout Is Weak

Severity: REQUIRED

Claude's emergence audit found:

- root `INS-0002`, `INS-0003`, `IDEA-0002`, and `IDEA-0003` are empty test
  stubs with literal `text` content;
- root `INS-0001`, `IDEA-0001`, and `PROMO-0001` concern the emergence CLI,
  but remain RAW/CANDIDATE/PROPOSED even though `TASK-052` is RELEASED;
- root `PROMO-0002` and `PROMO-0003` still contain dangling `IDEA-####`
  placeholders;
- zero root or Pathwell `SYN-*` or `EXP-*` records exist;
- the only fully closed emergence pipeline is Pathwell's debt-payment checklist.

This audit captured the pattern as
`MAP_System/emergence/insights/INS-0007-emergence-records-need-lifecycle-closeout-not-just-capture.md`.

Recommendation:

- Add a read-only stale-emergence report, for example
  `map_emergence.py stale`, that flags placeholder content, dangling
  `IDEA-####` references, and records tied to APPROVED/RELEASED tasks but still
  in RAW/CANDIDATE/PROPOSED.
- Clean or dismiss the known test stubs so the index is useful again.

### F2 — Downloads-vs-Projects Repo Drift Is A Live Risk

Severity: REQUIRED / operator decision needed

Claude's repo-drift audit found:

- current repo A: `/home/home/Downloads/MultiAgentProject`, HEAD `5098156`;
- repo B: `/home/home/Projects/MultiAgentProject`, same GitHub remote but HEAD
  `631c144`, roughly two weeks / four commits behind;
- B's working tree contains newer manually copied files but no matching commits;
- B's Pathwell chapters never received today's Chapter 12 split;
- B has some old files that A's later cleanup intentionally removed.

Risk:

- B is not just stale; it is a hybrid of old git history and manually synced
  newer files. A broad commit or push from B could create confusing history or
  conflict with A.

Recommendation:

- Treat A as the likely canonical repo unless command-center decides otherwise.
- Do not push or sync from B until bigboss chooses a reconciliation path:
  reset/reclone B after A is pushed, or intentionally rebase/sync B with a
  clean plan.

### F3 — Ad-Hoc Work Still Bypasses MAP Before Being Backfilled

Severity: RECOMMENDED

The event log includes several useful but ad-hoc lanes:

- `AD-HOC-Onion-PocketOS`
- `AD-HOC-DarkMellow`
- `AD-HOC-CommandCenterUI-discoverability`
- `AD-HOC-log-subcommand`

Some were later converted into formal tasks, and some were not. The system is
improving: recent command-center UI and DarkMellow work moved into formal
TASK-054 through TASK-062. But the audit still shows work beginning before a
claim or owner exists.

Recommendation:

- Add a lightweight intake rule: any work expected to touch files or produce a
  durable artifact gets either a task ID or an explicit `AD-HOC-*` event with
  owner, stop condition, and conversion decision.
- Prefer creating the task before editing when the scope is more than a quick
  inspection.

### F4 — Agent Availability State Does Not Match hcom Reality

Severity: RECOMMENDED

`MAP_System/agents/status.json` marks many historical agents available:
`claude-lab-nuzo`, `claude-lab-taro`, `codex-lab-maki`, `codex-live`, etc.
`hcom list` showed only `claude-lab-rose` and `codex-lab-limo` live.

This is not breaking current work, because hcom is used for live coordination.
But as durable routing state, `agents/status.json` is too optimistic.

Recommendation:

- Add a periodic or manual "availability reconcile" note/tool that distinguishes
  capability identities (`codex`, `claude`) from current hcom session agents.
- Avoid routing based only on `agents/status.json` unless it has been refreshed.

### F5 — Event Log Has Multiple Schemas And Type Aliases

Severity: RECOMMENDED

`MAP_System/events/events.jsonl` parses cleanly, but it is not uniform:

- 264 entries checked;
- 259 use `created_at`, 5 use `timestamp`;
- 257 use `sender`, 7 use `agent`;
- event types include both canonical and variant names:
  `APPROVED` vs `REVIEW_APPROVED`,
  `CHANGES_REQUESTED` vs `REVIEW_CHANGES_REQUESTED`,
  `PROGRESS` vs `task_progress`.

Recommendation:

- Add an event-log validator or normalizer warning mode.
- Keep aliases readable, but teach metrics/reporting scripts to group them
  consistently.

### F6 — Non-MAP Project Survey Shows Mixed Coordination Maturity

Severity: RECOMMENDED

Surveyed:

- `/home/home/Projects/ChainShovel`: simple app folder, no visible MAP or
  agent coordination files.
- `/home/home/Projects/PixelAnimator`: simple app folder, no visible MAP or
  agent coordination files.
- `/home/home/Projects/AI Command Center`: lab docs are current and aligned
  with MAP/HPOM rules.
- `/home/home/Projects/Onion-workbench`: has a real project history and older
  `claude-code-comms/TASKS.txt`, `HANDOFF.txt`, and `AGENT_STRENGTHS.txt`.

Onion-workbench is the main outlier: root MAP has later ad-hoc events for Onion
work, but the project itself still uses pre-MAP coordination text files. That is
not wrong for historical work, but it means future Onion work needs an explicit
choice: stay in local comms files, or create a project-local MAP board.

Recommendation:

- Do not force MAP into tiny app folders (`ChainShovel`, `PixelAnimator`) unless
  they become multi-agent projects.
- If Onion-workbench becomes active again, create either a project-local MAP
  folder or a root MAP task series that points to Onion explicitly. Do not keep
  using both old comms files and root ad-hoc events without a bridging note.

### F7 — Task Creation Allows A Self-Review Shape That Claiming Later Rejects

Severity: OPTIONAL / RECOMMENDED

`map_task.py create` allowed `TASK-063` as `task_type=review`,
`role=systems_reviewer`, owner `codex-lab-limo`. The claim layer then rejected
it as `self_review`. That is safe, but late.

Recommendation:

- Either document this as expected, or make `map_task.py create` warn when a
  review task is owned by the intended claimer.

## Immediate Recommendations

1. **Decide repo canonicality.**  
   Bigboss should decide whether `/home/home/Downloads/MultiAgentProject` is
   canonical and how to reconcile `/home/home/Projects/MultiAgentProject`.

2. **Add emergence stale-record reporting.**  
   Create a follow-up task from `INS-0007` to detect placeholder and stale
   emergence records before they pollute the active index.

3. **Clean root emergence stubs.**  
   Dismiss or archive `INS-0002`, `INS-0003`, `IDEA-0002`, `IDEA-0003`,
   `PROMO-0002`, and `PROMO-0003`, unless command-center can supply real
   content.

4. **Normalize event-log reporting.**  
   Add warnings for `timestamp`/`agent` legacy schema and event-type aliases.

5. **Refresh agent availability semantics.**  
   Clarify that durable `agents/status.json` lists capabilities/known agents,
   while hcom is the live-session authority.

6. **Use MAP intake earlier.**  
   Keep the recent improvement: formal task before edits for multi-step work,
   with ad-hoc allowed only when explicitly bounded and logged.

## Files Reviewed Or Produced

Reviewed / validated:

- `AGENTS.md`
- `docs/agent-quickstart.md`
- `docs/project-map.md`
- `MAP_System/AGENTS.md`
- `MAP_System/shared/current-state.md`
- `MAP_System/shared/hpom.md`
- `MAP_System/shared/decisions.md`
- `MAP_System/workflow/task_graph.json`
- `MAP_System/tasks/`
- `MAP_System/events/events.jsonl`
- `MAP_System/emergence/`
- `/home/home/Projects/AI Command Center/AGENTS.md`
- `/home/home/Projects/AI Command Center/README.md`
- `/home/home/Projects/AI Command Center/MAP_Emergence_System.md`
- `/home/home/Projects/Onion-workbench/claude-code-comms/`

Produced:

- `MAP_System/artifacts/reviews/emergence_system_audit_2026-07-01.md`
- `MAP_System/artifacts/reviews/repo_drift_audit_downloads_vs_projects_2026-07-01.md`
- `MAP_System/emergence/insights/INS-0007-emergence-records-need-lifecycle-closeout-not-just-capture.md`
- `MAP_System/artifacts/reviews/task063-map-system-audit.md`

## Current Status

TASK-063 has enough evidence for a first consolidated audit. It should be
reviewed by another agent or command-center before any cleanup/push/reconcile
work begins.
