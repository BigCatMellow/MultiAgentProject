# TASK-140 Process Use Audit

task_id: TASK-140
owner: codex-lab-neko
date: 2026-07-04
scope: Command Center Lab operating-loop use after TASK-129/TASK-130/TASK-122
status: submitted-for-review

## Baseline

This audit does not repeat the full systems inventory from:

- `MAP_System/artifacts/audits/task-129-map-system-adherence-audit.md`
- `MAP_System/artifacts/audits/task-130-map-systems-real-usage-evidence.md`
- `MAP_System/artifacts/reports/map-process-failure-report-2026-07-03.md`

Those records already establish the main pattern: MAP has many documented
systems, but the ones that get used reliably are the ones with a gate, a
script, or an obvious operating habit.

This audit checked the live lab loop around TASK-137 through TASK-140:

- task creation, claim, review, approval, and release;
- hcom/Monitor updates;
- helper routing;
- live route/status checks;
- agent availability reconciliation;
- observed operator friction from the ProjectUpdater and reviewer-conflict
  incidents.

## What Is Working

### Task/review/release gates are being used

Recent work went through durable MAP state rather than chat-only completion:

- TASK-137: review conflict resolved through visible helper `bula`, review
  artifact validated, task approved and released.
- TASK-138: no-self-review helper-routing policy captured as durable MAP
  guidance, reviewed by `claude-lab-vino`, released.
- TASK-139: CommandCenterUI ProjectUpdater bug fixed, security-framed review
  performed by `claude-lab-vino`, released.
- TASK-140: this audit was created and claimed before process files were edited.

This is the right operating shape. The system is not failing because agents
lack rules; the remaining failures are mostly places where the rules still
require agents to remember manual steps.

### Helper routing improved after the operator intervention

TASK-137 exposed a routine no-self-review conflict that should not have needed
the operator. TASK-138 turned that into a concrete rule in `AGENTS.md` and
`notes/helper-agent-guide.md`.

TASK-140 extended the helper guide with a permission-mode rule for Claude
helpers: bounded visible helpers may use the least-interruptive permission mode
available, but not across human, privacy/scope, security, destructive-action,
external-service, broad Git, or publication boundaries.

### Security second-pass review is active

TASK-139 added a local backend `xdg-open` action, which is a write/launch-capable
surface. The review explicitly checked same-origin enforcement, no user-supplied
path, no shell interpolation, and method restrictions before approval.

That is a strong example of `AGENTS.md` Security Second Pass being exercised
as behavior, not just prose.

### Cross-agent split is improving

For this audit, `claude-lab-vino` announced a complementary systems-adherence
angle through hcom instead of duplicating the same report. This agent took the
operating-loop/mechanics angle. That is the right response to a broadcasted
process-review ask: declare scope, avoid duplicated ownership, and coordinate
findings.

## Gaps Found

### 1. SQLite/file mirror sync is still too manual

TASK-140 reproduced a known gap from TASK-122. The SQLite task state became
`IN_PROGRESS` after `claim_task()`, but the task JSON still showed `READY`
until `export_to_files.py` was run explicitly.

Impact:

- reviewers can see stale task files;
- Monitor/UI code that reads file mirrors can lag canonical SQLite state;
- agents have to remember a sync step after claim/heartbeat/submit operations.

Status in this task: not fixed. This is larger than a doc tweak and should be
a follow-up validator or wrapper task. The preferred fix is a claim/submit
wrapper or pre-review validator that compares SQLite, task JSON, and
`workflow/task_graph.json`.

### 2. `reconcile_agents.py` default output was misleading

Running `reconcile_agents.py` without `--hcom-json` previously printed
`Live hcom agents: 0`. That looked like live reality, but it only meant no
live input file was supplied.

Fix applied in TASK-140:

- `reconcile_agents.py` now reports `Live hcom agents: not checked
  (--hcom-json not provided)`.
- JSON output includes `hcom_input_provided`.
- `test_reconcile_agents.py` covers the no-input case.
- `agents/README.md` warns not to treat no-input mode as proof that no sessions
  are live.

### 3. Live hcom and durable agent status still disagree

After providing real `hcom list --json`, reconcile showed live sessions that
are not registered in durable status and durable available agents that are not
live.

