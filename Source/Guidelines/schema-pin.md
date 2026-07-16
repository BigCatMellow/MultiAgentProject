# Schema Pin — Output Format Enforcement

When the output will be parsed, pin the schema upfront. Prose wrapping around structured data is tokens generated and immediately discarded. The model will fill a schema more tightly than it will wrap data in natural language.

---

## Core Rule

**If any part of the response will be parsed by code rather than read by a human, pin the exact output schema before the task.**

Pinning = including the schema in the prompt, before the task description, so the model treats it as a constraint rather than a suggestion.

---

## When to Schema-Pin

Pin whenever any of these are true:

- The output will be consumed by code (`JSON.parse`, `yaml.load`, `re.match`)
- The response contains multiple structured fields
- The receiver is another agent, not a human
- The same output shape is expected across multiple calls
- Downstream processing will fail or branch on the structure

---

## When NOT to Schema-Pin

Don't pin when:

- The output is human-readable reasoning or analysis
- The structure genuinely can't be known in advance (open-ended exploration)
- The task is creative or open-ended and the shape should emerge from the content
- You're asking the model to *design* a schema, not fill one

Pinning a schema on a reasoning task forces the model to compress genuine analysis into fields that may not fit it, producing worse output at the same token cost.

---

## Schema Design Rules

A pinned schema that's loose costs almost as many tokens as prose. Design tight.

**No prose fields unless the prose IS the product.**
```yaml
# ❌ Loose — the "explanation" field will generate a paragraph
{verdict: str, explanation: str, issues: [str]}

# ✅ Tight — if you need a reason, cap it
{verdict: "pass|fail|warn", reason: str(<80chars), issues: [{line: N, type: str}]}
```

**Enums over open strings where the space is finite.**
```yaml
# ❌ Open string — model will invent values
{status: str}

# ✅ Enum — constrained vocabulary, fewer tokens, parseable
{status: "pending|active|resolved|blocked"}
```

**Flat over nested where possible.**
Nested structures generate more tokens (keys, brackets, indentation) and are harder to validate. Only nest when the relationship is genuinely hierarchical.

```yaml
# ❌ Unnecessary nesting
{result: {code: N, message: str, details: {line: N, column: N}}}

# ✅ Flat
{code: N, message: str, line: N, col: N}
```

**Explicit required vs. optional. Default optional fields.**
Don't let the model decide which fields to emit. Every field should either always appear or have an explicit default.

```yaml
# Pin this in the prompt:
# Required: verdict, task_id
# Optional: issues (default []), notes (default null)
```

**No null where absent is meaningful.**
`null` and absent mean different things. Decide which you want and pin it. Mixing them forces the parser to handle both.

**Short, consistent key names.**
Key names are tokens too. `t` beats `type` if `t` is unambiguous in context. For agent-to-agent payloads where both sides control the schema, abbreviate.

---

## Pinning Syntax

Include the schema *before* the task description in the prompt. Two formats:

**Inline type annotation (fast, for simple shapes):**
```
Return JSON: {verdict: "pass|fail", issues: [{line: int, desc: str}], task_id: str}
Audit: src/auth.py for SQL injection
```

**Explicit schema block (for complex shapes or when the schema is shared):**
```
Output schema:
  task_id: string (required)
  verdict: enum[pass, fail, warn] (required)
  patches: array of {target: path, diff: string} (optional, default [])
  notes: string <100 chars (optional, default null)

Task: review src/billing.py against OWASP A03
```

Both work. Use inline for simple shapes; block for anything with optionals, defaults, or shared across multiple agents.

---

## Before / After

**❌ Unpinned:**

Prompt:
> Review auth.py and tell me if there are any security issues. List the issues you find.

Response (typical):
> After reviewing `auth.py`, I found several security concerns worth addressing:
>
> 1. **SQL Injection Risk** (Line 45): The query on line 45 concatenates user input directly...
> 2. **Missing Rate Limiting** (Line 112): The login endpoint at line 112 does not implement...
>
> Overall, I would recommend addressing the SQL injection issue first as it poses the most immediate risk.

Tokens: ~120. Parser has to strip prose, extract line numbers from markdown, infer severity.

**✅ Pinned:**

Prompt:
```
Return JSON: {issues: [{line: int, type: "sqli|auth|crypto|dos", sev: "high|med|low", desc: str(<60chars)}]}
Audit: src/auth.py
```

Response:
```json
{"issues": [{"line": 45, "type": "sqli", "sev": "high", "desc": "direct user input in query string"}, {"line": 112, "type": "dos", "sev": "med", "desc": "no rate limiting on login endpoint"}]}
```

Tokens: ~55. Zero parsing overhead. Directly machine-consumable.

---

## Format Choice: JSON vs. YAML

Both are valid (MATOCP §3.1). Decision criteria:

| Condition | Prefer |
|---|---|
| Output goes directly into code (`JSON.parse`) | JSON |
| Output is human-reviewed before use | YAML |
| Schema has type-ambiguous values (booleans, version strings) | JSON (no coercion risk) |
| Multi-line string values | YAML |
| Compact single-line payloads | JSON |

When in doubt: JSON. It sidesteps YAML's type coercion edge cases and is universally parseable without a library in most runtimes.

---

## Validation on Receipt

Pin the schema in the prompt; validate it on receipt. Don't trust that the model always emits exactly the pinned shape — it usually does, but not always.

Minimum validation:
- All required fields present
- Enum fields contain only expected values
- Array fields are arrays (not null, not a string)

If validation fails, emit `!ERR schema_mismatch reason="missing field: verdict"` rather than silently processing a malformed response.

---

## Integration with MATOCP

Schema-pinned outputs slot directly into MATOCP wire formats. The `!STATE` payload, `!PATCH` target, and `!ERR` reason field all have implicit schemas — make them explicit when the pipeline is complex enough to benefit.

For agent-to-agent calls where Claude is both sender and receiver across turns, carry the schema in `STATE_SNAPSHOT` under a `schemas` key so it doesn't need to be re-stated in every prompt:

```yaml
schemas:
  audit_result: "{issues: [{line: int, type: str, sev: str, desc: str}]}"
  patch_result: "{target: path, applied: bool, err: str|null}"
```

Reference by name in prompts: `Return audit_result schema.`

---

## Quick Checklist

Before any prompt where output will be parsed:

- [ ] Is the schema pinned before the task description?
- [ ] Are all string fields that have finite vocabularies expressed as enums?
- [ ] Are optional fields given explicit defaults?
- [ ] Is nesting minimal — flat where possible?
- [ ] Are key names as short as unambiguously possible?
- [ ] Is JSON preferred over YAML for machine-consumed output?
- [ ] Is validation-on-receipt implemented for required fields and enum values?
- [ ] For shared schemas across agents: is the schema in STATE_SNAPSHOT?
