"""
EMERGENCE LEARNING DYNAMICS v2 — fix the test so the risk actually exists.
v1 converged cleanly but produced ZERO spurious heuristics — because the model
only let emergence learn caps that were genuinely needed. That's not realistic:
real learning works from OBSERVED misses, which include NOISE and MISATTRIBUTION
(a defect blamed on the wrong cause). Without that, the over-learning failure mode
can't occur, so the test couldn't evaluate the guard.

Fix: inject misattribution. When a defect occurs, with some probability it gets
blamed on a RANDOM capability rather than the true cause. If that wrong cause
recurs (by chance), the loop learns a SPURIOUS heuristic that fires forever,
adding work with no benefit. NOW we can test whether pruning earns its place.
"""
import random, statistics, collections

TRUE_CAPS = {
    "text":  {"core","ui","tokenize"},
    "data":  {"core","ui","validate","persist"},
    "media": {"core","ui","encode"},
}
EXTRA_CAPS=["extra1","extra2","extra3","extra4"]   # never actually needed
WORK_PER_CAP=1.0; DEFECT_COST=6.0

def new_task(rng):
    t=rng.choice(list(TRUE_CAPS)); true=TRUE_CAPS[t]
    spec=set(rng.sample(list(true), rng.randint(1,len(true))))
    return t, spec

def run(days=40, tpd=25, seed=0, guarded=False,
        misattribution=0.25, learn_threshold=2, prune_after=6):
    rng=random.Random(seed)
    heuristics=collections.defaultdict(set)
    heur_fired=collections.Counter(); heur_prevented=collections.Counter()
    daily=[]
    for day in range(days):
        defects=0; work=0
        blame=collections.Counter()   # (ttype,cap) blamed for a defect this day
        for _ in range(tpd):
            ttype,spec=new_task(rng); true=TRUE_CAPS[ttype]
            forced=heuristics[ttype]
            effective=spec|forced
            work+=len(effective)*WORK_PER_CAP
            for cap in forced:
                heur_fired[(ttype,cap)]+=1
                if cap in true and cap not in spec: heur_prevented[(ttype,cap)]+=1
            missing=true-effective
            defects+=len(missing)
            # attribution: each real miss is usually blamed correctly, sometimes not
            for cap in missing:
                if rng.random()<misattribution:
                    # blame a WRONG cause (a random extra cap that isn't needed)
                    wrong=rng.choice(EXTRA_CAPS)
                    blame[(ttype,wrong)]+=1
                else:
                    blame[(ttype,cap)]+=1
        # learn from blamed causes crossing threshold
        for (ttype,cap),cnt in blame.items():
            if cnt>=learn_threshold:
                heuristics[ttype].add(cap)
        # guarded pruning: remove heuristics that fired a lot but never prevented a defect
        if guarded:
            for (ttype,cap),fired in list(heur_fired.items()):
                if fired>=prune_after and heur_prevented[(ttype,cap)]==0:
                    heuristics[ttype].discard(cap)
        n_heur=sum(len(v) for v in heuristics.values())
        n_spur=sum(1 for tt in heuristics for c in heuristics[tt] if c not in TRUE_CAPS[tt])
        total_cost=work+defects*DEFECT_COST
        daily.append(dict(defects=defects,cost=total_cost,heuristics=n_heur,spurious=n_spur))
    return daily

def avg_daily(days=40,seeds=8,**kw):
    runs=[run(days=days,seed=s,**kw) for s in range(seeds)]
    return [{k:statistics.mean([r[d][k] for r in runs])
             for k in ("defects","cost","heuristics","spurious")} for d in range(days)]

def show(label,daily,sample):
    print(f"\n{label}")
    print(f"{'day':>4} {'defects':>8} {'cost':>8} {'heuristics':>11} {'spurious':>9}")
    for d in sample:
        r=daily[d]
        print(f"{d:>4} {r['defects']:>8.1f} {r['cost']:>8.1f} {r['heuristics']:>11.1f} {r['spurious']:>9.1f}")

if __name__=="__main__":
    days=40; sample=[0,2,5,10,20,30,39]
    print("EMERGENCE DYNAMICS v2 — WITH misattribution (25%), so spurious heuristics can form")

    ung=avg_daily(days=days,guarded=False)
    show("UNGUARDED (learn on any recurring blamed cause, never prune)", ung, sample)

    g=avg_daily(days=days,guarded=True)
    show("GUARDED (+ prune heuristics that fire but never prevent a defect)", g, sample)

    print("\n--- steady-state (last 5 days) ---")
    def ss(d,k): return statistics.mean([d[i][k] for i in range(days-5,days)])
    print(f"{'metric':>22} {'unguarded':>10} {'guarded':>10}")
    for k in ("cost","spurious","defects","heuristics"):
        print(f"{k:>22} {ss(ung,k):>10.1f} {ss(g,k):>10.1f}")

    ung_sp=ss(ung,'spurious'); g_sp=ss(g,'spurious')
    ung_c=ss(ung,'cost'); g_c=ss(g,'cost')
    print("\n--- verdict ---")
    if ung_sp>0.5:
        print(f"=> UNGUARDED over-learns: {ung_sp:.1f} permanent spurious heuristics,")
        print(f"   inflating steady-state cost to {ung_c:.1f}.")
    if g_sp < ung_sp-0.3 and g_c < ung_c:
        print(f"=> GUARDED pruning cuts spurious heuristics to {g_sp:.1f} and cost to {g_c:.1f}.")
        print(f"   The learning loop NEEDS a pruning guard — unbounded learning degrades.")
    elif ung_sp<=0.5:
        print("=> even unguarded stays clean; guard may be optional at this noise level.")
    # sensitivity: does higher noise make the guard more essential?
    print("\n--- does the guard matter more as misattribution rises? ---")
    print(f"{'misattr':>9} {'unguarded cost':>15} {'guarded cost':>14} {'unguarded spur':>16}")
    for ma in (0.1,0.25,0.4,0.6):
        u=avg_daily(days=days,guarded=False,misattribution=ma)
        gg=avg_daily(days=days,guarded=True,misattribution=ma)
        print(f"{ma:>9.2f} {ss(u,'cost'):>15.1f} {ss(gg,'cost'):>14.1f} {ss(u,'spurious'):>16.1f}")
