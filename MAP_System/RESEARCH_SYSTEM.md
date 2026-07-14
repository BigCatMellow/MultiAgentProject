<!-- hpom: file: RESEARCH_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-103 build, Guidelines/MAP_repo_systems_gap_review.md -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Research System

Status: active
Decision: DEC-015
Owner: command-center
Built by: TASK-103

## What this is

The Research System is the knowledge-acquisition layer of MAP.

HPOM governs safe execution:
```
How does work move safely from task to review to release?
```

The Emergence System governs creative discovery:
```
What new thing is becoming possible because of the work?
```

The Research System governs truth:
```
What do we need to know before we act, and how do we know it is true?
```

## Core principle

```
Do not let assumptions become architecture.
Do not let unsourced claims become project truth.
Do not let outdated knowledge guide current decisions.
```

## Why this exists

Gap identified in `Guidelines/MAP_repo_systems_gap_review.md`: MAP already
moves work safely (HPOM), captures ideas safely (Emergence), and records
decisions (`shared/decisions.md`), but had no formal process for how an
agent establishes that a claim is true, current, and sourced before it
becomes the basis for a task or a decision. Research existed only as an
artifact category (`artifacts/research/`), not a process.

## The three layers, extended

| Layer | Question | System |
|---|---|---|
| Truth | What do we know, and how well do we know it? | Research System |
| Execution | How do we move work safely? | HPOM |
| Discovery | What is becoming possible? | Emergence System |
| Governance | What becomes real? | Human Owner + Decision process |

## The research flow

```
Research Question
  → Research Brief
  → Source Map
  → Source Evaluation
  → Claim Evidence Matrix
  → Assumption Register
  → Research Summary
  → Decision or HPOM Task
```

1. **Research Question** — a specific, answerable question blocking a task or decision. Not "learn about X"; must be falsifiable or resolvable.
2. **Research Brief** — states the question, why it matters, what would count as an answer, and the deadline sensitivity.
3. **Source Map** — lists candidate sources before reading them deeply, so coverage is visible before depth.
4. **Source Evaluation** — rates each source's authority, recency, and bias before its claims are trusted.
5. **Claim Evidence Matrix** — every claim used downstream is tied to at least one evaluated source, or flagged as unsourced.
6. **Assumption Register** — anything treated as true without a source is logged as an assumption, not silently absorbed into architecture.
7. **Research Summary** — the operator- and agent-facing answer: what we now believe, confidence level, and what remains open.
8. **Decision or HPOM Task** — the summary feeds `shared/decisions.md` (DEC-NNN) or becomes task input; research itself does not directly change code or config.

## Relationship to other systems

```
Research verifies facts.
Emergence creates new possibilities from those facts.
HPOM executes approved work based on those facts.
Self-Repair (`SELF_REPAIR_SYSTEM.md`, DEC-016) detects when facts become stale or contradictory, and files a Repair Record.
Memory stores the verified result.
Context (`CONTEXT_SYSTEM.md`, DEC-017) loads the right verified result for the next task.
```

