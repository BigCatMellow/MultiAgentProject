# MAP System Full Report

Prepared for: command-center / bigboss  
Prepared by: codex-lab-limo  
With input from: claude-lab-rose  
Date: 2026-07-02  
MAP task: TASK-064  
Primary audit basis: TASK-063

## Executive Summary

MAP is no longer theoretical. It is already doing useful work:

- tasks are tracked durably;
- SQLite claims prevent some ownership mistakes;
- review and release gates have caught real bugs;
- hcom keeps live agent coordination visible;
- artifacts, events, handoffs, and task graphs make work reconstructable;
- the AI Command Center Lab has working health checks and visible helper rules;
- the emergence system produced one genuinely valuable project artifact in Pathwell.

The system's main failures are not in the core idea. They are in the seams:

- repo copies are drifting and can corrupt history if pushed from the wrong place;
- task IDs are still manually chosen and can collide under concurrent agents;
- emergence records are captured but not reliably closed, promoted, dismissed, or cleaned;
- agents still start some work before formal intake/ownership is established;
- durable agent status is stale compared with hcom live state;
- event records are valid JSONL but inconsistent in schema and type names;
- operator approval calibration is uneven: agents sometimes ask too much after direction is set, but also sometimes do too much before ownership is clear.

The shortest honest diagnosis:

> MAP works as a coordination scaffold, but it needs fewer manual habits in the critical paths: task ID allocation, repo ownership, emergence lifecycle, event normalization, and request intake.

The highest-priority fixes are:

1. Declare one canonical repo and reconcile the stale `/home/home/Projects/MultiAgentProject` copy.
2. Add atomic task ID allocation.
3. Add stale-emergence reporting and clean placeholder emergence records.
4. Add an operator-request intake rule that assigns one owner quickly.
5. Add a Git operation lock.
6. Normalize event schema and live agent availability reporting.

## Current System Shape

### MAP

MAP is the durable coordination and memory layer. It records:

- task identity and state;
- owners, reviewers, dependencies, outputs, acceptance criteria;
- events and handoffs;
- shared state, decisions, requirements, and unresolved questions;
- artifacts from reviews, tests, releases, planning, and reports.

In this repo, the active MAP system is:

`/home/home/Downloads/MultiAgentProject/MAP_System`

### HPOM

HPOM is the assignment layer over MAP: the Human-Paced Orchestration Model.

It answers who or what should do the work:

- command-center / human;
- core agents;
- visible helper agents;
- local/Ollama assistants;
- Aider.

The principle is good and should stay:

> Use the cheapest competent worker, but keep authority with the right owner.

### hcom

hcom is the live coordination bus. It is good for:

- agent-to-agent status;
- operator attention;
- collision warnings;
- visible helper launch coordination.

hcom should not be the only memory. Important results must still land in MAP files.

### Emergence

Emergence is the idea-discovery layer. It captures:

- insights;
- synthesis notes;
- ideas;
- experiments;
- promotions.

It is intentionally separate from HPOM. That separation is correct:

- emergence can notice possibilities;
- HPOM decides what becomes real work.

## Validation Snapshot

Recent validation results from the audit/report pass:

- `validate_task_graph.py`: passed.
- `validate_shared_state.py`: 16 files checked, 0 failures, 0 warnings.
- `validate_decisions.py`: 11 decisions checked, 0 failures.
- `map_emergence.py validate`: passed, 16 artifacts checked after INS-0007.
- events JSONL parse check: passed.
- `map_metrics.py`: review queue size 1 during TASK-063 submission; conflict count 0; stale shared file count 0.
- `ai-command-center-lab-status`: 24 passed, 0 warnings, 0 failed.

This means the system is internally coherent enough to keep using while fixing its weaker edges.

## What Works

### 1. Durable Task Records Work

The task graph and per-task JSON files are understandable. They let agents reconstruct:

- what the task was;
- who owned it;
- what files were expected to change;
- what acceptance criteria mattered;
- what state the task reached.

Recent examples:

- `TASK-054` through `TASK-062` handled DarkMellow and CommandCenterUI work with real tasks, reviews, release checklists, and events.
- `TASK-063` captured the system audit.
- `TASK-064` captures this full report.

