"""
GLOBAL SENSITIVITY ANALYSIS — grade the reliability of every prior conclusion.
The meta-critique: the sims keep confirming the design because one mental model
built both. The antidote isn't MORE data of the same kind — it's stress-testing
whether each CONCLUSION survives when its underlying assumptions are pushed to the
edges of plausibility. Robust conclusions (never flip) can be trusted. Fragile
ones (flip within plausible ranges) were artifacts of a guess and must be flagged.

We re-test the four biggest conclusions across WIDE parameter ranges:
  C1: eager halt (threshold=1) beats threshold gating
  C2: the knowledge layer's full design beats no-library
  C3: idempotency prevents silent corruption (resilience earns place)
  C4: emergence learning needs a pruning guard

For each, we sweep the parameters that could plausibly overturn it and report the
fraction of the plausible space where the conclusion HOLDS. High % = robust.
"""
import random, statistics, itertools

# ---------- C1: eager halt vs threshold gating, across cost & defect regimes ----------
def c1_holds(cost_ratio, defect_rate, false_pos, seeds=4):
    """Returns True if threshold=1 total cost < threshold=2 across seeds.
    cost_ratio = shipped_defect_cost / false_halt_cost."""
    def sim(thr, seed):
        rng=random.Random(seed); shipped=0; false_halts=0; caught=0
        signals={}
        for _ in range(600):
            defect = rng.random()<defect_rate
            sig = rng.randrange(20)   # defect signature
            raised = defect or (rng.random()<false_pos)
            if raised: signals[sig]=signals.get(sig,0)+1
            halted = signals.get(sig,0)>=thr
            if halted:
                if defect: caught+=1
                else: false_halts+=1
                signals[sig]=0
            elif defect:
                shipped+=1
        false_cost=1.0; shipped_cost=cost_ratio*false_cost
        return shipped*shipped_cost + false_halts*false_cost
    wins=0
    for s in range(seeds):
        if sim(1,s) < sim(2,s): wins+=1
    return wins/seeds >= 0.75

def c1_robustness():
    ratios=[0.25,0.5,1,2,4,8,16]        # shipped:false cost ratio (wide)
    defects=[0.1,0.2,0.3,0.5]           # defect rate
    fps=[0.02,0.05,0.1]                 # false-positive rate
    total=0; held=0
    for r,d,f in itertools.product(ratios,defects,fps):
        total+=1
        if c1_holds(r,d,f): held+=1
    return held/total, total

# ---------- C2: knowledge layer full design vs no-library, across churn/detail/compression ----------
def c2_holds(churn, detail, compression, defect_tok=6000, seeds=4):
    FULL=2000; SUMM=FULL/compression; REGEN=FULL*0.2
    def sim(mode, seed):
        rng=random.Random(seed); docs={i:{"stale":False} for i in range(50)}; total=0
        for _ in range(1500):
            d=docs[rng.randrange(50)]
            if rng.random()<churn: d["stale"]=True
            needs=rng.random()<detail
            if mode=="NONE": total+=FULL
            else:
                if d["stale"]: total+=REGEN; d["stale"]=False
                total+=SUMM
                if needs: total+=FULL; d["stale"]=False
        return total
    wins=0
    for s in range(seeds):
        if sim("TRACK",s) < sim("NONE",s): wins+=1
    return wins/seeds>=0.75

def c2_robustness():
    churns=[0.02,0.1,0.3,0.5]
    details=[0.05,0.2,0.5,0.8]
    comps=[1.2,2,5,10,20]               # compression ratio (wide, incl. weak)
    total=0; held=0
    for c,d,k in itertools.product(churns,details,comps):
        total+=1
        if c2_holds(c,d,k): held+=1
    return held/total, total

