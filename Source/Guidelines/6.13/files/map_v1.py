"""
MAP Simulation Harness — v1 BASELINE
Implements MAP exactly as the design series specifies, instrumented so we can
measure whether each mechanism earns its place. Discrete-event style with a
simulated clock (no real threads — deterministic and fast to iterate).

Mechanisms in v1 (from the design docs):
- Single entry point (HPOM orchestrator)
- Canonical shared state with ATOMIC task-ID allocation (Phase 0)
- Git lock / mutual exclusion on writes (Phase 0)
- Coordination via shared state, not messages (Principle 1)
- Cognitive-load routing: local vs cloud (Phase 4)
- Emergence: gap scoring + inference (Phase 4)
- Validator with threshold-gated halt (Phase 3 / Principle 2)
- Structured event log (Phase 2)
"""
import random, statistics, collections, itertools

# ------------------------------------------------------------------ core state
class Metrics:
    def __init__(self):
        self.events = []
        self.counters = collections.Counter()
        self.timings = collections.defaultdict(list)
        self.id_collisions = 0
        self.lock_violations = 0
        self.halts = 0
        self.false_halts = 0          # halted on noise that wasn't a real defect
        self.missed_defects = 0       # real defect shipped without halt
        self.correct_halts = 0        # halted on a real defect
        self.tasks_completed = 0
        self.operator_interrupts = 0  # times operator had to intervene
        self.messages = 0             # point-to-point messages (want low)
        self.state_reads = 0          # shared-state reads (cheap, want as needed)
    def log(self, clock, kind, **kw):
        self.events.append((round(clock,2), kind, kw))
        self.counters[kind]+=1

class CanonicalState:
    """One authoritative store. Atomic allocation + write lock."""
    def __init__(self, metrics):
        self.m = metrics
        self._next_id = itertools.count(1)
        self._allocated = set()
        self._lock_holder = None
        self.board = {}          # shared-state 'countdown board': task_id -> status
        self.results = {}        # task_id -> result payload
    def allocate_id(self):
        # Atomic: single source hands out IDs; no interleave possible in sim,
        # but we assert uniqueness to catch any accidental double-alloc.
        tid = next(self._next_id)
        if tid in self._allocated:
            self.m.id_collisions += 1
        self._allocated.add(tid)
        return tid
    def acquire_lock(self, who):
        if self._lock_holder is not None and self._lock_holder != who:
            self.m.lock_violations += 1
            return False
        self._lock_holder = who
        return True
    def release_lock(self, who):
        if self._lock_holder == who:
            self._lock_holder = None
    def write_board(self, tid, status):
        self.board[tid] = status
    def read_board(self, tid=None):
        self.m.state_reads += 1
        return self.board if tid is None else self.board.get(tid)

# ------------------------------------------------------------------ emergence
CAPABILITY_DB = {
    "text_feature": ["core_logic","ui_placement","edge_cases","tokenization_rules","update_timing"],
    "data_feature": ["core_logic","ui_placement","edge_cases","validation","persistence"],
    "generic":      ["core_logic","ui_placement","edge_cases"],
}
class Emergence:
    """Infers unstated requirements. Gap score gates downstream effort.
    Has a learned-heuristics memory that grows end-of-day."""
    def __init__(self, metrics):
        self.m = metrics
        self.learned = set()   # heuristics distilled from past failures
    def gap_score_and_fill(self, task):
        needed = set(CAPABILITY_DB.get(task["type"], CAPABILITY_DB["generic"]))
        # apply learned heuristics (they force-include certain capabilities)
        needed |= self.learned
        specified = set(task["specified"])
        gap = needed - specified
        score = len(gap) / max(1,len(needed))
        # confidence per inferred item (stub: high for core things, low for extras)
        auto, suggest = [], []
        for item in gap:
            conf = 0.9 if item in ("core_logic","ui_placement","tokenization_rules") else 0.5
            (auto if conf>=0.7 else suggest).append(item)
        task["specified"] = list(specified | set(auto))
        self.m.log(task["clock"], "emergence_gap", task=task["id"], score=round(score,2),
                   auto=auto, suggest=suggest)
        if suggest:
            self.m.operator_interrupts += 1  # operator asked about suggestions
        return score
    def end_of_day(self, defect_log):
        # If a defect type recurs, learn to force-include the missing capability
        by_cap = collections.Counter(d["missing_cap"] for d in defect_log if d.get("missing_cap"))
        for cap,cnt in by_cap.items():
            if cnt>=2 and cap not in self.learned:
                self.learned.add(cap)
                return cap
        return None

