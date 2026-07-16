# MAP Formal Invariant Spike (TASK-157, Wave 9)

Status: draft-active
Owner: command-center
Built by: TASK-157

## Purpose

This spike narrows formal verification to the MAP invariants most likely to
fail under concurrency: allocator uniqueness, task-claim exclusivity, and git
operation lock mutual exclusion. It follows the 6.13 formal-verification note:
prove a small design model, not the whole system.

## Scope

Covered:

- allocator: no duplicate task IDs;
- task claim: at most one active owner per task;
- git lock: at most one writer holds the operation lock;
- termination cleanup: a stopped agent cannot retain lock/claim forever in the
  abstract model.

Out of scope:

- semantic correctness of task outputs;
- exact Python implementation equivalence;
- all possible hcom delivery behaviors;
- all filesystem or Git edge cases;
- liveness guarantees beyond bounded cleanup/release.

## TLA+ Path

The preferred formal path is TLA+ with 2-3 abstract agents and a small task
set. The minimal safety invariants are:

```text
UniqueTaskIds == Cardinality(task_ids) = Cardinality(allocated_ids)
SingleClaimOwner == \A t \in Tasks : Cardinality(claimed_by[t]) <= 1
SingleGitLockHolder == Cardinality(git_lock_holders) <= 1
NoStoppedOwner == \A a \in StoppedAgents : a \notin git_lock_holders
```

The model should include nondeterministic interleavings:

- two agents allocate concurrently;
- two agents claim the same ready task;
- one agent dies while holding a claim or lock;
- one agent releases while another attempts to claim;
- one agent exports while another attempts a graph mutation.

TLC pass criteria:

- no duplicate task IDs are reachable;
- no task has two simultaneous active claim owners;
- no two agents hold the git operation lock at once;
- a stopped agent either releases in the model or becomes an explicit stale
  state handled by reaper/dead-letter policy;
- deadlock traces, if any, are documented as model limitations or design bugs.

## Executable State-Machine Test Sketch

If TLA+ tooling is not installed or approved, use a Python state-machine test
as a bounded executable proxy. The test does not prove the implementation, but
it catches bad abstract transition designs and creates regression fixtures.

Allocator property:

```python
def invariant_unique_ids(state):
    ids = [task.task_id for task in state.tasks]
    assert len(ids) == len(set(ids))

def allocate_task(state, agent):
    next_id = state.counter + 1
    state.counter = next_id
    state.tasks.append(Task(task_id=f"TASK-{next_id:03d}", created_by=agent))
```

Task-claim property:

```python
def invariant_single_claim_owner(state):
    for task in state.tasks:
        owners = [claim.agent for claim in state.claims if claim.task_id == task.task_id and claim.active]
        assert len(owners) <= 1

def claim_task(state, agent, task_id):
    if not state.task(task_id).ready:
        return
    if any(c.active and c.task_id == task_id for c in state.claims):
        return
    state.claims.append(Claim(task_id=task_id, agent=agent, active=True))
```

Git-lock property:

```python
def invariant_single_git_lock_holder(state):
    assert len(state.git_lock_holders) <= 1

def acquire_git_lock(state, agent):
    if state.git_lock_holders:
        return
    state.git_lock_holders.add(agent)
```

Bounded scheduler:

```python
for seed in range(200):
    state = initial_state(agent_count=3, task_count=3)
    for step in randomized_interleavings(seed, steps=50):
        apply(step, state)
        invariant_unique_ids(state)
        invariant_single_claim_owner(state)
        invariant_single_git_lock_holder(state)
```

Required bad-case fixtures:

- unlocked allocator race should produce a duplicate in the broken model;
- claim without compare-and-set should produce two owners in the broken model;
- lock acquire without atomic check should produce two holders in the broken
  model;
- agent termination without cleanup should produce an orphan lock or stale
  claim state.

## Design-Vs-Implementation Limits

Formal or state-machine verification proves only the model's transitions. MAP
still needs implementation checks:

- `test_map_task_auto_id.py` for actual allocator behavior;
- `test_git_operation_lock.py` for lock behavior;
- `test_exporter_invariants.py` and `validate_task_mirrors.py` for canonical
  mirror agreement;
- task-claim DB tests for SQLite transition behavior.

Bridging requirement: every model transition must map to a named Python helper
or CLI action. If implementation code can mutate state outside those helpers,
the proof does not cover that path.

## Recommendation

Do not specify all MAP in TLA+. Start with executable state-machine tests in
the existing Python test suite, then translate only the allocator/claim/lock
model to TLA+ if the Python model finds value or if concurrency work expands.
This keeps the proof effort proportional to the highest-risk invariants.
