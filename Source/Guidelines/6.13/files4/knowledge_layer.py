"""
MAP KNOWLEDGE-LAYER SIMULATION
Test the newest, least-proven component: the Library agent (summaries + wikilinks
+ staleness tracking). It was added on reasoning alone. Prove it pays off or cut it.

The question is NOT "are summaries nice" — it's "does the Library layer reduce
TOTAL cost once you count its two failure modes and its maintenance overhead?"

Four modes:
  NO_LIBRARY        : agents always read full docs. Expensive but always current
                      and complete (no staleness, no lossiness).
  SUMMARY_ONLY      : agents read summaries. Cheap reads, but risk (a) acting on a
                      STALE summary after the doc changed, and (b) missing detail a
                      task needed (LOSSY).
  SUMMARY_LINKS     : summaries + wikilinks. When a task needs detail, agent
                      traverses to full (pays full cost). Kills lossiness; staleness
                      remains.
  SUMMARY_LINKS_TRACK: adds event-driven staleness tracking — a changed doc's summary
                      is regenerated (maintenance cost) before it's read again. Kills
                      staleness too. This is the full synthesized-doc design.

Two parameters decide everything, so we SWEEP them:
  churn_rate       : how often a doc changes between accesses (staleness pressure)
  detail_need_rate : how often a task actually needs full detail (summary futility)

Cost model (tokens as the currency; defects converted to token-equivalent):
  read full     = FULL_TOK
  read summary  = SUMM_TOK
  stale defect  = DEFECT_TOK   (acted on outdated info)
  lossy defect  = DEFECT_TOK   (needed detail, had only summary, didn't traverse)
  summary regen = REGEN_TOK    (maintenance when a changed doc is re-summarized)
"""
import random, statistics, itertools

FULL_TOK   = 2000    # tokens to read a full doc
SUMM_TOK   = 200     # tokens to read a summary (10x compression)
DEFECT_TOK = 6000    # cost of a defect caused by stale/lossy context (found later)
REGEN_TOK  = 400     # cost to regenerate one summary

def run(mode, churn_rate, detail_need_rate, n_accesses=2000, seed=0):
    rng = random.Random(seed)
    # each doc tracks whether its summary is currently stale
    docs = {i: {"stale": False} for i in range(50)}
    total = 0
    stale_defects = 0
    lossy_defects = 0
    regens = 0
    for _ in range(n_accesses):
        d = docs[rng.randrange(len(docs))]
        # between accesses, the doc may have changed
        if rng.random() < churn_rate:
            d["stale"] = True   # summary no longer matches the doc
        needs_detail = rng.random() < detail_need_rate

        if mode == "NO_LIBRARY":
            total += FULL_TOK          # always full, always current+complete
            # reading full re-syncs understanding; no defects possible from context
        elif mode == "SUMMARY_ONLY":
            total += SUMM_TOK
            if d["stale"]:
                total += DEFECT_TOK; stale_defects += 1
            if needs_detail:
                total += DEFECT_TOK; lossy_defects += 1   # couldn't get detail
        elif mode == "SUMMARY_LINKS":
            total += SUMM_TOK
            if d["stale"]:
                total += DEFECT_TOK; stale_defects += 1
            if needs_detail:
                total += FULL_TOK      # traverse to full detail (no lossy defect)
        elif mode == "SUMMARY_LINKS_TRACK":
            # staleness tracking: if changed, regenerate summary before read
            if d["stale"]:
                total += REGEN_TOK; regens += 1; d["stale"] = False
            total += SUMM_TOK
            if needs_detail:
                total += FULL_TOK
        # reading current full detail (in link modes) also clears staleness
        if mode in ("SUMMARY_LINKS","SUMMARY_LINKS_TRACK") and needs_detail:
            d["stale"] = False
    return dict(total=total, stale=stale_defects, lossy=lossy_defects, regens=regens)

def avg(mode, churn, detail, seeds=6):
    rs=[run(mode,churn,detail,seed=s) for s in range(seeds)]
    return {k:statistics.mean([r[k] for r in rs]) for k in rs[0]}

MODES=["NO_LIBRARY","SUMMARY_ONLY","SUMMARY_LINKS","SUMMARY_LINKS_TRACK"]

def sweep():
    print("KNOWLEDGE-LAYER COST (lower = better). Currency = tokens.\n")
    churns  = [0.02, 0.1, 0.3]
    details = [0.05, 0.2, 0.5]
    for churn in churns:
        for detail in details:
            print(f"--- churn={churn:.0%}  detail_need={detail:.0%} ---")
            costs={}
            for m in MODES:
                a=avg(m,churn,detail)
                costs[m]=a['total']
                extra=f"stale={a['stale']:.0f} lossy={a['lossy']:.0f} regens={a['regens']:.0f}"
                print(f"  {m:22s} cost={a['total']:>10.0f}   {extra}")
            best=min(costs,key=costs.get)
            nolib=costs['NO_LIBRARY']
            savings=100*(nolib-costs[best])/nolib
            print(f"  >> WINNER: {best}  ({savings:+.0f}% vs NO_LIBRARY)\n")

if __name__=="__main__":
    sweep()
    print("="*60)
    print("Reading the result: if SUMMARY_LINKS_TRACK wins broadly, the Library")
    print("layer earns its place. If NO_LIBRARY wins in realistic regimes, or if")
    print("the full design only wins in a narrow band, that's a reason to cut or")
    print("scope it down. We follow the data.")
