"""
MAP CHAOS ENGINEERING — a different kind of test.
Previous rounds optimized cost. This one INJECTS FAULTS and measures survival.

The synthesized doc asserts a resilience layer (idempotency keys, dead-letter
queue, circuit breakers, blast-radius containment) but never tested it. Do these
mechanisms actually help under failure — or are some of them Braess again?

FAULTS injected each run:
  - crash: an agent dies mid-task (work lost, must be retried)
  - timeout: a task hangs (looks like failure, may actually have half-completed)
  - corrupt_write: an agent writes BAD state to the shared store; if not contained,
                   downstream tasks that READ that state are poisoned (cascade)

RESILIENCE MECHANISMS (each toggleable, so we can test their marginal value):
  - idempotency : retries after crash/timeout don't double-apply the write
  - deadletter  : failed tasks go to an inspectable queue and get retried;
                  without it, a failed task is simply LOST
  - breaker     : after N consecutive failures from one agent, stop routing to it
  - blastradius : a corrupt write is isolated to its own task; downstream readers
                  are protected. Without it, one bad write poisons everything
                  that reads the shared state before it's caught.

We measure: completed, lost, cascaded (poisoned by bad state), and total work cost.
Then we run the Braess test: full stack vs each mechanism removed vs none.
"""
import random, statistics, collections

class ChaosResult:
    def __init__(self):
        self.completed=0; self.lost=0; self.cascaded=0
        self.retries=0; self.double_applies=0; self.work=0
        self.breaker_trips=0

def run(seed, n_tasks=500,
        p_crash=0.10, p_timeout=0.08, p_corrupt=0.06,
        idempotency=True, deadletter=True, breaker=True, blastradius=True,
        breaker_threshold=3):
    rng=random.Random(seed)
    r=ChaosResult()
    # shared state can be 'poisoned' by an uncontained corrupt write
    poison_pending=0        # number of corrupt writes currently live in shared state
    agent_fail_streak=collections.Counter()
    disabled_agents=set()
    agents=[f"A{i}" for i in range(4)]

    queue=list(range(n_tasks))
    task_attempts=collections.Counter()

    while queue:
        tid=queue.pop(0)
        # pick an agent that isn't circuit-broken
        live=[a for a in agents if a not in disabled_agents] or agents
        agent=rng.choice(live)
        task_attempts[tid]+=1
        r.work += 1

        # a task reading poisoned state gets cascaded (unless blast-radius contains it)
        if poison_pending>0 and not blastradius:
            # probability this task reads the poisoned state
            if rng.random() < 0.5:
                r.cascaded+=1
                # cascaded task itself produces bad output -> more poison
                poison_pending+=1
                continue

        # inject faults
        roll=rng.random()
        if roll < p_crash:
            # agent crashed mid-task
            agent_fail_streak[agent]+=1
            if not idempotency:
                # crash may have half-applied a write that gets re-applied on retry
                if rng.random()<0.5: r.double_applies+=1
            if deadletter:
                queue.append(tid); r.retries+=1     # retried later
            else:
                r.lost+=1                            # dropped, never completes
        elif roll < p_crash+p_timeout:
            agent_fail_streak[agent]+=1
            if deadletter:
                queue.append(tid); r.retries+=1
            else:
                r.lost+=1
        elif roll < p_crash+p_timeout+p_corrupt:
            # agent produced a corrupt write
            agent_fail_streak[agent]+=1
            if blastradius:
                # contained: bad write isolated, task fails but no cascade; retry
                if deadletter: queue.append(tid); r.retries+=1
                else: r.lost+=1
            else:
                # uncontained: poison enters shared state
                poison_pending+=1
                if deadletter: queue.append(tid); r.retries+=1
                else: r.lost+=1
        else:
            # success
            agent_fail_streak[agent]=0
            r.completed+=1
            # a successful write on a poisoned store slowly cleans it (re-sync)
            if poison_pending>0 and blastradius: poison_pending=max(0,poison_pending-1)

        # circuit breaker: disable an agent with too many consecutive failures
        if breaker and agent_fail_streak[agent]>=breaker_threshold and agent not in disabled_agents:
            disabled_agents.add(agent); r.breaker_trips+=1
            agent_fail_streak[agent]=0
        # occasionally re-enable a disabled agent (recovery)
        if breaker and disabled_agents and rng.random()<0.05:
            disabled_agents.pop()

        # safety valve: prevent infinite retry loops
        if task_attempts[tid]>=6 and tid in queue:
            queue.remove(tid); r.lost+=1

    return r

def summarize(r, n_tasks=500):
    return dict(
        completed=r.completed, lost=r.lost, cascaded=r.cascaded,
        success_rate=r.completed/n_tasks, work=r.work,
        double_applies=r.double_applies, breaker_trips=r.breaker_trips)

def avg(seeds=8, **kw):
    rs=[summarize(run(seed=s,**kw)) for s in range(seeds)]
    return {k:statistics.mean([r[k] for r in rs]) for k in rs[0]}

if __name__=="__main__":
    print("CHAOS TEST — inject crashes/timeouts/corruption, measure survival\n")
    print("Baseline fault load: 10% crash, 8% timeout, 6% corrupt-write per attempt\n")

    print("TEST 1 — full resilience stack vs NO resilience")
    print(f"{'config':>22} {'success':>8} {'lost':>6} {'cascaded':>9} {'work':>7}")
    full=avg(idempotency=True,deadletter=True,breaker=True,blastradius=True)
    none=avg(idempotency=False,deadletter=False,breaker=False,blastradius=False)
    print(f"{'FULL STACK':>22} {full['success_rate']*100:>7.1f}% {full['lost']:>6.0f} {full['cascaded']:>9.0f} {full['work']:>7.0f}")
    print(f"{'NONE':>22} {none['success_rate']*100:>7.1f}% {none['lost']:>6.0f} {none['cascaded']:>9.0f} {none['work']:>7.0f}")

    print("\nTEST 2 — Braess check: remove ONE mechanism at a time from full stack")
    print("(big drop in success or spike in lost/cascaded = that mechanism earns its place)")
    print(f"{'removed':>22} {'success':>8} {'lost':>6} {'cascaded':>9} {'dbl_apply':>10} {'work':>7}")
    base=dict(idempotency=True,deadletter=True,breaker=True,blastradius=True)
    print(f"{'(nothing removed)':>22} {full['success_rate']*100:>7.1f}% {full['lost']:>6.0f} {full['cascaded']:>9.0f} {full['double_applies']:>10.1f} {full['work']:>7.0f}")
    for mech in ("idempotency","deadletter","breaker","blastradius"):
        kw=dict(base); kw[mech]=False
        a=avg(**kw)
        print(f"{'- '+mech:>22} {a['success_rate']*100:>7.1f}% {a['lost']:>6.0f} {a['cascaded']:>9.0f} {a['double_applies']:>10.1f} {a['work']:>7.0f}")

    print("\nTEST 3 — stress: crank fault load up (does the stack still hold?)")
    print(f"{'fault load':>22} {'success':>8} {'lost':>6} {'cascaded':>9}")
    for mult,label in ((1,'baseline'),(2,'2x faults'),(3,'3x faults')):
        a=avg(p_crash=0.10*mult,p_timeout=0.08*mult,p_corrupt=0.06*mult)
        print(f"{label:>22} {a['success_rate']*100:>7.1f}% {a['lost']:>6.0f} {a['cascaded']:>9.0f}")

    print("\n"+"="*60)
    print("Reading it: any mechanism whose removal barely changes the numbers is a")
    print("Braess candidate (cut it). Any whose removal craters survival is load-bearing.")