- A research question may originate from an Emergence insight ("we don't
  actually know if X is true") — capture that as an `INS-NNNN` first if it
  is a passing observation, and only open a Research Brief once the
  question is specific enough to answer.
- A completed Research Summary that changes project truth gets recorded as
  a decision in `shared/decisions.md`, same as any other decision — the
  Research System does not bypass the decision log.
- A completed Research Summary that unblocks implementation work becomes
  input to a new or existing task (`input_paths` should name the summary).

## Source quality ratings

Rate every source in the Source Map / Source Evaluation as one of:

| Rating | Meaning | Example |
|---|---|---|
| `PRIMARY` | Authoritative, first-party, or canonical for the claim | official docs, source code, spec, direct measurement |
| `SECONDARY` | Reputable but interpreted or aggregated | changelog summaries, reputable technical writeups |
| `COMMUNITY` | Unverified but plausible | forum posts, issue threads, blog posts without citations |
| `UNVERIFIED` | Unknown provenance or could not be checked | AI-generated summary with no link back to source, memory/recall with no citation |
| `STALE` | Was authoritative but is date-sensitive and may be outdated | old version docs, deprecated API reference |

Claims sourced only from `COMMUNITY` or `UNVERIFIED` sources must be flagged
in the Claim Evidence Matrix as low-confidence, not stated as fact.

## Claim extraction rules

- Extract one claim per row in the Claim Evidence Matrix. Do not bundle
  multiple assertions into one claim — each must be independently checkable.
- A claim is only "supported" if a specific source (with a locator: file
  path, URL, section, or line) backs it, not "the docs" in general.
- If two sources disagree, do not average or silently pick one — log it
  under Contradiction Handling below.
- Claims derived from a model's own training/memory without a live source
  check must be rated `UNVERIFIED` and re-checked before being load-bearing
  for architecture, security, or external-facing behavior.

## Contradiction handling

When sources disagree on a claim:

1. Log both sources and both claims in the Claim Evidence Matrix; do not
   delete the losing claim.
2. Prefer the source with the higher quality rating (PRIMARY over
   SECONDARY over COMMUNITY).
3. If ratings tie, prefer the more recent source unless the older source is
   normative (e.g., a spec) and the newer one is a paraphrase.
4. If the contradiction cannot be resolved with available sources, record
   it as an open question in the Assumption Register and in
   `shared/unresolved-questions.md`, and say so explicitly in the Research
   Summary. Do not resolve by guessing.

## Date-sensitivity rules

- Every source in the Source Map records a retrieval or publish date.
- A Research Brief states whether the question is time-sensitive (pricing,
  API versions, library behavior, security advisories) or stable (math,
  established protocols, historical fact).
- Time-sensitive claims older than one active project cycle should be
  re-verified before being reused in a new task; do not assume a prior
  Research Summary is still current without checking its date against the
  question's sensitivity.
- The Research Summary must state its own "confidence decays after" note
  when the topic is time-sensitive, so future readers know when to
  re-verify rather than reuse blindly.

## Assumption register rules

- Anything treated as true in a task, decision, or design without a source
  belongs in the Assumption Register, not silently in code comments or
  task descriptions.
- Each assumption states: what is assumed, why it was assumed instead of
  verified, the blast radius if wrong, and who can resolve it.
- Assumptions that gate `BLOCKER`/`REQUIRED` review findings or
  security/network-facing work must be resolved (verified or explicitly
  accepted by command-center) before release, not carried indefinitely.

## Folder structure

```
MAP_System/
  RESEARCH_SYSTEM.md        ← this file
  research/
    README.md                ← process + CLI-equivalent usage
  templates/research/
    RESEARCH_BRIEF_TEMPLATE.md
    SOURCE_MAP_TEMPLATE.md
    SOURCE_EVALUATION_TEMPLATE.md
    CLAIM_EVIDENCE_MATRIX_TEMPLATE.md
    ASSUMPTION_REGISTER_TEMPLATE.md
    RESEARCH_SUMMARY_TEMPLATE.md
  artifacts/research/        ← completed research records live here (existing folder)
```

Project-level research folders follow the same shape under
`Projects/<PROJECT_NAME>/research/{briefs,sources,evidence,assumptions,summaries}/`
when a project needs isolated research state; MAP-system-level research
(questions about MAP itself) stays under `MAP_System/artifacts/research/`.

## How to run a research task

1. Open (or receive) a Research Question. If it is not specific enough to
   answer, shape it first — do not start sourcing against a vague question.
2. Copy `templates/research/RESEARCH_BRIEF_TEMPLATE.md` into
   `artifacts/research/` (or the project's `research/briefs/`), fill it in.
3. Copy the Source Map template, list candidate sources before deep-reading
   any of them.
4. Copy the Source Evaluation template, rate each source used.
5. Copy the Claim Evidence Matrix template, extract claims tied to sources.
6. Copy the Assumption Register template for anything unsourced.
7. Copy the Research Summary template, write the operator-facing answer,
   confidence level, and open questions.
8. If the summary changes project truth, add a `DEC-NNN` entry to
   `shared/decisions.md` referencing the summary path. If it unblocks
   implementation, create or update a task with the summary in
   `input_paths`.
9. Log `PROGRESS`/`SUBMISSION` events in `events/events.jsonl` as with any
   other task.

## Who does research (HPOM routing)

Applying `shared/hpom.md` authority tiers to research work:

- **Tier 1 (core agents)** own Research Briefs, Claim Evidence Matrices,
  Assumption Registers, and Research Summaries — synthesis and judgment
  calls about source quality and contradiction resolution require core
  agent judgment.
- **Tier 3 (local assistants)** may draft a Source Map (listing candidate
  sources) or produce a first-pass summary of a single already-fetched
  source, subject to core-agent review before it is trusted.
- **Tier 0 (command-center/human)** must resolve assumptions that gate
  BLOCKER/REQUIRED findings, security-relevant claims, or contradictions
  the core agents could not settle from available sources. See
  `DECISION_AUTHORITY_SYSTEM.md` for how such a resolution is routed to
  approval as a decision.
- No tier may state an `UNVERIFIED` claim as project truth in a decision or
  task description without labeling it as unverified.

## Agent rule

```
Ask before assuming.
Cite before claiming.
Flag before building on uncertainty.
```

## Related files

- `research/README.md` [[research/README]] — folder layout and quick-start
- `templates/research/` — the six research templates
- `HUMAN_INTERFACE_SYSTEM.md` [[HUMAN_INTERFACE_SYSTEM]] — where open research questions and
  unresolved assumptions are surfaced to the operator
- `PROJECT_BOOTSTRAPPING_SYSTEM.md` [[PROJECT_BOOTSTRAPPING_SYSTEM]] — where a new project's day-one
  research needs draw from this system
- `SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]] — where stale/contradictory facts this system
  surfaces become repair targets
- `RISK_SYSTEM.md` [[RISK_SYSTEM]] — where an unresolved contradiction this system could
  not settle becomes a KNOWLEDGE-class risk
- `CONTEXT_SYSTEM.md` [[CONTEXT_SYSTEM]] — where a context packet carries a Research
  Summary's conclusion instead of raw sourcing
- `DECISION_AUTHORITY_SYSTEM.md` [[DECISION_AUTHORITY_SYSTEM]] — where a research conclusion that
  requires command-center approval is routed for a binding decision
- `emergence/README.md` [[emergence/README]] — where questions worth investigating may originate
- `shared/hpom.md` [[hpom]] — the execution/authority system this feeds into
- `shared/decisions.md` [[decisions]] — where research conclusions that change project
  truth land as decisions
- `shared/unresolved-questions.md` [[unresolved-questions]] — where unresolved contradictions land
  if research cannot settle them
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as the highest-priority build
