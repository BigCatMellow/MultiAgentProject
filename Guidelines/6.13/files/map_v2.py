"""
MAP v2 — TUNING EXPERIMENTS
Don't assume; measure. Two things to settle with data:

EXPERIMENT A: validator threshold sweep (1..3) — what does the catch/precision
              tradeoff actually look like?

EXPERIMENT B: validator ARCHITECTURE bake-off:
   - 'threshold'  : v1 design — N correlated signals before halt (Principle 2 literal)
   - 'severity'   : halt immediately on high-severity caps, threshold on low-severity
   - 'confidence' : halt based on a per-output confidence score, not signal count
   The design docs assume 'threshold' is right. Test that belief.

Also fixes the emergence interrupt problem: recalibrate 'edge_cases' confidence.
"""
import random, statistics, collections, itertools
import map_v1 as v1

# ---- fix 1: recalibrate confidence so we stop pestering on edge_cases ----
# edge_cases is routine for most features; treat as high-confidence auto-add.
HIGH_CONF_CAPS = {"core_logic","ui_placement","tokenization_rules","edge_cases","update_timing"}

class EmergenceV2(v1.Emergence):
    def gap_score_and_fill(self, task):
        needed=set(v1.CAPABILITY_DB.get(task["type"],v1.CAPABILITY_DB["generic"]))|self.learned
        specified=set(task["specified"])
        gap=needed-specified
        score=len(gap)/max(1,len(needed))
        auto,suggest=[],[]
        for item in gap:
            conf=0.9 if item in HIGH_CONF_CAPS else 0.5
            (auto if conf>=0.7 else suggest).append(item)
        task["specified"]=list(specified|set(auto))
        self.m.log(task["clock"],"emergence_gap",task=task["id"],score=round(score,2))
        if suggest:
            self.m.operator_interrupts+=1
        return score

# ---- experiment B: three validator architectures ----
SEVERITY = {  # how bad is a defect in this capability if it ships?
    "core_logic":1.0,"tokenization_rules":0.9,"validation":0.9,"persistence":0.8,
    "ui_placement":0.4,"edge_cases":0.5,"update_timing":0.3,
}
class ValidatorV2:
    def __init__(self, metrics, mode="threshold", threshold=2, sensitivity=1.0):
        self.m=metrics; self.mode=mode; self.threshold=threshold
        self.sensitivity=sensitivity; self.signals=collections.Counter()
    def check(self, sub, defect, clock):
        sig=sub["defect_sig"]; cap=sub["cap"]
        raised = defect or (random.random()<0.05*self.sensitivity)
        if raised: self.signals[sig]+=1
        halted=False
        if self.mode=="threshold":
            halted = self.signals[sig]>=self.threshold
        elif self.mode=="severity":
            sev=SEVERITY.get(cap,0.5)
            # high-severity: halt on first raise; low-severity: need threshold
            need = 1 if sev>=0.8 else self.threshold
            halted = self.signals[sig]>=need
        elif self.mode=="confidence":
            # probabilistic: chance of halt scales with severity when raised
            if raised:
                sev=SEVERITY.get(cap,0.5)
                halted = random.random() < (0.4+0.6*sev)
        if halted:
            self.m.halts+=1
            if defect: self.m.correct_halts+=1
            else: self.m.false_halts+=1
            self.signals[sig]=0
        return halted, raised

def make_world_v2(seed, mode="threshold", threshold=2, sensitivity=1.0):
    random.seed(seed)
    m=v1.Metrics(); state=v1.CanonicalState(m); em=EmergenceV2(m)
    val=ValidatorV2(m,mode=mode,threshold=threshold,sensitivity=sensitivity)
    agents=[v1.Agent("Cloud-1","cloud",0.85,2.0),v1.Agent("Cloud-2","cloud",0.85,2.0),
            v1.Agent("Local-1","local",0.75,0.7),v1.Agent("Local-2","local",0.75,0.7)]
    return v1.HPOM(state,em,val,agents,m), m, em

def run_v2(days=5,tpd=20,seed=0,**kw):
    hpom,m,em=make_world_v2(seed,**kw)
    for day in range(days):
        dl=[]
        for _ in range(tpd): hpom.run_task(v1.random_task(),dl)
        em.end_of_day(dl)
    return m

def score(m):
    tt=m.timings["task_time"]
    tot=m.correct_halts+m.missed_defects
    catch=m.correct_halts/tot if tot else 1.0
    prec=m.correct_halts/(m.correct_halts+m.false_halts) if (m.correct_halts+m.false_halts) else 1.0
    return dict(mean_time=statistics.mean(tt),catch=catch,precision=prec,
                shipped=m.missed_defects,false_halts=m.false_halts,
                interrupts=m.operator_interrupts)

def avg(mode,threshold=2,seeds=6):
    rs=[score(run_v2(seed=s,mode=mode,threshold=threshold)) for s in range(seeds)]
    return {k:statistics.mean([r[k] for r in rs]) for k in rs[0]}

if __name__=="__main__":
    print("EXPERIMENT A — threshold sweep (mode=threshold)")
    print(f"{'thr':>4} {'catch':>7} {'prec':>7} {'shipped':>8} {'false':>7} {'interrupts':>10} {'time':>7}")
    for thr in (1,2,3):
        a=avg("threshold",threshold=thr)
        print(f"{thr:>4} {a['catch']*100:>6.1f}% {a['precision']*100:>6.1f}% "
              f"{a['shipped']:>8.1f} {a['false_halts']:>7.1f} {a['interrupts']:>10.1f} {a['mean_time']:>7.2f}")

    print("\nEXPERIMENT B — validator architecture bake-off (best threshold=1 for threshold-mode)")
    print(f"{'mode':>12} {'catch':>7} {'prec':>7} {'shipped':>8} {'false':>7} {'interrupts':>10}")
    for mode in ("threshold","severity","confidence"):
        thr = 1 if mode=="threshold" else 2
        a=avg(mode,threshold=thr)
        print(f"{mode:>12} {a['catch']*100:>6.1f}% {a['precision']*100:>6.1f}% "
              f"{a['shipped']:>8.1f} {a['false_halts']:>7.1f} {a['interrupts']:>10.1f}")

    print("\n(interrupts should drop sharply vs v1's ~83 after edge_cases recalibration)")