Observed sample:

- live hcom agents: `claude-lab-vino`, `codex-lab-neko`, `claude-lab-rose`;
- live but not registered: `claude-lab-vino`, `claude-lab-rose`;
- durable available but not live: several capability identities or stale lab
  agents.

Some mismatch is expected because `agents/status.json` intentionally mixes live
sessions, capability identities, human/relay identities, and durable routing
records. The remaining problem is presentation: agents and the Monitor need a
clear distinction between "capability exists", "durable session record says
available", and "hcom says this session is live right now."

Status in this task: recorded here as a recommendation. A larger UI/reconcile
task should decide whether to normalize the durable board, improve the
reconcile report grouping, or wire the live hcom feed into CommandCenterUI.

### 4. hcom sender aliases are not always reply targets

The process-review request arrived from `command-center`, but `hcom send
@command-center` failed because that alias is not a live agent target. The
correct authority route was `@bigboss`.

Impact:

- agents can waste time trying to reply to a sender label that is not routable;
- Monitor-visible status may not reach the operator unless the agent knows the
  authority route.

Status in this task: recorded as an operating observation. No code fix applied.
The practical rule is to route operator-facing progress to `@bigboss` when the
sender is a non-agent command-center alias.

### 5. Broadcast ownership still depends on agents behaving well

This audit worked because Vino declared a non-overlapping angle and this agent
declared the mechanics angle. That was human-like coordination, not a gate.

This is the same class TASK-122 identified: broadcast assignments can create
duplicate-owner risk until one agent claims coordinator/owner and others switch
to findings-only or review/support mode.

Status in this task: no new mechanism built. The recommendation remains to
formalize a broadcast coordinator rule or intake helper before the next large
multi-agent audit.

### 6. Event warnings remain accepted background noise

`validate_events.py` still passes with `errors=0 warnings=33`, all legacy
warnings. That is acceptable for current release gates, but repeated expected
warnings lower the signal of new warnings.

Status in this task: no change. This remains a known cleanup item from
TASK-122.

## Fixes Applied

Files changed by TASK-140:

- `MAP_System/scripts/reconcile_agents.py`
- `MAP_System/tests/test_reconcile_agents.py`
- `MAP_System/agents/README.md`
- `MAP_System/notes/helper-agent-guide.md`
- `MAP_System/artifacts/reports/task-140-process-use-audit.md`

Behavioral changes:

- agent reconciliation no longer implies zero live agents when no hcom JSON was
  supplied;
- helper guide now documents safe Claude helper permission-mode handling;

## Recommendations

1. Build a task-state mirror reconciliation gate.
   This should compare SQLite, `tasks/TASK-*.json`, and
   `workflow/task_graph.json` before review/release. This is the highest-value
   follow-up because TASK-122 and TASK-140 both reproduced the drift pattern.

2. Improve live/durable agent reconciliation.
   Either group reconcile output by identity kind or wire live hcom state into
   the CommandCenterUI so the operator sees live sessions separately from
   durable capability records.

3. Add a broadcast coordinator convention.
   For broad hcom requests, the first agent taking durable ownership should
   announce owner/scope and request findings-only packets from others unless
   the operator asked for independent deliverables.

4. Normalize or grandfather event warnings.
   Keep `validate_events.py` tolerant for historical logs, but make it harder
   for new warnings to hide inside the known 33-warning baseline.

5. Avoid adding more prose-only systems until the above enforcement gaps move.
   The current bottleneck is not a lack of documented process. It is that some
   process still relies on agent memory instead of the path of least resistance.

## Verification

Commands run:

```text
python3 MAP_System/tests/test_reconcile_agents.py
MAP_System/.venv/bin/python MAP_System/scripts/reconcile_agents.py
hcom list --json --name neko > /tmp/live-hcom-task140.json
MAP_System/.venv/bin/python MAP_System/scripts/reconcile_agents.py --hcom-json /tmp/live-hcom-task140.json
```

Focused test result:

```text
PASS test_reconcile_reports_stale_and_unregistered_agents
PASS test_reconcile_without_hcom_json_reports_not_checked
```

The full validation suite should still run before release review.
