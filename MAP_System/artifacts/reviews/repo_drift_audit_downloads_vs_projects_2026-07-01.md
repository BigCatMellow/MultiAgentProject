# Repo Drift Audit — Downloads/MultiAgentProject vs ~/Projects/MultiAgentProject

Owner: claude-lab-rose
Method: read-only Explore-agent survey (no files modified).
Part of the operator-requested full MAP-system audit (hcom #14289).

## Summary

Location A (`~/Downloads/MultiAgentProject`, this session's working copy) and
Location B (`~/Projects/MultiAgentProject`, referenced in Pathwell docs as
the two-repo sync target) are both real git repositories tracking the same
GitHub remote, but they are in a confusing, risky hybrid state — not simply
"B is behind."

## What's actually going on

- **A**: HEAD `5098156`, 7 commits, normal work-in-progress dirty state
  (today's task files, emergence records, handoffs).
- **B**: has a `.git` with `origin` → the correct GitHub remote, but HEAD is
  `631c144` — 4 commits and roughly two weeks behind A (frozen at 2026-06-17).
- **B's working tree is heavily dirty** against its own stale HEAD — dozens
  of files show as modified/deleted, plus a large pile of untracked content
  (`MAP_System/emergence/`, `agents/`, most current scripts, tasks through
  TASK-062) that matches what A already has *committed*. Someone copied newer
  files into B's working directory by hand at some point, without ever
  running `git add`/`git commit` there.
- **Pathwell chapters diverge for real**: A's Ch5-8/10/12 all differ from B's
  by word count and mtime (A is today, B is 2026-06-29). Most notably, **B
  still has the old unsplit Chapter_12.txt** — it never received today's
  TASK-020 pacing split into `Chapter_12.txt` + `Chapter_12b.txt`, confirming
  the sync-blocked issue flagged earlier this session.
- **B has a handful of files A doesn't** (`artifacts/planning/autonomous-claim-loop.md`,
  a couple of old notes, an old `project_state.json`/`project.yaml`, an older
  handoff snapshot) — all identifiable as cruft that A's later cleanup
  commits (`31d2e52`, `2941fb1`) intentionally removed or renamed. Nothing of
  current value exists in B that doesn't already exist in A.

## Risk

B is not just stale — it's a **hybrid**: old committed history plus newer
uncommitted files mixed in ad hoc. If anyone runs `git add -A && git commit`
in B as-is, it produces a strange commit that doesn't cleanly match A's
actual state, and pushing it to GitHub risks either a confusing history or a
conflict against whatever A eventually pushes. This is a live risk, not just
a housekeeping note — B is in a git-tracked repo pointed at a real remote.

## Recommendation

Do not push from B in its current state. Before treating B as the sync
target again:
1. Decide whether A or B should be canonical going forward (A is clearly
   ahead and is where today's work happened — recommend A).
2. Either reset B to match A's working tree exactly and commit that as one
   clean sync commit, or delete/re-clone B from GitHub after A is pushed.
3. Re-run the Pathwell two-repo sync (blocked earlier today by a safety
   classifier treating the copy as an out-of-scope destination) once B is
   reconciled, not before — copying now would layer more drift onto an
   already-inconsistent target.

This should be a bigboss decision, not something either lab agent resolves
unilaterally — it touches git history on a repo with a live GitHub remote.