### 2. SQLite Claiming Catches Real Ownership Errors

The no-self-review claim gate works.

Evidence:

- When TASK-063 was initially created as a review task owned by `codex-lab-limo`, the claim helper rejected it as `self_review`.
- That prevented a review-shaped task from being claimed by its own reviewer.

This is exactly the kind of mechanical guard MAP needs more of.

### 3. Review Gates Catch Real Bugs

The review process is not ceremonial. It caught real problems:

- CommandCenterUI initially risked false hcom attribution by sending/listing as the wrong identity.
- CommandCenterUI later had a real CSRF issue on a local write endpoint.
- DarkMellow's visible release ZIP was stale even though source-tree fixes existed.
- Pathwell review caught pacing, earnedness, and continuity issues.

That means the review layer is useful.

### 4. Release Gates Improve User-Facing Safety

Release checklists forced agents to verify:

- package contents;
- README consistency;
- installer paths;
- remote GitHub state;
- not just source tree diffs.

The DarkMellow stale ZIP problem is the best proof: source code looked improved, but the user-visible acquisition path was still wrong. MAP captured that as an insight (`INS-0005`).

### 5. Lab Visibility Rules Are Healthy

The AI Command Center Lab docs and health checks support the operator's visibility requirements:

- helpers use visible `wezterm-tab`;
- headless is disallowed unless explicitly requested;
- Monitor is attention-only;
- `request` vs `inform` hcom messages are documented.

The lab health check passing 24/24 is meaningful. It shows this layer is not just written down; it is testable.

### 6. Emergence Can Produce Real Value

Pathwell proved the emergence system can work when the loop is closed.

The best example:

- insight: unpaid plot debts must be paid on page;
- idea: debt-payment pass;
- promotion: reusable review pattern;
- artifact: `Projects/Pathwell/Story_Files/debt_payment_checklist.md`.

That artifact directly improved later Pathwell review and expansion behavior.

## What Does Not Work

### F1. Repo Canonicality Is Unsafe

The biggest live operational risk is repo drift.

There are two important repo locations:

- A: `/home/home/Downloads/MultiAgentProject`
- B: `/home/home/Projects/MultiAgentProject`

Claude's repo-drift audit found:

- A is current for this session's MAP and Pathwell work.
- B has the same GitHub remote, but its HEAD is stale.
- B's working tree contains manually copied newer files that were not committed there.
- B's Pathwell chapters lack today's Chapter 12 split.
- B is a hybrid of stale git history and ad hoc copied newer content.

Why it fails:

MAP assumes file-backed truth, but two repo copies now claim to hold similar truth. Git history and working tree state disagree in B.

How to fix:

1. Bigboss chooses one canonical working repo.
2. Recommended: declare A (`/home/home/Downloads/MultiAgentProject`) canonical because current validated work happened there.
3. Do not push from B.
4. After A is reviewed/pushed, either reset/reclone B or intentionally sync it with a clean plan.

Priority: P0.

### F2. Task ID Allocation Is Not Atomic

The system has atomic claiming, but not atomic task ID creation.

Evidence:

- During Pathwell work, both agents collided around `TASK-023`.
- Claude nearly removed the wrong task file while fixing the collision.
- This became `INS-0006` / `IDEA-0006`.

Why it fails:

Agents choose "next task ID" by reading the task directory or graph. Two agents can read the same latest ID and both choose the same next ID.

How to fix:

- Add `map_task.py next-id` or make `map_task.py create --task-id auto` allocate IDs inside SQLite transaction.
- The allocator should reserve the ID and write the task in one operation.
- Agents should stop manually choosing IDs for normal tasks once this exists.

Priority: P0/P1.

### F3. Emergence Records Are Captured But Not Closed

The emergence system validates shape, not lifecycle quality.

Current issues:

- root `INS-0002`, `INS-0003`, `IDEA-0002`, `IDEA-0003` are placeholder stubs with literal `text`;
- root `PROMO-0002` and `PROMO-0003` contain `IDEA-####`;
- root emergence CLI records remain RAW/CANDIDATE/PROPOSED even though `TASK-052` is released;
- zero synthesis or experiment records have been used;
- Pathwell is the only complete insight -> idea -> promotion -> artifact example.