# ------------------------------------------------------------------ agents
class Agent:
    def __init__(self, name, kind, skill, speed):
        self.name=name; self.kind=kind      # 'cloud' or 'local'
        self.skill=skill                     # 0..1 prob of clean output
        self.speed=speed                     # time units per subtask
    def do(self, subtask, state, metrics, clock):
        # Agents coordinate by READING shared state, not messaging.
        state.read_board()                   # e.g. check what peers did
        dur = self.speed * random.uniform(0.8,1.2)
        # defect probability depends on skill and whether the needed capability
        # was specified (missing tokenization_rules -> higher defect chance)
        base_defect = 1.0 - self.skill
        if subtask["cap"]=="core_logic" and "tokenization_rules" not in subtask["ctx_specified"] \
           and subtask["task_type"]=="text_feature":
            base_defect += 0.5   # the classic under-spec defect
        defect = random.random() < min(0.95, base_defect)
        return dur, defect

# ------------------------------------------------------------------ validator
class Validator:
    """Threshold-gated halt. Needs >= THRESHOLD correlated defect signals
    before halting (Principle 2 / coagulation). Tunable."""
    def __init__(self, metrics, threshold=2, sensitivity=1.0):
        self.m=metrics; self.threshold=threshold; self.sensitivity=sensitivity
        self.signals=collections.Counter()   # defect_signature -> count
    def check(self, subtask, defect, clock):
        # schema check always runs (cheap). content check may raise a signal.
        sig = subtask["defect_sig"]
        raised = False
        if defect:
            raised = True
        else:
            # false-positive: sometimes flags clean output as suspicious
            if random.random() < 0.05*self.sensitivity:
                raised = True
        if raised:
            self.signals[sig]+=1
        halted = self.signals[sig] >= self.threshold
        if halted:
            self.m.halts+=1
            if defect:
                self.m.correct_halts+=1
            else:
                self.m.false_halts+=1
            self.signals[sig]=0  # reset after halt
            self.m.log(clock,"validator_halt",sig=sig,defect=defect)
        return halted, raised

# ------------------------------------------------------------------ orchestrator
class HPOM:
    def __init__(self, state, emergence, validator, agents, metrics):
        self.state=state; self.em=emergence; self.val=validator
        self.agents=agents; self.m=metrics; self.clock=0.0
    def route(self, cap, task_type):
        # cognitive-load routing: mechanical caps -> local, reasoning -> cloud
        mechanical = {"ui_placement","edge_cases","update_timing"}
        want = "local" if cap in mechanical else "cloud"
        cands=[a for a in self.agents if a.kind==want] or self.agents
        return random.choice(cands)
    def run_task(self, task, defect_log):
        task["clock"]=self.clock
        tid=self.state.allocate_id(); task["id"]=tid
        self.state.write_board(tid,"intake")
        self.m.log(self.clock,"intake",task=tid,type=task["type"])
        # Emergence
        self.em.gap_score_and_fill(task)
        # Decompose into subtasks (one per specified capability)
        caps=task["specified"]
        for cap in caps:
            agent=self.route(cap,task["type"])
            sub={"cap":cap,"task_type":task["type"],
                 "ctx_specified":task["specified"],
                 "defect_sig":f'{task["type"]}:{cap}'}
            # acquire lock only for writes to shared editor files
            needs_lock = cap in ("core_logic","ui_placement")
            if needs_lock and not self.state.acquire_lock(agent.name):
                # lock contention: wait (advance clock), then retry once
                self.clock+=0.5
                self.state.acquire_lock(agent.name)
            dur,defect=agent.do(sub,self.state,self.m,self.clock)
            self.clock+=dur
            halted,raised=self.val.check(sub,defect,self.clock)
            if needs_lock: self.state.release_lock(agent.name)
            if halted:
                # Jidoka: stop -> fix -> rootcause. Re-run once, cleanly.
                self.clock+=agent.speed*0.5   # fix cost
                if defect:
                    defect_log.append({"task":tid,"cap":cap,
                        "missing_cap":"tokenization_rules" if task["type"]=="text_feature"
                        and cap=="core_logic" else None})
            elif defect:
                # defect shipped un-halted
                self.m.missed_defects+=1
                defect_log.append({"task":tid,"cap":cap,"shipped":True,
                    "missing_cap":"tokenization_rules" if task["type"]=="text_feature"
                    and cap=="core_logic" else None})
            self.state.write_board(tid,f"done:{cap}")
        self.m.tasks_completed+=1
        self.m.timings["task_time"].append(self.clock-task["clock"])

