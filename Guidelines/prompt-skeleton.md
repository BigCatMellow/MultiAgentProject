# Prompt Skeleton — Input Compression

Compress what goes *in* to the model. Every token in the prompt costs the same as a token in the response. The model already knows most things — state only what it doesn't.

---

## Core Rule

**A prompt should contain exactly the information the model cannot infer from its training, the task context, or the output schema.**

Everything else is noise.

---

## The Three Mechanisms

### 1. Schema-First

Lead with the output shape, not a prose description of what you want. The schema *is* the instruction — it specifies structure, field names, and implicit constraints without a paragraph of explanation.

**❌ Prose-first:**
> Please analyze this function and tell me about any issues you find. I'm particularly interested in security vulnerabilities, performance bottlenecks, and code quality problems. For each issue, let me know which line it's on and give me a description of what's wrong.

**✅ Schema-first:**
```
Audit: src/auth.py
Return: {issues: [{type: "security|perf|quality", line: N, desc: str}]}
```

The return schema makes the prose redundant. The model knows what "audit" means; you only need to specify the output shape.

Apply this pattern to every prompt where the output is structured: **schema first, task second, context third.**

---

### 2. Negative Space

State only deviations from the obvious default. The model has strong priors about what good code, good prose, and good analysis look like. Don't re-specify the baseline — only specify where you diverge from it.

**❌ Over-specified:**
> Write a Python function that takes a list of integers as input, iterates through them, and returns the sum. Make sure to handle edge cases. Use clear variable names. Add a docstring.

**✅ Negative space:**
> Sum a list of ints. Skip `None` values silently.

The "clear variable names" and "handle edge cases" are the default. The silent `None` skip is the deviation — the only thing worth stating.

**What counts as a baseline the model already knows:**
- Clean, idiomatic code in the target language
- Sensible error handling
- Reasonable variable naming
- Standard output format for the task type
- Common-sense scope (don't overengineer a one-liner)

**What requires explicit statement:**
- Constraints that conflict with the baseline ("no external deps", "must run in <2ms", "ES5 only")
- Domain-specific requirements the model can't infer
- Non-obvious output format requirements
- Side effects that wouldn't be expected

---

### 3. No Re-Explanation

Don't explain things the model already knows. Don't re-summarize context that's already in the conversation. Don't define standard terms.

| ❌ Re-explanation | ✅ Compressed |
|---|---|
| "As we discussed, the auth module uses JWT tokens stored in Redis..." | "Update auth.py:" |
| "Python's `pathlib` module provides object-oriented filesystem paths..." | *(just use it)* |
| "Remember to follow best practices for security..." | *(it will)* |
| "As you know, REST APIs use HTTP verbs..." | *(omit entirely)* |

**In a multi-turn or multi-agent context:** if the information is already in the STATE_SNAPSHOT or earlier in the conversation, don't restate it. Reference it by name if needed (`"see task 89a2"`), don't copy it in.

---

## Prompt Structure Order

When a prompt needs all three layers, order them:

```
1. Output schema (what shape is the answer)
2. Task verb + target (what to do, to what)
3. Constraints (only the non-default ones)
4. Context (only what isn't already known)
```

**Example:**
```
Return: {verdict: "pass|fail", issues: [str]}
Lint: src/billing.py
Constraints: flag any direct SQL string concat; ignore line-length
```

Not:
```
I need you to review the billing module for code quality issues. Please go through
src/billing.py carefully and look for any problems. Pay special attention to SQL
injection risks where strings are concatenated directly into queries. You don't
need to worry about line length for this one. Return a verdict of pass or fail and
list any issues you find.
```

Same information. ~80% fewer tokens.

---

## What Never Gets Compressed

**Security constraints.** If there's a non-obvious security requirement, state it explicitly. "No PII in logs" isn't a universal default — say it.

**Genuine ambiguity.** If the task is ambiguous in a way that would produce wrong output, resolve it in the prompt. Don't assume the model will guess correctly.

**Cross-session or cross-agent context.** If the model or agent receiving this prompt doesn't have the prior conversation, give it the minimum necessary context. Don't assume shared state that doesn't exist.

**Format requirements that break from the standard.** If you need something genuinely unusual — a specific delimiter, a non-standard field name, a legacy format — specify it. Non-default formatting isn't inferrable.

---

## Anti-Patterns

| Pattern | Problem | Fix |
|---|---|---|
| Restating the task type ("Write a function that...") | Model knows what a function is | Start with the function signature or schema |
| Explaining standard library behavior | Model knows stdlib | Just use it |
| "Be concise and clear" | Baseline instruction, always applies | Drop it |
| "Make sure to handle errors" | Default behavior | Drop it, or specify *which* errors need *which* treatment |
| Repeating context already in STATE_SNAPSHOT | Doubles token cost | Reference by task_id or key name |
| Full examples when one suffices | Over-specified | One tight example > three verbose ones |

---

## In a Multi-Agent Pipeline

Schema-first prompting pairs with MATOCP wire formats (`llm-communication-rules.md` §3): the output schema in the prompt should match the YAML/JSON structure the next agent expects to receive. Aligning prompt schema with wire format eliminates any translation step between generation and consumption.

```
Return YAML:
  task_id: str
  verdict: "pass|fail|warn"
  patches: [{target: path, diff: str}]

Review: src/auth.py against OWASP Top 10
```

The downstream agent receives exactly the shape it can `!ACK` and act on, with no parsing step.

---

## Quick Checklist

Before sending any prompt:

- [ ] Does the schema come first?
- [ ] Does the prompt state any baseline behavior that the model already knows? (Cut it.)
- [ ] Does the prompt restate context that's already in the conversation or STATE_SNAPSHOT? (Cut it.)
- [ ] Does every constraint in the prompt represent a *deviation* from the default?
- [ ] Are genuine ambiguities, security requirements, and non-default formats still explicit?
