#!/usr/bin/env python3
"""Tests for the redaction guard (TASK-191). All credential fixtures are
deliberately fake (AWS documentation examples, invented tokens)."""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
MAP_EMERGENCE = ROOT / "scripts" / "map_emergence.py"

sys.path.insert(0, str(ROOT / "scripts"))

from redaction import Finding, guard, redact, scan

# Official AWS documentation example credentials -- fake by definition.
FAKE_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
FAKE_AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"


def kinds_of(text):
    return [f.kind for f in scan(text)]


def test_known_pattern_families_one_each():
    cases = {
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIfake\n-----END RSA PRIVATE KEY-----",
        "anthropic_key": "sk-ant-api03-FaKe0Token1MaterialHere2",
        "openai_key": "sk-proj-FaKe0Token1MaterialHere2",
        "github_fine_grained": "github_pat_11FAKE0FAKE0FAKE0FAKE0FAKE0FAKE0",
        "github_token": "ghp_FaKe0Token1FaKe2Token3FaKe4Token5",
        "aws_access_key": FAKE_AWS_KEY,
        "google_api_key": "AIzaFaKe0Token1FaKe2Token3FaKe4Token567",
        "slack_token": "xoxb-1234567890-FaKeToken",
        "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.FaKeSig",
        "bearer_token": "Authorization: Bearer FaKe0Token1Material",
    }
    for expected_kind, secret in cases.items():
        clean, findings = redact(f"leaked: {secret} in a record")
        assert [f.kind for f in findings] == [expected_kind], \
            f"{expected_kind}: got {[f.kind for f in findings]}"
        assert f"[REDACTED:{expected_kind}]" in clean
        # no fragment of the secret body survives (prefix words like
        # 'Authorization:' may remain; the token material must not)
        assert secret.split()[-1] not in clean


def test_url_credential_password_only():
    clean, findings = redact("db is postgres://map:Sup3r/Secr3t@db.internal:5432/map")
    assert [f.kind for f in findings] == ["url_credential"]
    assert clean == "db is postgres://map:[REDACTED:url_credential]@db.internal:5432/map"
    # SSH remotes and credential-free URLs never fire
    assert kinds_of("git clone git@github.com:BigCatMellow/MultiAgentProject.git") == []
    assert kinds_of("see https://example.com:8443/path and http://localhost:3000") == []


def test_secret_assignment_value_only_with_prose_guard():
    clean, findings = redact("export DATABASE_PASSWORD=hunter2secret99")
    assert [f.kind for f in findings] == ["secret_assignment"]
    assert clean == "export DATABASE_PASSWORD=[REDACTED:secret_assignment]"
    # documentation prose never fires: no digit in the value
    for prose in ("api_key: required", "the password: rotate it quarterly",
                  "token = placeholder", "secret: TBD."):
        assert kinds_of(prose) == [], prose
    # a vendor key as the value keeps its precise label, not secret_assignment
    clean, findings = redact("api_key = sk-ant-api03-FaKe0Token1MaterialHere2")
    assert [f.kind for f in findings] == ["anthropic_key"]
    assert "[REDACTED:anthropic_key]" in clean


def test_bare_aws_secret_value_and_guards():
    clean, findings = redact(f"old secret was {FAKE_AWS_SECRET} rotate it")
    assert "aws_secret_value" in [f.kind for f in findings]
    assert FAKE_AWS_SECRET not in clean
    # 40-char single-case runs (e.g. git SHA-1) never fire this pass
    sha = "f3d17de96b66ad5f56a3f29cf8bcb57b7aed83fe"
    assert kinds_of(f"commit {sha} on main") == []


def test_entropy_true_positive():
    tok = "Zk9Q2mVx7Lp4Rt6Yw1Nf3Hd8Bc5Jg0Ks2Pv4Ua7Xe"  # 42-char mixed base62
    clean, findings = redact(f"value {tok} end")
    assert [f.kind for f in findings] == ["high_entropy"]
    assert tok not in clean
    assert findings[0] == Finding(kind="high_entropy", length=len(tok))


def test_entropy_false_positive_guards():
    survivors = [
        # git SHA-1 and SHA-256: pure hex, any length -- documented ignore
        "commit f3d17de96b66ad5f56a3f29cf8bcb57b7aed83fe on main",
        "digest e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        # UUID: hyphen-segmented, segments far below the 32-char minimum
        "session f1a0e903-798f-44cc-a2f1-873abd2f3073 resumed",
        # paths, URLs, branches, snake_case: separators excluded by construction
        "/home/home/Projects/MultiAgentProject/MAP_System/scripts/limit_watcher.py",
        "https://github.com/BigCatMellow/MultiAgentProject/blob/main/CHANGELOG.md",
        "branch feat/task-191-redaction-guard-for-capture-pipelines",
        "mcp__claude_ai_Google_Drive__download_file_content",
        # long single-case run: documented ignore
        "aaaabbbbccccddddeeeeffffgggghhhhiiiijjjj is repeated padding",
    ]
    for text in survivors:
        clean, findings = redact(text)
        assert findings == [], f"false positive on: {text!r} -> {findings}"
        assert clean == text


def test_redact_preserves_surrounding_text():
    text = f"Before. Key {FAKE_AWS_KEY} used by staging; see TASK-191.\nAfter."
    clean, findings = redact(text)
    assert clean == ("Before. Key [REDACTED:aws_access_key] used by staging; "
                     "see TASK-191.\nAfter.")
    assert len(findings) == 1
    # idempotent: a second pass over redacted text finds nothing
    assert scan(clean) == []


def test_guard_warns_stderr_and_returns_clean():
    stream = io.StringIO()
    clean = guard(f"note with {FAKE_AWS_KEY} inside", "unit-test", stream=stream)
    assert "[REDACTED:aws_access_key]" in clean
    warning = stream.getvalue()
    assert "redaction-guard: unit-test" in warning
    assert "aws_access_key x1" in warning
    assert FAKE_AWS_KEY not in warning
    # clean input: silent, unchanged
    stream = io.StringIO()
    assert guard("plain text", "unit-test", stream=stream) == "plain text"
    assert stream.getvalue() == ""


def test_wired_emergence_create_redacts_on_disk():
    """Integration: emergence create with a fake key in --summary writes a
    [REDACTED:...] record and warns on stderr. Temp root, not the real tree."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        (root / "emergence" / "templates").mkdir(parents=True)
        template_src = ROOT / "emergence" / "templates"
        for tpl in template_src.glob("*.md"):
            (root / "emergence" / "templates" / tpl.name).write_text(
                tpl.read_text(encoding="utf-8"), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(MAP_EMERGENCE), "--root", str(root),
             "insight", f"observed leak of {FAKE_AWS_KEY} during capture",
             "--source", "TASK-191 test"],
            cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert result.returncode == 0, result.stderr
        record = next((root / "emergence" / "insights").glob("INS-*.md"))
        text = record.read_text(encoding="utf-8")
        assert FAKE_AWS_KEY not in text
        assert "[REDACTED:aws_access_key]" in text
        assert "redaction-guard: emergence create INS-0001" in result.stderr


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} redaction tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