# ---------- C3: idempotency prevents corruption, across crash/retry regimes ----------
def c3_holds(p_crash, retry_prob, seeds=4):
    """Without idempotency, crashes cause double-applies. Conclusion holds if
    removing idempotency produces meaningfully more corruption."""
    def sim(idem, seed):
        rng=random.Random(seed); double=0
        for _ in range(1000):
            if rng.random()<p_crash:      # crash mid-write
                if not idem and rng.random()<retry_prob:
                    double+=1
        return double
    # conclusion: idempotency matters if no-idem corruption > 0 across seeds
    no_idem=statistics.mean([sim(False,s) for s in range(seeds)])
    with_idem=statistics.mean([sim(True,s) for s in range(seeds)])
    return no_idem > with_idem + 2   # meaningfully more corruption without it

def c3_robustness():
    crashes=[0.02,0.05,0.1,0.2]
    retries=[0.1,0.3,0.5,0.8]
    total=0; held=0
    for c,r in itertools.product(crashes,retries):
        total+=1
        if c3_holds(c,r): held+=1
    return held/total, total

# ---------- C4: emergence needs pruning guard, across noise/horizon ----------
def c4_holds(misattr, days, seeds=4):
    TRUE={"t":{"a","b","c"}}; EXTRA=["x1","x2","x3","x4"]
    def sim(guarded, seed):
        rng=random.Random(seed); heur=set(); fired={}; prevented={}; cost=0
        for _ in range(days):
            blame={}
            for _ in range(25):
                spec=set(rng.sample(list(TRUE["t"]),rng.randint(1,3)))
                eff=spec|heur
                cost+=len(eff)
                for c in heur:
                    fired[c]=fired.get(c,0)+1
                    if c in TRUE["t"] and c not in spec: prevented[c]=prevented.get(c,0)+1
                missing=TRUE["t"]-eff
                cost+=len(missing)*6
                for c in missing:
                    tgt = rng.choice(EXTRA) if rng.random()<misattr else c
                    blame[tgt]=blame.get(tgt,0)+1
            for c,n in blame.items():
                if n>=2: heur.add(c)
            if guarded:
                for c in list(heur):
                    if fired.get(c,0)>=6 and prevented.get(c,0)==0: heur.discard(c)
        return cost
    # conclusion holds if guarded cost < unguarded cost (guard helps)
    ung=statistics.mean([sim(False,s) for s in range(seeds)])
    g=statistics.mean([sim(True,s) for s in range(seeds)])
    return g < ung

def c4_robustness():
    noises=[0.1,0.25,0.4,0.6]
    horizons=[15,30,50]
    total=0; held=0
    for n,h in itertools.product(noises,horizons):
        total+=1
        if c4_holds(n,h): held+=1
    return held/total, total

if __name__=="__main__":
    print("GLOBAL SENSITIVITY — % of plausible parameter space where each conclusion HOLDS")
    print("(high % = robust, trust it; low % = fragile, it was an artifact of assumptions)\n")

    c1,c1n = c1_robustness()
    c2,c2n = c2_robustness()
    c3,c3n = c3_robustness()
    c4,c4n = c4_robustness()

    def verdict(p):
        if p>=0.95: return "ROBUST — trust it"
        if p>=0.80: return "MOSTLY ROBUST — minor caveats"
        if p>=0.60: return "CONDITIONAL — depends on regime"
        return "FRAGILE — artifact of assumptions"

    print(f"{'conclusion':<52} {'holds%':>7} {'cells':>6}  verdict")
    print(f"{'C1 eager-halt beats threshold gating':<52} {c1*100:>6.0f}% {c1n:>6}  {verdict(c1)}")
    print(f"{'C2 knowledge layer (full) beats no-library':<52} {c2*100:>6.0f}% {c2n:>6}  {verdict(c2)}")
    print(f"{'C3 idempotency prevents silent corruption':<52} {c3*100:>6.0f}% {c3n:>6}  {verdict(c3)}")
    print(f"{'C4 emergence needs a pruning guard':<52} {c4*100:>6.0f}% {c4n:>6}  {verdict(c4)}")

    print("\nReading it: conclusions at ~100% held across even extreme parameters are")
    print("safe to build on. Anything CONDITIONAL flips within plausible ranges — those")
    print("are the ones whose real-repo parameters actually need measuring before trusting.")
