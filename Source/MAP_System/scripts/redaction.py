#!/usr/bin/env python3
"""Redaction guard for MAP capture pipelines (TASK-191).

Secrets and credentials must not reach durable MAP records. Capture CLIs call
`guard(text, source)` on body text before writing: known credential shapes,
URL userinfo passwords, sensitive-assignment values, and high-entropy tokens
are replaced with `[REDACTED:<pattern-name>]`; findings are warned to stderr
so the author sees what was scrubbed; the clean text is what lands on disk.
Warn-and-redact, never reject.

Patterns adapt agentcairn's scrubbing rules (repo/agentcairn-main
src/cairn/ingest/redact.py, incl. its 2026-06-11 over-firing fix) without
vendoring. Bias is conservative -- for MAP records a false positive (mangled
documentation) is worse than a missed exotic secret shape.

The entropy fallback deliberately ignores (documented misses):

- pure-hex runs of ANY length (git SHA-1/SHA-256, digests, UUID segments) --
  a bare hex signing secret is only caught when it appears in a sensitive
  assignment (`signing_secret=...`);
- single-case tokens (long lowercase base32/base36 secrets) -- prose words,
  repeated padding, and identifiers would otherwise dominate findings;
- tokens containing '/', '-', or '_' (paths, URLs, branches, slugs,
  snake_case can never form a candidate by construction; agentcairn's
  2026-06-11 audit found ~99% of entropy hits were such identifiers).

Threshold choice: candidates are [A-Za-z0-9+] runs >= 32 chars (packet
minimum; UUID hyphen-segments and most identifiers fall short) with
upper+lower+digit mixed charset and Shannon entropy >= 3.5 bits/char
(random base62 measures ~5.2; English-ish camelCase words sit well below).
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    """One redaction: the pattern family that fired and the length of the
    replaced text. The matched text itself is never carried (it is a secret)."""
    kind: str
    length: int


# URL / connection-string credential: scheme://user:password@host. Password
# class allows '/' and anchors on the FIRST '@' so a slash cannot defeat the
# match; SSH remotes (git@..., no ://) and plain host:port URLs never match.
_URL_CRED_RE = re.compile(r"([a-z][a-z0-9+.-]*://[^/\s:@]*:)([^@\s]+)(@)", re.IGNORECASE)

# Known credential formats. Order matters: multi-line PEM first; anthropic
# before openai (sk-ant- is a sk- prefix superset).
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key",
     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
                re.DOTALL)),
    # Lookbehinds keep prefixes from firing inside words: 'task-191-...'
    # contains 'sk-' and must never match (found by this task's own fixtures).
    ("anthropic_key", re.compile(r"(?<![A-Za-z0-9])sk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai_key", re.compile(r"(?<![A-Za-z0-9])sk-(?:proj-)?[A-Za-z0-9_-]{20,}")),
    ("github_fine_grained", re.compile(r"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{30,}")),
    ("github_token", re.compile(r"(?<![A-Za-z0-9])gh[posru]_[A-Za-z0-9]{30,}")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("slack_token", re.compile(r"(?<![A-Za-z0-9])xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}")),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]{12,}")),
]

# Sensitive assignment: key[:=] value for credential-ish key names. Only the
# VALUE is redacted (the key name is audit context). Guarded conservatively:
# the value must be >= 8 chars AND contain a digit -- documentation prose like
# "api_key: required" or "password: rotate it" never fires.
_ASSIGNMENT_RE = re.compile(
    r"(?i)(?<![A-Za-z])"
    r"((?:aws_secret_access_key|secret_access_key|api[_-]?key|secret|token|password|passwd|pwd)"
    r"(?:[_-][A-Za-z0-9]+)*"
    r"(?![A-Za-z0-9])\s*[:=]\s*)"
    r"(\"[^\"]{8,}\"|'[^']{8,}'|[^\s'\"]{8,})"
)

# Bare AWS-style secret value: exactly 40 chars of base64-ish material (may
# contain '/' and '+') standing alone. The entropy token class cannot span
# '/', so this proven agentcairn shape gets its own mixed-charset-guarded
# pass, run BEFORE entropy so a partial match cannot leak the prefix.
_AWS_SECRET_VALUE_RE = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{40}(?![A-Za-z0-9+/=])")

# Entropy fallback bounds -- see module docstring for the reasoning.
_ENTROPY_MIN_LEN = 32
_ENTROPY_BITS = 3.5
_TOKEN_RE = re.compile(rf"[A-Za-z0-9+]{{{_ENTROPY_MIN_LEN},}}")
_HEX_RE = re.compile(r"(?i)^[0-9a-f]+$")

_REDACTED_PREFIX = "[REDACTED:"


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def _mixed_charset(token: str) -> bool:
    return (bool(re.search(r"[A-Z]", token))
            and bool(re.search(r"[a-z]", token))
            and bool(re.search(r"[0-9]", token)))


def _entropy_candidate_is_secret(token: str) -> bool:
    if _HEX_RE.match(token):
        return False  # pure hex never flagged (git SHAs, digests) -- documented
    if not _mixed_charset(token):
        return False  # single-case never flagged -- documented
    return _shannon_entropy(token) >= _ENTROPY_BITS


def redact(text: str) -> tuple[str, list[Finding]]:
    """Return (clean_text, findings). clean_text is safe to write durably.

    Pass order (agentcairn's documented ordering rationale): URL credentials
    first (short passwords beat any threshold), then precise known shapes,
    then assignment values, then the bare AWS shape, entropy last -- so a
    vendor key is consumed whole and never fragmented by the entropy pass.
    """
    findings: list[Finding] = []

    def token(kind: str, matched: str) -> str:
        findings.append(Finding(kind=kind, length=len(matched)))
        return f"{_REDACTED_PREFIX}{kind}]"

    out = _URL_CRED_RE.sub(
        lambda m: f"{m.group(1)}{token('url_credential', m.group(2))}{m.group(3)}", text)

    for kind, pattern in _PATTERNS:
        out = pattern.sub(lambda m, k=kind: token(k, m.group(0)), out)

    def _assignment_sub(m: re.Match[str]) -> str:
        value = m.group(2).strip("\"'")
        if value.startswith(_REDACTED_PREFIX) or not re.search(r"[0-9]", value):
            return m.group(0)  # already labeled by a precise pass, or prose
        return f"{m.group(1)}{token('secret_assignment', m.group(2))}"

    out = _ASSIGNMENT_RE.sub(_assignment_sub, out)

    def _aws_sub(m: re.Match[str]) -> str:
        tok = m.group(0)
        return token("aws_secret_value", tok) if _mixed_charset(tok) else tok

    out = _AWS_SECRET_VALUE_RE.sub(_aws_sub, out)

    def _entropy_sub(m: re.Match[str]) -> str:
        tok = m.group(0)
        return token("high_entropy", tok) if _entropy_candidate_is_secret(tok) else tok

    out = _TOKEN_RE.sub(_entropy_sub, out)

    return out, findings


def scan(text: str) -> list[Finding]:
    """Findings that redact() would produce, without needing the clean text."""
    return redact(text)[1]


def guard(text: str, source: str, *, stream=sys.stderr) -> str:
    """Warn-and-redact wrapper for capture write paths: warns the author on
    stderr about anything scrubbed and returns the text safe to persist."""
    clean, findings = redact(text)
    if findings:
        by_kind: dict[str, int] = {}
        for finding in findings:
            by_kind[finding.kind] = by_kind.get(finding.kind, 0) + 1
        detail = ", ".join(f"{kind} x{count}" for kind, count in sorted(by_kind.items()))
        print(f"redaction-guard: {source}: redacted {len(findings)} secret(s) "
              f"before write ({detail}); the durable record contains "
              f"[REDACTED:<pattern>] placeholders.", file=stream)
    return clean
