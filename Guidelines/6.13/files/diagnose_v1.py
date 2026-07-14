"""Diagnose v1: where do defects escape, and why so many operator interrupts?"""
import collections, statistics, random
import map_v1 as v1

def instrumented_run(days=5, tasks_per_day=20, seed=0, threshold=2):
    random.seed(seed)
    m=v1.Metrics(); state=v1.CanonicalState(m); em=v1.Emergence(m)
    val=v1.Validator(m,threshold=threshold)
    agents=[v1.Agent("Cloud-1","cloud",0.85,2.0),v1.Agent("Cloud-2","cloud",0.85,2.0),
            v1.Agent("Local-1","local",0.75,0.7),v1.Agent("Local-2","local",0.75,0.7)]
    hpom=v1.HPOM(state,em,val,agents,m)
    escaped_by_cap=collections.Counter()
    escaped_first_instance=0
    caught_after_repeat=0
    seen_sigs=collections.Counter()
    interrupt_causes=collections.Counter()

    # monkeypatch validator.check to record escape context
    orig_check=val.check
    def traced_check(sub,defect,clock):
        sig=sub["defect_sig"]
        halted,raised=orig_check(sub,defect,clock)
        nonlocal escaped_first_instance,caught_after_repeat
        if defect and not halted:
            escaped_by_cap[sub["cap"]]+=1
            if seen_sigs[sig]==0:
                escaped_first_instance+=1
        if defect:
            seen_sigs[sig]+=1
        if halted and defect and seen_sigs[sig]>0:
            caught_after_repeat+=1
        return halted,raised
    val.check=traced_check

    # trace emergence suggestions
    orig_gap=em.gap_score_and_fill
    def traced_gap(task):
        needed=set(v1.CAPABILITY_DB.get(task["type"],v1.CAPABILITY_DB["generic"]))|em.learned
        specified=set(task["specified"])
        gap=needed-specified
        for item in gap:
            conf=0.9 if item in ("core_logic","ui_placement","tokenization_rules") else 0.5
            if conf<0.7: interrupt_causes[item]+=1
        return orig_gap(task)
    em.gap_score_and_fill=traced_gap

    for day in range(days):
        dl=[]
        for _ in range(tasks_per_day):
            hpom.run_task(v1.random_task(),dl)
        em.end_of_day(dl)

    print(f"--- diagnosis (threshold={threshold}, seed={seed}) ---")
    print(f"defects that escaped on their FIRST occurrence: {escaped_first_instance}")
    print(f"escaped defects by capability: {dict(escaped_by_cap)}")
    print(f"operator-interrupt causes (low-conf items): {dict(interrupt_causes)}")
    print(f"total shipped: {m.missed_defects}, caught: {m.correct_halts}")
    return escaped_first_instance, m.missed_defects

if __name__=="__main__":
    tot_first=0; tot_ship=0
    for s in range(3):
        f,sh=instrumented_run(seed=s)
        tot_first+=f; tot_ship+=sh
    print(f"\nSUMMARY: {tot_first}/{tot_ship} shipped defects escaped on first occurrence "
          f"({100*tot_first/tot_ship:.0f}%)")
    print("=> If most escapes are 'first occurrence', threshold=2 is the culprit.")