# ------------------------------------------------------------------ sim driver
def make_world(seed, validator_threshold=2, validator_sensitivity=1.0):
    random.seed(seed)
    m=Metrics()
    state=CanonicalState(m)
    em=Emergence(m)
    val=Validator(m,threshold=validator_threshold,sensitivity=validator_sensitivity)
    agents=[Agent("Cloud-1","cloud",skill=0.85,speed=2.0),
            Agent("Cloud-2","cloud",skill=0.85,speed=2.0),
            Agent("Local-1","local",skill=0.75,speed=0.7),
            Agent("Local-2","local",skill=0.75,speed=0.7)]
    return HPOM(state,em,val,agents,m), m, em

TASK_TYPES=["text_feature","data_feature","generic"]
def random_task():
    t=random.choice(TASK_TYPES)
    # operator specifies a random subset (under-specification is the norm)
    full=CAPABILITY_DB[t]
    k=random.randint(1,max(1,len(full)-2))
    return {"type":t,"specified":random.sample(full,k)}

def run_sim(days=5, tasks_per_day=20, seed=0, **valkw):
    hpom,m,em=make_world(seed,**valkw)
    for day in range(days):
        defect_log=[]
        for _ in range(tasks_per_day):
            hpom.run_task(random_task(),defect_log)
        learned=em.end_of_day(defect_log)
        if learned:
            m.log(hpom.clock,"learned_heuristic",cap=learned,day=day)
    return m

def summarize(m,label):
    tt=m.timings["task_time"]
    total_defects=m.correct_halts+m.missed_defects
    catch_rate = m.correct_halts/total_defects if total_defects else 1.0
    halt_precision = m.correct_halts/(m.correct_halts+m.false_halts) if (m.correct_halts+m.false_halts) else 1.0
    print(f"\n=== {label} ===")
    print(f"tasks completed      : {m.tasks_completed}")
    print(f"mean task time       : {statistics.mean(tt):.2f}  (median {statistics.median(tt):.2f})")
    print(f"ID collisions        : {m.id_collisions}")
    print(f"lock violations      : {m.lock_violations}")
    print(f"defects shipped       : {m.missed_defects}")
    print(f"defects caught (halt) : {m.correct_halts}")
    print(f"false halts          : {m.false_halts}")
    print(f"defect catch rate    : {catch_rate*100:.1f}%")
    print(f"halt precision       : {halt_precision*100:.1f}%")
    print(f"operator interrupts  : {m.operator_interrupts}")
    print(f"point-to-point msgs  : {m.messages}")
    print(f"shared-state reads   : {m.state_reads}")
    print(f"learned heuristics   : {m.counters['learned_heuristic']}")
    return {"label":label,"mean_time":statistics.mean(tt),"catch":catch_rate,
            "precision":halt_precision,"shipped":m.missed_defects,
            "false_halts":m.false_halts,"interrupts":m.operator_interrupts,
            "collisions":m.id_collisions,"lock_viol":m.lock_violations}

if __name__=="__main__":
    # run across several seeds for stability
    results=[]
    for seed in range(5):
        m=run_sim(days=5,tasks_per_day=20,seed=seed)
        results.append(summarize(m,f"v1 baseline seed={seed}"))
    print("\n\n########## v1 AGGREGATE (mean over seeds) ##########")
    for k in ["mean_time","catch","precision","shipped","false_halts","interrupts","collisions","lock_viol"]:
        vals=[r[k] for r in results]
        print(f"{k:16s}: {statistics.mean(vals):.3f}")
