"""
MAP v6 — FIX THE BROKEN TEST, THEN RESOLVE THE TRUST TENSION

EXP 2 (REDO): the v5 concurrency test produced no data — a broken test.
   Rebuild it to ACTUALLY race: use a shared counter with a genuine
   read-modify-write and enough work in the window that the GIL releases.
   Use a thread barrier so all threads hit the critical section together.
   Compare a truly-unsafe counter vs a locked one and vs threading primitives.

EXP 3 (RESOLVE): v5 found threshold=1's false halts erode operator trust
   (100% -> 82% real catch over 10 days). But the fix might not be a higher
   threshold — it might be a LOWER FALSE-POSITIVE RATE. Test the real lever:
   hold threshold=1, sweep validator false-positive rate DOWN, and see if
   trust survives while catch stays high. Find the FP rate where threshold=1
   beats threshold=2 on real (trust-adjusted) catch.
"""
import random, statistics, threading, collections
import map_v1 as v1
from map_v2 import EmergenceV2, ValidatorV2

# ============================================================ EXP 2 REDO
def race_test(n_threads=8, per_thread=5000, use_lock=False):
    """Genuine shared-counter race. Each thread does read, tiny compute, write."""
    counter={"v":0}
    lock=threading.Lock()
    barrier=threading.Barrier(n_threads)
    issued=[]
    issued_lock=threading.Lock()
    def worker():
        barrier.wait()  # ensure all threads contend simultaneously
        local=[]
        for _ in range(per_thread):
            if use_lock:
                with lock:
                    v=counter["v"]; v+=1; counter["v"]=v
                    local.append(v)
            else:
                v=counter["v"]          # READ
                v=v+1                   # MODIFY (separate bytecode ops)
                counter["v"]=v          # WRITE  -- race window between read and write
                local.append(v)
        with issued_lock:
            issued.extend(local)
    threads=[threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads: t.start()
    for t in threads: t.join()
    final=counter["v"]
    expected=n_threads*per_thread
    unique=len(set(issued))
    # 'lost updates': counter should equal expected if no races
    lost=expected-final
    dup=len(issued)-unique
    return expected, final, lost, dup

def exp2_redo():
    print("EXP 2 (REDO) — REAL RACE on a shared counter")
    print(f"{'variant':>16} {'expected':>9} {'final_val':>10} {'lost_updates':>13} {'dup_ids':>8} {'verdict':>8}")
    for name,use_lock in (("UNSAFE (no lock)",False),("ATOMIC (locked)",True)):
        # worst case over several runs (races are nondeterministic)
        worst=None
        for _ in range(8):
            e,f,lost,dup=race_test(use_lock=use_lock)
            score=lost+dup
            if worst is None or score>worst[4]: worst=(e,f,lost,dup,score)
        verdict="FAILS" if worst[4]>0 else "SAFE"
        print(f"{name:>16} {worst[0]:>9} {worst[1]:>10} {worst[2]:>13} {worst[3]:>8} {verdict:>8}")
    print("=> UNSAFE should now show lost updates (the real bug); ATOMIC should be clean.")
    print("   This is the genuine near-deletion root-cause reproduction.")

# ============================================================ EXP 3 RESOLVE
class TrustValidator2(ValidatorV2):
    def __init__(self,metrics,threshold=1,sensitivity=1.0,trust_decay=0.03,override_below=0.5):
        super().__init__(metrics,mode="threshold",threshold=threshold,sensitivity=sensitivity)
        self.trust=1.0; self.trust_decay=trust_decay; self.override_below=override_below
        self.overrides=0
    def check(self, sub, defect, clock):
        halted,raised=super().check(sub,defect,clock)
        if halted and not defect:
            self.trust=max(0.0,self.trust-self.trust_decay)
        if halted and self.trust<self.override_below:
            if random.random() < (self.override_below-self.trust):
                self.overrides+=1
                if defect:
                    self.m.missed_defects+=1; self.m.correct_halts-=1
                halted=False
        return halted,raised

def run_fp(seed, threshold, sensitivity):
    """sensitivity scales the false-positive rate (0.05*sensitivity in validator)."""
    random.seed(seed)
    m=v1.Metrics(); state=v1.CanonicalState(m); em=EmergenceV2(m)
    val=TrustValidator2(m,threshold=threshold,sensitivity=sensitivity)
    agents=[v1.Agent("Cloud-1","cloud",0.85,2.0),v1.Agent("Cloud-2","cloud",0.85,2.0),
            v1.Agent("Local-1","local",0.75,0.7),v1.Agent("Local-2","local",0.75,0.7)]
    hpom=v1.HPOM(state,em,val,agents,m)
    for _ in range(10):
        dl=[]
        for _ in range(20): hpom.run_task(v1.random_task(),dl)
        em.end_of_day(dl)
    tot=m.correct_halts+m.missed_defects
    catch=m.correct_halts/tot if tot else 1.0
    return catch, m.missed_defects, val.trust, val.false_halts, val.overrides

def exp3_resolve():
    print("\n\nEXP 3 (RESOLVE) — hold threshold=1, drive false-positive rate DOWN")
    print("Baseline FP sensitivity = 1.0 (~5% FP). Lower sensitivity = fewer false halts.")
    print(f"{'sensitivity':>12} {'~FP_rate':>9} {'final_trust':>12} {'shipped':>8} {'real_catch':>11}")
    for sens in (1.0, 0.5, 0.25, 0.1, 0.0):
        rs=[run_fp(s,1,sens) for s in range(8)]
        catch=statistics.mean([r[0] for r in rs])
        shipped=statistics.mean([r[1] for r in rs])
        trust=statistics.mean([r[2] for r in rs])
        fp=0.05*sens
        print(f"{sens:>12.2f} {fp*100:>8.1f}% {trust:>12.2f} {shipped:>8.1f} {catch*100:>10.1f}%")
    print("\ncompare vs threshold=2 (from v5): trust 0.46, shipped 96.5, catch 46.9%")
    # threshold=2 at low FP for fairness
    rs2=[run_fp(s,2,0.1) for s in range(8)]
    c2=statistics.mean([r[0] for r in rs2]); s2=statistics.mean([r[1] for r in rs2]); t2=statistics.mean([r[2] for r in rs2])
    print(f"threshold=2 @ low FP (0.5%): trust {t2:.2f}, shipped {s2:.1f}, catch {c2*100:.1f}%")
    print("\n=> If threshold=1 + low FP keeps BOTH high trust AND high catch, the answer")
    print("   isn't 'raise the threshold' — it's 'halt eagerly but be accurate'.")

if __name__=="__main__":
    exp2_redo()
    exp3_resolve()
