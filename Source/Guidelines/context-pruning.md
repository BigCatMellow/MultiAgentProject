# Context Pruning — Window Hygiene

A context window that only grows is the same problem as a response that never stops. Stale context costs tokens on every subsequent call and adds noise the model has to route around. Prune actively.

---

## Core Rule

**If a piece of context won't affect the next decision, it shouldn't be in the window.**

The test is forward-looking: not "was this useful?" but "will this change anything from here?"

---

## Drop Rules

These get deleted from context entirely:

**Resolved tasks.** A task is resolved when its output has been accepted and no follow-up is pending. The task description, the back-and-forth, and the intermediate attempts are all droppable. Keep only the final output if it's referenced downstream.

**Superseded instructions.** If a later message changes or overrides an earlier instruction, the earlier one is gone. Two conflicting instructions in context costs the model work to reconcile; the loser should simply not be there.

**Corrected examples.** If an example was given, found wrong, and corrected, drop both the original example and the correction exchange. Keep only the correct version, stated cleanly.

**Raw tool output that was summarized.** If a tool returned 400 lines and the agent summarized it to 5 relevant fields, drop the raw output. The summary is the canonical version.

**Meta-conversation.** Clarifying questions and their answers, once resolved, collapse into a single resolved-spec line. The Q&A exchange itself is droppable.

**Pleasantries and acknowledgments.** Any turn that contains only acknowledgment (`"Got it"`, `"Sure"`, `"Understood"`) with no new information is pure noise after the fact.

---

## Collapse Rules

These get compressed rather than deleted:

**Deliberation → decision.** A reasoning chain that led to a decision collapses to the decision plus a one-line rationale if the rationale is non-obvious. The full chain of thought is not forward-relevant.

> `Decided: write-through cache. Reason: write volume low, consistency required.`

**Failed attempts → working solution.** Multiple attempts at a problem collapse to the working solution only. The failure modes may be worth a single note if they represent real constraints (`"Regex approach hit backtracking — using parser instead"`), but the failed code itself goes.

**Long spec → accepted spec.** A negotiated specification collapses to its final accepted form. The negotiation is not forward-relevant.

**Verbose error → error summary.** A full stack trace collapses to the error type, location, and cause once diagnosed. The raw trace is available if needed; it doesn't need to ride in context forever.

---

## Checkpoint: When to Prune

Prune at **natural task boundaries** — points where one coherent unit of work is complete and the next begins. Signals:

- A `!LGTM` or `!EOF` was emitted
- A deliverable was accepted
- The task type is changing (e.g., switching from planning to implementation)
- Context is approaching 50% of the window limit

At a checkpoint:

1. Emit a `STATE_SNAPSHOT` (MATOCP §2) containing only forward-relevant state
2. Drop everything before the checkpoint from the active window
3. The snapshot is the new context floor

```yaml
# Checkpoint snapshot — task 89a2 complete
task_id: 89a2
status: complete
output: src/auth.py patched, tests passing
forward_constraints:
  - no direct SQL concat anywhere in src/billing/
  - api_version: "2.1"
next_task: billing module audit
lexicon:
  btx: "billing transaction object, src/billing/models.py"
```

Everything prior to this snapshot is gone. Everything after it has this as ground truth.

---

## What Never Gets Pruned

**Active constraints.** Any rule or requirement that's still in force must stay in context until it's no longer in force. "No PII in logs" doesn't expire when the task that introduced it finishes.

**Unresolved errors.** An error that hasn't been diagnosed and fixed stays in context. Pruning it means losing the problem statement.

**Security and auth context.** Permissions, roles, access levels, and trust boundaries stay. These are load-bearing; losing them silently is a correctness risk.

**The current task spec.** Whatever the model is actively working on is never pruned mid-task, only after it's complete and accepted.

**The lexicon.** Session-local token definitions (MATOCP §4.2) travel in STATE_SNAPSHOT rather than being pruned — they're part of the communication grammar, not task history.

---

## Collapse vs. Drop Decision

When unsure whether to drop or collapse:

- **Drop** if the content has no forward-referential value at all (pleasantries, raw tool output post-summary, superseded instructions)
- **Collapse** if the *fact that something happened* might matter even if the details don't (decisions, accepted specs, error diagnoses)
- **Keep** if the specific content might be re-referenced by the model or another agent

When in doubt, collapse to a single line rather than keeping the full exchange.

---

## Anti-Patterns

| Pattern | Problem | Fix |
|---|---|---|
| Carrying full conversation history across sessions | All prior context costs tokens every call | Checkpoint to STATE_SNAPSHOT at session end |
| Keeping raw tool output after summarizing it | Redundant with the summary | Drop raw, keep summary |
| Re-injecting prior turns for "context" | Usually already in window; if not, use STATE_SNAPSHOT | Reference by task_id, don't re-paste |
| Never pruning because "it might be useful" | Window fills; model routes around noise | Apply the forward-relevance test strictly |
| Pruning the wrong layer (deleting current task, keeping resolved one) | Loses active work | Always prune oldest resolved tasks first |

---

## Integration with MATOCP

MATOCP's `STATE_SNAPSHOT` is the checkpoint format. This skill defines the *rules for what goes in it*: only forward-relevant state, collapsed decisions, active constraints, and the session lexicon. The snapshot should be smaller than the context it replaces — if it isn't, the collapse rules weren't applied.

`!REQ` and `!ASK` in flight are never pruned until resolved — they represent open dependencies that will affect the next step.

---

## Quick Checklist

At each task boundary:

- [ ] Are resolved tasks dropped or collapsed to final output only?
- [ ] Are superseded instructions gone?
- [ ] Is raw tool output replaced by its summary?
- [ ] Are corrected examples collapsed to correct-only?
- [ ] Is the deliberation collapsed to decision + one-line rationale?
- [ ] Does the STATE_SNAPSHOT contain only forward-relevant state?
- [ ] Are active constraints, unresolved errors, and the session lexicon still in the snapshot?
- [ ] Is the snapshot smaller than what it replaced?
