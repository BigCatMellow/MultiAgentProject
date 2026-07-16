"""
MAP v3 — CHALLENGE THE RESULT, THEN CHALLENGE THE WHOLE APPROACH

Part 1: threshold=1 won, but has more false halts. Does that matter?
        Model a real COST for false halts (wasted rework) and see if threshold=1
        still wins on total cost, or if the tradeoff flips.

Part 2: A deeper question the design docs never ask. The validator is a
        DOWNSTREAM net. What if we reduce defects at the SOURCE instead?
        Test three source-side levers against the best validator:
          - route reasoning-heavy caps to cloud ALWAYS (no local on hard caps)
          - emergence pre-defines tokenization (removes the under-spec defect class)
          - a cheap 'peer review' pass (second agent reads output before validator)
        Goal: find the cheapest path to low shipped-defects + low total cost,
        not just the best validator.
"""
import random, statistics, collections
import map_v1 as v1
from map_v2 import EmergenceV2, ValidatorV2, HIGH_CONF_CAPS

# cost model (time units)
COST_SHIPPED_DEFECT = 8.0   # a shipped defect costs a lot (found later, expensive)
COST_FALSE_HALT     = 1.5   # a false halt costs some rework
COST_CORRECT_HALT   = 1.0   # catching early is cheap
COST_INTERRUPT      = 0.5   # operator attention has a price

class SourceAwareHPOM(v1.HPOM):
    """HPOM variant with tunable source-side defect reduction."""
    def __init__(self,*a,strict_routing=False,peer_review=False,**kw):
        super().__init__(*a,**kw)
        self.strict_routing=strict_routing
        self.peer_review=peer_review
    def route(self, cap, task_type):
        mechanical={"ui_placement","edge_cases","update_timing"}
        if self.strict_routing:
            # hard caps ALWAYS to cloud (higher skill), even if 'mechanical' overlap
            reasoning={"core_logic","validation","tokenization_rules","persistence"}
            want="cloud" if cap in reasoning else ("local" if cap in mechanical else "cloud")
        else:
            want="local" if cap in mechanical else "cloud"
        cands=[a for a in self.agents if a.kind==want] or self.agents
        return random.choice(cands)
    def run_task(self, task, defect_log):
        task["clock"]=self.clock
        tid=self.state.allocate_id(); task["id"]=tid
        self.state.write_board(tid,"intake")
        self.em.gap_score_and_fill(task)
        caps=task["specified"]
        for cap in caps:
            agent=self.route(cap,task["type"])
            sub={"cap":cap,"task_type":task["type"],
                 "ctx_specified":task["specified"],"defect_sig":f'{task["type"]}:{cap}'}
            needs_lock=cap in ("core_logic","ui_placement")
            if needs_lock and not self.state.acquire_lock(agent.name):
                self.clock+=0.5; self.state.acquire_lock(agent.name)
            dur,defect=agent.do(sub,self.state,self.m,self.clock)
            self.clock+=dur
            # peer review: a second agent catches some defects pre-validator (cheap)
            if self.peer_review and defect:
                reviewer=random.choice([a for a in self.agents if a is not agent] or [agent])
                self.clock+=reviewer.speed*0.3
                if random.random()<reviewer.skill:   # reviewer skill = catch prob
                    defect=False
                    self.m.counters["peer_caught"]+=1
            halted,raised=self.val.check(sub,defect,self.clock)
            if needs_lock: self.state.release_lock(agent.name)
            if halted:
                self.clock+=agent.speed*0.5
                if defect:
                    defect_log.append({"task":tid,"cap":cap,
                        "missing_cap":"tokenization_rules" if task["type"]=="text_feature"
                        and cap=="core_logic" else None})
            elif defect:
                self.m.missed_defects+=1
                defect_log.append({"task":tid,"cap":cap,"shipped":True,
                    "missing_cap":"tokenization_rules" if task["type"]=="text_feature"
                    and cap=="core_logic" else None})
            self.state.write_board(tid,f"done:{cap}")
        self.m.tasks_completed+=1
        self.m.timings["task_time"].append(self.clock-task["clock"])

