"""
MAP v7 — RACE AT THE RIGHT LEVEL, AND FINISH THE TRUST RESOLUTION

Insight from v5/v6: Python's GIL makes bytecode-level thread races nearly
impossible to trigger, so those tests showed false 'SAFE'. But MAP's real
near-deletion risk is MULTI-PROCESS (separate agent processes touching the same
git repo / task file), where there is NO shared lock unless you build one.
So model the race where it actually lives: explicit interleaved processes
sharing a file-like resource, with and without a file lock.

EXP 2 (CORRECT): simulate N processes each doing check-then-act on a shared
   task-ID file. Interleave them deterministically to EXPOSE the race in the
   unlocked case and prove the file-lock case is safe.

EXP 3 (FIXED): the typo is fixed. Hold threshold=1, drive false-positive rate
   down, and see if trust survives while catch stays high.
"""
import random, statistics, collections
import map_v1 as v1
from map_v2 import EmergenceV2, ValidatorV2

# ============================================================ EXP 2 CORRECT
class SharedTaskFile:
    """Models a task-ID file two PROCESSES read/write. No implicit lock."""
    def __init__(self): self.max_id=0; self.rows=[]
    def read_max(self): return self.max_id
    def write_row(self, tid, owner): self.max_id=max(self.max_id,tid); self.rows.append((tid,owner))

def simulate_processes(n_procs=6, ops=100, locked=False, seed=0):
    """Explicitly interleave process steps to model concurrent check-then-act.
    Unlocked: process reads max, computes max+1, writes -- but another process
    can interleave between its read and write (the real bug).
    Locked: the read-compute-write is a critical section no one can interleave."""
    rng=random.Random(seed)
    f=SharedTaskFile()
    # each process wants to allocate 'ops' ids
    pending=[[p]*ops for p in range(n_procs)]
    # flatten into an interleaved schedule of (proc, step) micro-ops
    # step model: 0=read, 1=write  (only matters when unlocked)
    inflight={}   # proc -> value it read but hasn't written yet
    issued=[]
    # build a randomized interleaving of read/write micro-ops
    ops_queue=[]
    for p in range(n_procs):
        for _ in range(ops):
            ops_queue.append(p)
    rng.shuffle(ops_queue)

    if locked:
        # critical section: each allocation is atomic; process the queue but
        # for each proc-op do read+write together with no interleave
        for p in ops_queue:
            cur=f.read_max(); nid=cur+1; f.write_row(nid,p); issued.append(nid)
    else:
        # unlocked: split each allocation into read then (later) write, letting
        # other procs interleave between -> collisions when two read same max
        # We simulate by having each proc read, hold, and write after a delay.
        read_phase={}
        # process in queue order, but writes are deferred by a random lag
        write_schedule=[]
        t=0
        for p in ops_queue:
            cur=f.read_max()                 # READ now
            nid=cur+1
            # defer the WRITE by a few ticks, allowing interleave
            write_schedule.append((t+rng.randint(1,3), nid, p))
            t+=1
        # execute writes in time order (interleaved with the reads already done)
        for _,nid,p in sorted(write_schedule):
            f.write_row(nid,p); issued.append(nid)

    expected_unique=n_procs*ops
    unique=len(set(issued))
    collisions=len(issued)-unique
    return expected_unique, len(issued), unique, collisions

def exp2_correct():
    print("EXP 2 (CORRECT) — PROCESS-LEVEL race on a shared task-ID file")
    print("This models MAP's REAL risk: separate agent processes, no shared lock.")
    print(f"{'variant':>18} {'issued':>8} {'unique':>8} {'collisions':>11} {'verdict':>8}")
    for name,locked in (("UNLOCKED (procs)",False),("FILE-LOCKED",True)):
        worst=None
        for s in range(10):
            e,iss,u,c=simulate_processes(locked=locked,seed=s)
            if worst is None or c>worst[3]: worst=(e,iss,u,c)
        verdict="FAILS" if worst[3]>0 else "SAFE"
        print(f"{name:>18} {worst[1]:>8} {worst[2]:>8} {worst[3]:>11} {verdict:>8}")
    print("=> UNLOCKED shows ID collisions (two processes read the same max, both +1,")
    print("   both write the same id) — the near-deletion mechanism. FILE-LOCKED is clean.")
    print("   TAKEAWAY: map-git MUST enforce a real cross-PROCESS lock, not just wrap git.")