Why it fails:

Capture is one-way. Nothing asks "what happened to this insight?" when a related task closes.

How to fix:

- Add `map_emergence.py stale`.
- Add stricter content validation mode.
- Flag placeholder strings: `text`, `TBD`, `IDEA-####`, blank required sections.
- Cross-reference `Related task` against task state.
- If related task is APPROVED/RELEASED, require the emergence record to be PROMOTED, PARKED, DISMISSED, or SUPERSEDED.
- Clean existing stubs.

Priority: P1.

### F4. Operator Intake Is Not Yet Reliable Enough

Ad-hoc work still sometimes starts before MAP ownership is clear.

Evidence:

- event log contains `AD-HOC-Onion-PocketOS`, `AD-HOC-DarkMellow`, `AD-HOC-CommandCenterUI-discoverability`, `AD-HOC-log-subcommand`;
- some became formal tasks later;
- some remained ad hoc;
- operator had to remind agents to stop hand-holding and use the system.

Why it fails:

There is no mandatory first step when the operator gives a broad request. Agents may begin useful work immediately, but without one owner, one task, or one review path.

How to fix:

- Add a lightweight intake protocol:
  - classify request;
  - choose worker fit;
  - assign owner;
  - identify reviewer/support;
  - decide whether it needs a task or bounded ad-hoc record;
  - announce the split via hcom.
- Do this before substantive edits, not after.

Priority: P1.

### F5. Approval Calibration Is Uneven

There are two opposite failure modes:

- asking too much after direction is already clear;
- acting too much before ownership is clear.

Evidence:

- During Pathwell, command-center explicitly pushed for fewer check-ins and more autonomous follow-through once a pattern was approved.
- Earlier gates around manuscript changes caused agents to pause even when the operator wanted the system to execute approved low-risk work.
- Conversely, ad-hoc work sometimes began before formal ownership existed.

Why it fails:

MAP has strong safety instincts but does not distinguish enough between:

- "need operator intent";
- "need peer review";
- "safe to continue under established direction";
- "must stop because ownership is unclear."

How to fix:

- Add an approval calibration rule:
  - Ask command-center for canon, destructive actions, repo canonicality, publication, privacy/scope risks, or unresolved intent.
  - Use peer review for implementation/prose quality when direction is clear.
  - Continue autonomously for low-risk changes under an approved pattern.
  - Do not start editing if ownership is unclear.

Priority: P1.

### F6. Agent Availability State Is Stale

`MAP_System/agents/status.json` lists many historical agents as available, while hcom showed only `claude-lab-rose` and `codex-lab-limo` active.

Why it fails:

The file is being used as a capability/history list more than a live availability source.

How to fix:

- Separate durable capability registry from live session status.
- Add a reconcile command that compares `agents/status.json` with `hcom list`.
- Mark historical lab agents as inactive/session-ended unless they are actually live.

Priority: P2.

### F7. Event Log Schema Is Inconsistent

The event log parses, but has multiple shapes.

Observed:

- most entries use `created_at`, some use `timestamp`;
- most use `sender`, some use `agent`;
- type aliases exist: `APPROVED` / `REVIEW_APPROVED`, `CHANGES_REQUESTED` / `REVIEW_CHANGES_REQUESTED`, `PROGRESS` / `task_progress`.

Why it fails:

Agents and scripts append events from different eras and helpers without a single validator enforcing canonical fields.

How to fix:

- Add `validate_events.py`.
- Warn, do not immediately fail, on legacy shapes.
- Teach metrics to group aliases.
- Prefer canonical fields going forward:
  - `created_at`
  - `type`
  - `task_id`
  - `sender`
  - `summary`
  - `artifact_paths`

Priority: P2.

### F8. Non-MAP Projects Have Mixed Coordination Systems

Survey:

- `ChainShovel`: simple app folder, no MAP state.
- `PixelAnimator`: simple app folder, no MAP state.
- `AI Command Center`: lab docs align with MAP.
- `Onion-workbench`: older `claude-code-comms` task/handoff files still exist.

Why it fails:

