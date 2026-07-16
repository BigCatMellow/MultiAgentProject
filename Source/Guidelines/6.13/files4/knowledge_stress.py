"""
KNOWLEDGE-LAYER STRESS TEST — find where it STOPS being worth it.
The full-design win looked almost too clean. Two assumptions drove it:
  - 10x compression (summary=200 vs full=2000)
  - regen cost = 400 (cheap re-summarization)
  - defect cost = 6000
Push each until the recommendation flips, so the advice is conditional and honest.

EXP A: sweep REGEN cost. Re-summarizing on every change is the maintenance tax.
       If regen is expensive (a big doc, an expensive model), does tracking still win?
EXP B: sweep COMPRESSION ratio. If summaries aren't that much smaller than full docs
       (weak compression), the whole scheme loses its point. Where's the break-even?
EXP C: the practical lever — does it matter WHICH model regenerates summaries?
       cheap-tier regen vs reasoning-tier regen (10x cost difference).
"""
import statistics, random

FULL_TOK=2000; SUMM_TOK=200; DEFECT_TOK=6000; REGEN_TOK=400

def run(mode, churn, detail, n=2000, seed=0, full_tok=FULL_TOK, summ_tok=SUMM_TOK,
        regen_tok=REGEN_TOK, defect_tok=DEFECT_TOK):
    rng=random.Random(seed); docs={i:{"stale":False} for i in range(50)}
    total=0
    for _ in range(n):
        d=docs[rng.randrange(len(docs))]
        if rng.random()<churn: d["stale"]=True
        needs=rng.random()<detail
        if mode=="NO_LIBRARY":
            total+=full_tok
        elif mode=="TRACK":
            if d["stale"]: total+=regen_tok; d["stale"]=False
            total+=summ_tok
            if needs: total+=full_tok; d["stale"]=False
    return total

def avg(mode,churn,detail,seeds=6,**kw):
    return statistics.mean([run(mode,churn,detail,seed=s,**kw) for s in range(seeds)])

# Use a realistic-ish middle regime for the stress tests
CHURN, DETAIL = 0.1, 0.2

def expA():
    print(f"EXP A — REGEN COST sweep (churn={CHURN:.0%}, detail={DETAIL:.0%})")
    print("How expensive can re-summarization get before tracking loses to no-library?")
    print(f"{'regen_tok':>10} {'TRACK cost':>12} {'NO_LIB cost':>12} {'winner':>10}")
    nolib=avg("NO_LIBRARY",CHURN,DETAIL)
    flip=None
    for regen in (100,400,1000,2000,4000,8000,16000):
        t=avg("TRACK",CHURN,DETAIL,regen_tok=regen)
        w="TRACK" if t<nolib else "NO_LIBRARY"
        if w=="NO_LIBRARY" and flip is None: flip=regen
        print(f"{regen:>10} {t:>12.0f} {nolib:>12.0f} {w:>10}")
    if flip:
        print(f"=> Tracking loses once regen costs ~{flip}+ tokens per summary")
        print(f"   (i.e. re-summarizing costs ~{flip/FULL_TOK:.0f}x reading the full doc — implausible)")
    else:
        print("=> Tracking wins even at absurd regen costs. Robust.")

def expB():
    print(f"\nEXP B — COMPRESSION RATIO sweep (churn={CHURN:.0%}, detail={DETAIL:.0%})")
    print("Weaker compression = summaries closer to full size. Where's break-even?")
    print(f"{'summ_tok':>9} {'ratio':>7} {'TRACK cost':>12} {'NO_LIB cost':>12} {'winner':>10}")
    nolib=avg("NO_LIBRARY",CHURN,DETAIL)
    flip=None
    for summ in (100,200,400,800,1200,1600,1900):
        t=avg("TRACK",CHURN,DETAIL,summ_tok=summ)
        ratio=FULL_TOK/summ
        w="TRACK" if t<nolib else "NO_LIBRARY"
        if w=="NO_LIBRARY" and flip is None: flip=ratio
        print(f"{summ:>9} {ratio:>6.1f}x {t:>12.0f} {nolib:>12.0f} {w:>10}")
    if flip:
        print(f"=> Tracking loses once compression drops below ~{flip:.1f}x")
    else:
        print("=> Tracking wins even at weak compression. Robust.")

def expC():
    print(f"\nEXP C — WHICH MODEL regenerates summaries? (churn={CHURN:.0%}, detail={DETAIL:.0%})")
    print("Summary regen is 'mechanical but needs a model' — should be cheap tier.")
    print(f"{'regen tier':>18} {'regen_tok':>10} {'TRACK cost':>12}")
    for name,regen in (("cheap-language tier",400),("reasoning tier (10x)",4000)):
        t=avg("TRACK",CHURN,DETAIL,regen_tok=regen)
        print(f"{name:>18} {regen:>10} {t:>12.0f}")
    print("=> Confirms the roster placement: regenerating summaries on the cheap tier")
    print("   keeps the maintenance tax low. Putting it on the reasoning tier wastes money.")

if __name__=="__main__":
    expA(); expB(); expC()
    print("\n"+"="*60)
    print("VERDICT LOGIC: the Library layer (full design) is robust across")
    print("plausible regen costs and compression ratios. It only fails under")
    print("implausible conditions (re-summarizing costs more than reading full,")
    print("or compression under ~1.2x). Keep it — but keep staleness tracking as")
    print("the non-negotiable core, and run regen on the cheap tier.")
