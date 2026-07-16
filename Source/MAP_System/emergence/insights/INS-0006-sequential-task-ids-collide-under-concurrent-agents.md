# Insight Record

Insight ID: INS-0006
Project: MAP
Related task: TASK-020/TASK-023/TASK-024 (Pathwell)
Detected by: claude-lab-rose
Date: 2026-07-01
Status: PROMOTED

## Short description

Two concurrently active agents choosing "the next task ID" by inspecting the
task directory independently will sometimes pick the same ID, because
neither agent's read-then-write is atomic against the other's.

## Trigger

During a Pathwell MAP-system test, claude-lab-rose and codex-lab-limo both
independently created a task file named `TASK-023.json` for two different,
unrelated pieces of work within the same session. The collision wasn't
caught until claude-lab-rose wrote its own TASK-023.json and a later Read
surfaced limo's already-approved TASK-023.json with different content — at
which point claude-lab-rose, while trying to fix the collision quickly,
accidentally ran `rm` on limo's live, approved task file. It was restored
immediately from content already in context, but the near-loss was
avoidable.

## The synthesis

"Check the directory, then use the next free number" is not a claim
operation — it's a race condition whenever more than one agent can act in
the same window. This is the same class of problem `db/claims.py` already
solves for task *claiming*, but nothing currently guards task *ID
allocation* the same way, especially in per-project MAP_System instances
(like Pathwell's) that don't share the root project's SQLite claims layer at
all.

## Why it might matter

This will recur any time two core agents (or a core agent plus a helper) are
both creating new tasks in the same project during overlapping work — which
is exactly the kind of parallel, low-hand-holding operation command-center
has been asking for more of, not less. As agents get less supervised
turn-by-turn, this failure mode gets more likely, not less.

## Evidence

- Pathwell `MAP_System/tasks/TASK-023.json` (codex-lab-limo, back-half
  mechanical cleanup, APPROVED) vs. claude-lab-rose's independently created
  `TASK-023.json` (expansion pass) — same session, 2026-07-01.
- hcom transcript: collision caught only by chance (a file-modification
  system note), not by any tooling.

## Risk

If unaddressed, a future collision could go unnoticed rather than caught,
silently corrupting task history or causing one agent's approved work to be
overwritten by another's in-progress draft.

## Scope

- [ ] Inside the current task
- [ ] Adjacent to the current task
- [ ] A project-level idea
- [x] A MAP-system-level improvement

## Recommended next action

- [ ] Ignore — not worth preserving
- [ ] Park for later — valid but low priority
- [x] Create follow-up task — actionable now
- [ ] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

Smallest safe fix: before creating a new task file, an agent should announce
the intended ID via hcom (`inform`, not `request`) and pause briefly for a
same-window collision, the same discipline already used for file-edit
lanes in this session. A more durable fix would extend project-local
task-numbering to use a shared counter or timestamp-suffixed IDs
(`TASK-023-rose`, or a UUID-suffixed scratch ID promoted to a clean number
on approval) rather than trusting a directory listing to stay accurate
between read and write.

## Lifecycle close-out (2026-07-02, TASK-075)

Promoted via IDEA-0006 into TASK-065 (MAP audit remediation batch), whose acceptance criteria include SQLite-backed atomic task ID allocation -- the exact fix this insight recommended. Closed during TASK-075.