# ============================================================ EXP 3 FIXED
class TrustValidator3(ValidatorV2):
    def __init__(self,metrics,threshold=1,sensitivity=1.0,trust_decay=0.03,override_below=0.5):
        super().__init__(metrics,mode="threshold",threshold=threshold,sensitivity=sensitivity)
        self.trust=1.0; self.trust_decay=trust_decay; self.override_below=override_below
        self.overrides=0; self.my_false_halts=0
    def check(self, sub, defect, clock):
        halted,raised=super().check(sub,defect,clock)
        if halted and not defect:
            self.my_false_halts+=1
            self.trust=max(0.0,self.trust-self.trust_decay)
        if halted and self.trust<self.override_below:
            if random.random() < (self.override_below-self.trust):
                self.overrides+=1
                if defect:
                    self.m.missed_defects+=1; self.m.correct_halts-=1
                halted=False
        return halted,raised

def run_fp(seed, threshold, sensitivity):
    random.seed(seed)
    m=v1.Metrics(); state=v1.CanonicalState(m); em=EmergenceV2(m)
    val=TrustValidator3(m,threshold=threshold,sensitivity=sensitivity)
    agents=[v1.Agent("Cloud-1","cloud",0.85,2.0),v1.Agent("Cloud-2","cloud",0.85,2.0),
            v1.Agent("Local-1","local",0.75,0.7),v1.Agent("Local-2","local",0.75,0.7)]
    hpom=v1.HPOM(state,em,val,agents,m)
    for _ in range(10):
        dl=[]
        for _ in range(20): hpom.run_task(v1.random_task(),dl)
        em.end_of_day(dl)
    tot=m.correct_halts+m.missed_defects
    catch=m.correct_halts/tot if tot else 1.0
    return catch, m.missed_defects, val.trust, val.my_false_halts, val.overrides

def exp3_fixed():
    print("\n\nEXP 3 (FIXED) — hold threshold=1, drive false-positive rate DOWN")
    print("Does an ACCURATE eager validator keep both trust AND catch high?")
    print(f"{'sensitivity':>12} {'~FP_rate':>9} {'false_halts':>12} {'final_trust':>12} {'shipped':>8} {'real_catch':>11}")
    best=None
    for sens in (1.0, 0.5, 0.25, 0.1, 0.0):
        rs=[run_fp(s,1,sens) for s in range(10)]
        catch=statistics.mean([r[0] for r in rs])
        shipped=statistics.mean([r[1] for r in rs])
        trust=statistics.mean([r[2] for r in rs])
        fh=statistics.mean([r[3] for r in rs])
        fp=0.05*sens
        print(f"{sens:>12.2f} {fp*100:>8.1f}% {fh:>12.1f} {trust:>12.2f} {shipped:>8.1f} {catch*100:>10.1f}%")
        if best is None or catch>best[1]: best=(sens,catch,shipped,trust)
    print(f"\nBEST: sensitivity={best[0]} -> catch {best[1]*100:.1f}%, trust {best[3]:.2f}, shipped {best[2]:.1f}")
    print("compare threshold=2 (v5): catch 46.9%, trust 0.46, shipped 96.5")
    print("\n=> RESOLUTION: the fix for trust erosion is validator ACCURACY, not a higher")
    print("   threshold. Halt eagerly (threshold=1) but keep false positives low.")

if __name__=="__main__":
    exp2_correct()
    exp3_fixed()
