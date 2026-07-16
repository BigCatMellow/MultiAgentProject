"""
CIRCUIT BREAKER — a fair test.
The chaos round found the breaker did almost nothing. But its purpose is NOT
uniform random failure — it's a SINGLE PERSISTENTLY BROKEN agent (bad deploy,
wedged local model, a node that's just sick). Test it under that condition, which
is what it actually exists for. If it still does nothing, cut it. If it saves the
run when one agent goes bad, keep it — the earlier test was just unfair to it.

Scenario: 4 agents, but ONE of them is 'sick' — it fails most tasks it touches.
Without a breaker, the router keeps handing it work (and it keeps failing/retrying,
or poisoning state). With a breaker, after N failures it's pulled from rotation.
"""
import random, statistics, collections

def run(seed, n_tasks=500, sick_agent_fail=0.85, breaker=True,
        breaker_threshold=3, blastradius=True, deadletter=True):
    rng=random.Random(seed)
    agents=["A0","A1","A2","SICK"]
    streak=collections.Counter(); disabled=set()
    queue=list(range(n_tasks)); attempts=collections.Counter()
    completed=lost=cascaded=work=0; poison=0
    routed_to_sick=0

    while queue:
        tid=queue.pop(0)
        live=[a for a in agents if a not in disabled] or agents
        agent=rng.choice(live)
        if agent=="SICK": routed_to_sick+=1
        attempts[tid]+=1; work+=1

        if poison>0 and not blastradius and rng.random()<0.5:
            cascaded+=1; poison+=1; continue

        # the sick agent fails most of the time; healthy agents rarely fail
        p_fail = sick_agent_fail if agent=="SICK" else 0.04
        if rng.random() < p_fail:
            streak[agent]+=1
            # a sick-agent failure sometimes corrupts state too
            if agent=="SICK" and rng.random()<0.3 and not blastradius:
                poison+=1
            if deadletter: queue.append(tid)
            else: lost+=1
        else:
            streak[agent]=0; completed+=1
            if poison>0 and blastradius: poison=max(0,poison-1)

        if breaker and streak[agent]>=breaker_threshold and agent not in disabled:
            disabled.add(agent); streak[agent]=0
        # healthy agents recover; sick agent should STAY disabled (still sick)
        if breaker and disabled:
            for a in list(disabled):
                if a!="SICK" and rng.random()<0.1: disabled.discard(a)

        if attempts[tid]>=8 and tid in queue:
            queue.remove(tid); lost+=1

    return dict(completed=completed, lost=lost, cascaded=cascaded, work=work,
                success_rate=completed/n_tasks, routed_to_sick=routed_to_sick)

def avg(seeds=8, **kw):
    rs=[run(seed=s,**kw) for s in range(seeds)]
    return {k:statistics.mean([r[k] for r in rs]) for k in rs[0]}

if __name__=="__main__":
    print("CIRCUIT BREAKER — tested under its ACTUAL purpose (one sick agent)\n")
    print(f"{'config':>16} {'success':>8} {'lost':>6} {'work':>7} {'routed_to_sick':>15}")
    with_b=avg(breaker=True)
    without_b=avg(breaker=False)
    print(f"{'WITH breaker':>16} {with_b['success_rate']*100:>7.1f}% {with_b['lost']:>6.0f} {with_b['work']:>7.0f} {with_b['routed_to_sick']:>15.0f}")
    print(f"{'WITHOUT breaker':>16} {without_b['success_rate']*100:>7.1f}% {without_b['lost']:>6.0f} {without_b['work']:>7.0f} {without_b['routed_to_sick']:>15.0f}")

    print("\nInterpretation:")
    dwork = without_b['work']-with_b['work']
    dsick = without_b['routed_to_sick']-with_b['routed_to_sick']
    print(f"  wasted work avoided by breaker : {dwork:.0f} attempts")
    print(f"  fewer tasks sent to sick agent : {dsick:.0f}")
    if dwork>30 or (without_b['success_rate']-with_b['success_rate'])< -0.02:
        print("  => breaker EARNS its place when an agent goes persistently bad.")
        print("     The earlier chaos test was unfair (uniform failure isn't its job).")
    else:
        print("  => breaker still does little even under its intended scenario. Cut it.")

    print("\nAlso: crank the sick agent's failure rate")
    print(f"{'sick_fail':>10} {'w/ breaker work':>16} {'w/o breaker work':>17}")
    for sf in (0.5,0.7,0.9,0.99):
        wb=avg(breaker=True,sick_agent_fail=sf)
        nb=avg(breaker=False,sick_agent_fail=sf)
        print(f"{sf:>10.2f} {wb['work']:>16.0f} {nb['work']:>17.0f}")