# emergence that pre-defines tokenization from day 1 (kills the under-spec class)
class EmergencePreTok(EmergenceV2):
    def __init__(self,metrics,pretok=False):
        super().__init__(metrics); 
        if pretok: self.learned.add("tokenization_rules")

def build(seed, val_mode="threshold", val_thr=1, strict_routing=False,
          peer_review=False, pretok=False):
    random.seed(seed)
    m=v1.Metrics(); state=v1.CanonicalState(m); em=EmergencePreTok(m,pretok=pretok)
    val=ValidatorV2(m,mode=val_mode,threshold=val_thr)
    agents=[v1.Agent("Cloud-1","cloud",0.85,2.0),v1.Agent("Cloud-2","cloud",0.85,2.0),
            v1.Agent("Local-1","local",0.75,0.7),v1.Agent("Local-2","local",0.75,0.7)]
    hpom=SourceAwareHPOM(state,em,val,agents,m,
                         strict_routing=strict_routing,peer_review=peer_review)
    return hpom,m,em

def run(seed,days=5,tpd=20,**kw):
    hpom,m,em=build(seed,**kw)
    for _ in range(days):
        dl=[]
        for _ in range(tpd): hpom.run_task(v1.random_task(),dl)
        em.end_of_day(dl)
    return m

def total_cost(m):
    return (m.missed_defects*COST_SHIPPED_DEFECT
            + m.false_halts*COST_FALSE_HALT
            + m.correct_halts*COST_CORRECT_HALT
            + m.operator_interrupts*COST_INTERRUPT
            + sum(m.timings["task_time"]))   # base work time

def metrics(m):
    tot=m.correct_halts+m.missed_defects
    catch=m.correct_halts/tot if tot else 1.0
    return dict(cost=total_cost(m),shipped=m.missed_defects,
                false_halts=m.false_halts,catch=catch,
                interrupts=m.operator_interrupts,
                peer_caught=m.counters.get("peer_caught",0),
                worktime=sum(m.timings["task_time"]))

def avg(seeds=6,**kw):
    rs=[metrics(run(seed=s,**kw)) for s in range(seeds)]
    return {k:statistics.mean([r[k] for r in rs]) for k in rs[0]}

if __name__=="__main__":
    print("PART 1 — does threshold=1 survive a real false-halt cost?")
    print(f"{'config':>28} {'total_cost':>11} {'shipped':>8} {'false':>7} {'catch':>7}")
    for thr in (1,2):
        a=avg(val_thr=thr)
        print(f"{'threshold='+str(thr):>28} {a['cost']:>11.0f} {a['shipped']:>8.1f} "
              f"{a['false_halts']:>7.1f} {a['catch']*100:>6.1f}%")

    print("\nPART 2 — source-side levers (all with best validator threshold=1)")
    print(f"{'config':>28} {'total_cost':>11} {'shipped':>8} {'false':>7} {'worktime':>9} {'peer':>6}")
    configs = [
        ("baseline (v2 best)",      dict()),
        ("+ strict routing",        dict(strict_routing=True)),
        ("+ pre-define tokenizn",   dict(pretok=True)),
        ("+ peer review",           dict(peer_review=True)),
        ("+ strict + pretok",       dict(strict_routing=True,pretok=True)),
        ("ALL three",               dict(strict_routing=True,pretok=True,peer_review=True)),
    ]
    best=None
    for name,kw in configs:
        a=avg(val_thr=1,**kw)
        print(f"{name:>28} {a['cost']:>11.0f} {a['shipped']:>8.1f} {a['false_halts']:>7.1f} "
              f"{a['worktime']:>9.0f} {a['peer_caught']:>6.0f}")
        if best is None or a['cost']<best[1]: best=(name,a['cost'])
    print(f"\nLOWEST TOTAL COST: {best[0]} ({best[1]:.0f})")
