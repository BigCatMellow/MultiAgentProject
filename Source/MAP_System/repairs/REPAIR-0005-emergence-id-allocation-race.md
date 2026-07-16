# Repair Record

Repair ID: REPAIR-0005
Related task: TASK-141
Found by: claude-lab-vino
Date: 2026-07-04
Severity: BLOCKING
Status: APPLIED

## What was found

`MAP_System/scripts/map_emergence.py`'s `create_artifact()` computed the
next sequential ID (`next_id()`, a plain scan of existing filenames for
the highest `PREFIX-NNNN`) and checked whether the target path already
existed, with no lock between the scan and the write. Two concurrent
`create` invocations for the same artifact kind could both read the same
highest ID and both pass the pre-write `path.exists()` check before
either had written, producing two different files that both claim the
same ID string — the same failure class as the `REPAIR-0001` collision
between dino's and valo's records, which `REPAIR-0004` fixed as one
specific instance (renaming the later record) rather than by adding a
general-purpose ID allocator to `repairs/`; `repairs/` itself still has
no atomic allocation mechanism today.

This directly contradicts an assumption in TASK-129's audit report
(`artifacts/audits/task-129-map-system-adherence-audit.md`, Finding 2),
which described `repairs/` as lacking atomic ID allocation "unlike
`map_task.py create --task-id auto` **or `map_emergence.py`'s ID
assignment**" — implying `map_emergence.py` was already safe. It was not;
that assumption was never verified against the code, only against the
absence of an observed collision.

## Surfaced by

Manual code read during TASK-141's systems-adherence follow-up (this task
was not investigating this file specifically; the gap was found while
checking whether the prior audit's claims about atomic ID allocation
still held).

## Severity rationale

BLOCKING, not STRUCTURAL: it is a straightforward, low-risk, mechanical
fix (a file lock around an existing code path, no schema or behavior
change to any artifact's content) with no judgment call or scope decision
involved — same class as REPAIR-0004's own fix. Not COSMETIC/DRIFT because
an actual collision would silently corrupt the emergence index (two
records sharing one ID) rather than just looking inconsistent.

## Proposed or applied fix

Added `id_allocation_lock()`, an `fcntl.flock`-based exclusive lock keyed
per artifact kind (`MAP_System/.locks/emergence-PREFIX.lock`, mirroring
the existing `.locks/` convention used by the limit watcher), and wrapped
`create_artifact()`'s ID computation, existence check, and file write
inside it. `next_id()` itself is unchanged; the fix serializes callers
around it instead of making the scan itself atomic, which is simpler and
sufficient since the whole allocate-check-write sequence now runs under
one lock per kind.

## Authority check

- [x] DRIFT or mechanical BLOCKING — core agent applied directly

## Verification

- Reproduced the race first: 8 concurrent `create insight` invocations
  against a temp copy of `MAP_System` with the fix reverted (`git stash`)
  produced 23 files but only 20 unique IDs (3 real collisions).
- Same test against the fixed code: 23 files, 23 unique IDs, 0 collisions.
- `python3 MAP_System/tests/test_map_emergence.py` — all 4 existing cases
  still pass (PASS on `test_create_all_kinds_and_rebuild_index`,
  `test_validate_rejects_unresolved_placeholders`,
  `test_validate_accepts_created_artifact`, `test_short_lab_contract`).
- `python3 MAP_System/scripts/map_emergence.py validate` — OK, 38 artifacts
  checked (unchanged from before the fix).
- `bash MAP_System/scripts/run_tests.sh` — 33/33 pass.

## Recurrence check

- [x] Repeat — logged in `shared/improvement-backlog.md`: this is the
  second instance of "no atomic ID allocation" found across MAP systems
  (first: `repairs/` itself, REPAIR-0004). The `repairs/` half of that
  backlog item (`map_repair.py` helper) is still open and not addressed
  by this repair — see `shared/improvement-backlog.md`.

## Notes

The `path.exists()` check inside `create_artifact()` is now effectively
redundant under the lock for auto-allocated IDs (the lock already
prevents two callers from computing the same ID), but it is kept as
defense-in-depth for the explicit `--artifact-id` case, where a caller
could still name a colliding ID on purpose or by mistake.