This is not a universal failure. Tiny projects do not need MAP. The risk is Onion-workbench: it has enough multi-agent history to need coordination, but it uses older coordination files plus root MAP ad-hoc events.

How to fix:

- Do not force MAP into simple projects.
- If Onion-workbench becomes active again, choose one:
  - create project-local MAP;
  - or keep root MAP tasks that explicitly point to Onion paths.
- Add a bridging note if old `claude-code-comms` remains historical only.

Priority: P2/P3.

### F9. `map_task.py create` Allows Some Bad Shapes

The no-self-review gate blocked a bad claim, but only after task creation.

Why it fails:

Creation and claiming are separate. The create command does not warn that a self-owned review task will later be unclaimable by that same agent.

How to fix:

- Add create-time warning for `task_type=review` or `role=reviewer` with same owner as intended claimer.
- Better: add `--reviewer` separate from `--owner`, and make task shape clearer.

Priority: P3.

## Things To Add

### 1. Atomic Task ID Allocator

Add:

```bash
python3 MAP_System/scripts/map_task.py create --task-id auto ...
```

or:

```bash
python3 MAP_System/scripts/map_task.py next-id
```

Requirements:

- SQLite transaction;
- reserves the ID;
- refuses collisions;
- exports file mirrors immediately;
- emits event.

### 2. Git Operation Lock

Add a repo-global lock for:

- commit;
- push;
- pull;
- branch reset;
- release publication;
- cross-repo sync.

Minimum viable form:

- `MAP_System/.locks/git-operation.json`;
- owner, repo path, operation, start time, expected stop condition;
- hcom announcement required.

### 3. Emergence Stale Report

Add:

```bash
python3 MAP_System/scripts/map_emergence.py stale
```

Flags:

- placeholder content;
- dangling IDs;
- open records tied to closed tasks;
- promotions without approval;
- old RAW/CANDIDATE records past threshold.

### 4. Event Validator

Add:

```bash
python3 MAP_System/scripts/validate_events.py
```

Modes:

- `--warn-legacy`;
- `--strict-new`;
- `--json`.

### 5. Agent Availability Reconcile

Add:

```bash
python3 MAP_System/scripts/reconcile_agents.py
```

or hcom-aware report:

- durable known agents;
- live hcom agents;
- stale lab identities;
- mismatches.

### 6. Operator Intake Script Or Checklist

Add a small intake helper:

```bash
python3 MAP_System/scripts/intake_request.py --summary "..."
```

Output:

- task needed? yes/no;
- owner recommendation;
- reviewer recommendation;
- helper/local model fit;
- hcom announcement text.

Do not over-automate this. Start as a checklist/report.

### 7. Canonical Repo Marker

Add a durable file after command-center decides:

```text
MAP_System/shared/canonical-repo.md
```

It should say:

- canonical local path;
- sync targets;
- push rules;
- forbidden stale locations;
- last verified date.

## Things To Change

### 1. Change From "Capture Emergence" To "Manage Emergence Lifecycle"

Current habit:

- capture insight;
- maybe create idea;
- move on.

Needed habit:

- capture;
- link to task;
- revisit at task close;
- promote, park, dismiss, or supersede.

### 2. Change From Manual Task IDs To Tool-Assigned IDs

Manual IDs are fragile under concurrency. They should become exceptional.

### 3. Change From "Ask For Approval Often" To "Ask At The Right Gate"

Use command-center attention for:

- operator intent;
- repo canonicality;
- external publication;
- destructive actions;
- privacy/scope risks;
- real blockers.

Use agent judgment and peer review for:

- low-risk execution under approved direction;
- routine validation;
- report drafting;
- non-destructive cleanup proposals.

### 4. Change Event Writing To One Canonical Shape

Keep old events, but new events should use one shape.

### 5. Change Agent State Into Two Concepts

Separate:

- durable capability registry;
- live hcom session availability.

## Things To Stop Doing

- Do not push or sync from `/home/home/Projects/MultiAgentProject` until it is reconciled.
- Do not manually pick next task IDs during concurrent sessions once allocator exists.
- Do not leave emergence smoke-test artifacts in the active index.
- Do not start broad edit work from hcom before a single owner is announced.
- Do not use `agents/status.json` alone as live truth.
- Do not treat Desktop/browser visibility as the same thing as hcom agent identity.

