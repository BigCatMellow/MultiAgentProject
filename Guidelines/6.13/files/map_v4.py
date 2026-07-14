"""
MAP v4 — FINAL TUNING + ROBUSTNESS

Locked-in winners from v1-v3 (data-driven, not doctrine):
  * validator threshold = 1  (threshold gating was HARMFUL here — removed)
  * emergence edge_cases recalibrated to high-confidence (interrupts 83->28)
  * peer-review pass ON (best single lever, -18% cost)
  * strict routing OFF (no effect — removed)
  * pre-define tokenization OFF (net-negative — removed)

Remaining questions:
  Q1: how much peer review is optimal? (review-everything is expensive;
      review-nothing loses the benefit). Sweep the peer-review TRIGGER.
  Q2: is 'peer review only when defect exists' realistic? In reality you
      don't know a defect exists. Model REALISTIC peer review: review a
      FRACTION of all outputs (not just defective ones) and see real cost.
  Q3: robustness — does the tuned config hold under 2x load and worse agents?
"""
import random, statistics, collections
import map_v1 as v1
from map_v2 import EmergenceV2, ValidatorV2
from map_v3 import COST_SHIPPED_DEFECT, COST_FALSE_HALT, COST_CORRECT_HALT, COST_INTERRUPT

class RealisticHPOM(v1.HPOM):
    """Peer review applied to a FRACTION of all outputs (you don't know which
    are defective in advance). review_rate in [0,1]."""
    def __init__(self,*a,review_rate=0.0,**kw):
        super().__init__(*a,**kw); self.review_rate=review_rate
    def run_task(self, task, defect_log):
        task["clock"]=self.clock
        tid=self.state.allocate_id(); task["id"]=tid
        self.state.write_board(tid,"intake")
        self.em.gap_score_and_fill(task)
        for cap in task["specified"]:
            agent=self.route(cap,task["type"])
            sub={"cap":cap,"task_type":task["type"],
                 "ctx_specified":task["specified"],"defect_sig":f'{task["type"]}:{cap}'}
            needs_lock=cap in ("core_logic","ui_placement")
            if needs_lock and not self.state.acquire_lock(agent.name):
                self.clock+=0.5; self.state.acquire_lock(agent.name)
            dur,defect=agent.do(sub,self.state,self.m,self.clock)
            self.clock+=dur
            # realistic peer review: review a fraction of ALL outputs
            if random.random()<self.review_rate:
                reviewer=random.choice([a for a in self.agents if a is not agent] or [agent])
                self.clock+=reviewer.speed*0.3          # review cost paid on reviewed items
                self.m.counters["reviewed"]+=1
                if defect and random.random()<reviewer.skill:
                    defect=False; self.m.counters["peer_caught"]+=1
            halted,raised=self.val.check(sub,defect,self.clock)
            if needs_lock: self.state.release_lock(agent.name)
            if halted:
                self.clock+=agent.speed*0.5
            elif defect:
                self.m.missed_defects+=1
            self.state.write_board(tid,f"done:{cap}")
        self.m.tasks_completed+=1
        self.m.timings["task_time"].append(self.clock-task["clock"])

def build(seed,review_rate=0.0,agent_skill=(0.85,0.75),tpd_note=None):
    random.seed(seed)
    m=v1.Metrics(); state=v1.CanonicalState(m); em=EmergenceV2(m)
    val=ValidatorV2(m,mode="threshold",threshold=1)
    cs,ls=agent_skill
    agents=[v1.Agent("Cloud-1","cloud",cs,2.0),v1.Agent("Cloud-2","cloud",cs,2.0),
            v1.Agent("Local-1","local",ls,0.7),v1.Agent("Local-2","local",ls,0.7)]
    return RealisticHPOM(state,em,val,agents,m,review_rate=review_rate),m,em

def run(seed,days=5,tpd=20,**kw):
    hpom,m,em=build(seed,**kw)
    for _ in range(days):
        dl=[]
        for _ in range(tpd): hpom.run_task(v1.random_task(),dl)
        em.end_of_day(dl)
    return m

REVIEW_COST_PER = COST_CORRECT_HALT*0.3  # cheap
def total_cost(m):
    reviewed=m.counters.get("reviewed",0)
    return (m.missed_defects*COST_SHIPPED_DEFECT + m.false_halts*COST_FALSE_HALT
            + m.correct_halts*COST_CORRECT_HALT + m.operator_interrupts*COST_INTERRUPT
            + sum(m.timings["task_time"]))
def metrics(m):
    tot=m.correct_halts+m.missed_defects
    return dict(cost=total_cost(m),shipped=m.missed_defects,
                catch=(m.correct_halts/tot if tot else 1.0),
                reviewed=m.counters.get("reviewed",0),
                peer_caught=m.counters.get("peer_caught",0),
                worktime=sum(m.timings["task_time"]))
def avg(seeds=8,**kw):
    rs=[metrics(run(seed=s,**kw)) for s in range(seeds)]
    return {k:statistics.mean([r[k] for r in rs]) for k in rs[0]}

if __name__=="__main__":
    print("Q1/Q2 — realistic peer-review rate sweep (review fraction of ALL outputs)")
    print(f"{'review_rate':>12} {'total_cost':>11} {'shipped':>8} {'reviewed':>9} {'peer_caught':>12}")
    best=None
    for rr in (0.0,0.1,0.25,0.5,0.75,1.0):
        a=avg(review_rate=rr)
        print(f"{rr:>12.2f} {a['cost']:>11.0f} {a['shipped']:>8.1f} {a['reviewed']:>9.0f} {a['peer_caught']:>12.0f}")
        if best is None or a['cost']<best[1]: best=(rr,a['cost'])
    print(f"OPTIMAL review_rate = {best[0]} (cost {best[1]:.0f})")

    opt_rr=best[0]
    print(f"\nQ3 — ROBUSTNESS of tuned config (review_rate={opt_rr}) under stress")
    print(f"{'scenario':>26} {'total_cost':>11} {'shipped':>8} {'catch':>7}")
    scenarios=[
        ("normal (5d x20)",       dict(days=5,tpd=20,agent_skill=(0.85,0.75))),
        ("2x load (5d x40)",      dict(days=5,tpd=40,agent_skill=(0.85,0.75))),
        ("degraded agents",       dict(days=5,tpd=20,agent_skill=(0.70,0.55))),
        ("2x load + degraded",    dict(days=5,tpd=40,agent_skill=(0.70,0.55))),
    ]
    for name,kw in scenarios:
        rs=[metrics(run(seed=s,review_rate=opt_rr,**kw)) for s in range(8)]
        c=statistics.mean([r['cost'] for r in rs])
        sh=statistics.mean([r['shipped'] for r in rs])
        ca=statistics.mean([r['catch'] for r in rs])
        # normalize cost per task for fair load comparison
        ntasks=kw['days']*kw['tpd']
        print(f"{name:>26} {c/ntasks:>10.2f}/t {sh:>8.1f} {ca*100:>6.1f}%")
    print("\n(cost shown PER TASK so load scenarios compare fairly)")