## Things To Keep Doing

- Keep visible helper tabs.
- Keep hcom request/inform discipline.
- Keep review gates for write-capable/network-facing tools.
- Keep release-path reviews for user-facing packages.
- Keep durable artifacts instead of relying on chat memory.
- Keep using project-local MAP for substantial projects like Pathwell.
- Keep using emergence for real patterns, especially when an insight generalizes beyond one task.

## Proposed Roadmap

### Phase 0: Safety Freeze

Do immediately.

1. Declare `/home/home/Downloads/MultiAgentProject` or `/home/home/Projects/MultiAgentProject` canonical.
2. Until then, no push from B and no two-repo Pathwell sync.
3. Record decision in `shared/decisions.md` or new `shared/canonical-repo.md`.

### Phase 1: Coordination Integrity

Do next.

1. Implement atomic task ID allocation.
2. Implement Git operation lock.
3. Add operator-request intake checklist.

These prevent collisions and duplicated work.

### Phase 2: Emergence Cleanup

Do after Phase 1 or in parallel if safe.

1. Add stale-emergence report.
2. Clean placeholder records.
3. Close root emergence CLI records related to TASK-052.
4. Decide what to do with unused synthesis/experiment paths: keep and test, or explicitly mark as advanced/optional.

### Phase 3: Observability Cleanup

1. Add event validator.
2. Normalize metrics aliases.
3. Add agent availability reconcile.
4. Update current-state after these changes.

### Phase 4: Project Portfolio Hygiene

1. Decide Onion-workbench coordination path.
2. Leave ChainShovel and PixelAnimator alone unless they become multi-agent.
3. Keep AI Command Center Lab as the test surface, but ensure lab changes feed back into root MAP tasks when they become general.

## Recommended Next Tasks

### TASK-A: Decide Canonical Repo

Owner: bigboss  
Type: decision  
Priority: P0

Decision:

- A: `/home/home/Downloads/MultiAgentProject`
- B: `/home/home/Projects/MultiAgentProject`

Recommendation: A.

### TASK-B: Atomic Task ID Allocation

Owner: Codex  
Reviewer: Claude  
Priority: P0/P1

Output:

- `map_task.py create --task-id auto`;
- tests for concurrent allocation;
- docs update.

### TASK-C: Git Operation Lock

Owner: Codex  
Reviewer: Claude  
Priority: P1

Output:

- lock file or SQLite lock;
- hcom announcement template;
- refusal/warning when lock exists.

### TASK-D: Emergence Stale Report

Owner: Codex  
Reviewer: Claude  
Priority: P1

Output:

- `map_emergence.py stale`;
- content quality checks;
- related-task lifecycle checks.

### TASK-E: Emergence Index Cleanup

Owner: Claude  
Reviewer: Codex / bigboss for decisions  
Priority: P1

Output:

- stubs dismissed or archived;
- TASK-052 emergence records closed;
- root index rebuilt.

### TASK-F: Event Validator

Owner: Codex  
Reviewer: Claude  
Priority: P2

Output:

- `validate_events.py`;
- canonical schema docs;
- metrics alias grouping.

### TASK-G: Agent Availability Reconcile

Owner: Codex  
Reviewer: Claude  
Priority: P2

Output:

- report comparing hcom live agents and durable status file;
- clarified semantics in shared state.

### TASK-H: Approval Calibration Guide

Owner: Claude  
Reviewer: Codex / bigboss  
Priority: P1/P2

Output:

- short policy: when to ask command-center, when to continue, when to peer review, when to stop for ownership.

## Final Assessment

MAP should continue. It is already useful.

But the next improvement cycle should be less about adding big new concepts and more about making the current concepts reliable:

- one canonical repo;
- one atomic way to create tasks;
- one owner before edits;
- one lifecycle for emergence records;
- one event schema;
- one live-vs-durable agent status distinction;
- one approval calibration rule.

The system's strongest pattern is also its weakness: it makes work visible, but it still relies on agents remembering to close loops manually. The fixes above should move those loops into tools and validators without making the system heavy.

