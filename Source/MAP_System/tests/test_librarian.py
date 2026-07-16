#!/usr/bin/env python3
"""Tests for the MAP librarian agent (wikilinks, backlinks, measurement)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.librarian import (  # noqa: E402
    build_name_index,
    resolve_wikilink,
    validate_wikilinks_in_file,
    validate_all_wikilinks,
    build_backlink_index,
    add_wikilinks_to_related_section,
    structural_summary,
    measure_compression,
    _tokenish_count,
    _resolve_related_bullet_path,
)


def _make_fixture_tree(tmp: Path) -> None:
    (tmp / "a.md").write_text("# A\n\nHello world.\n\n## Related files\n\n- `b.md` — the b doc\n", encoding="utf-8")
    (tmp / "b.md").write_text("# B\n\nBody of B.\n", encoding="utf-8")
    (tmp / "sub").mkdir()
    (tmp / "sub" / "b.md").write_text("# Sub B\n\nA different b.\n", encoding="utf-8")


def test_build_name_index_groups_by_stem() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        index = build_name_index(tmp_path)
        assert len(index["b"]) == 2
        assert len(index["a"]) == 1


def test_resolve_wikilink_unambiguous_stem() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        targets = resolve_wikilink("a", root=tmp_path)
        assert len(targets) == 1
        assert targets[0].name == "a.md"


def test_resolve_wikilink_path_shaped_disambiguates_ambiguous_stem() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        # Bare "b" is ambiguous (2 files); a path-shaped name must resolve
        # to exactly the one it names, not dissolve back into all matches.
        targets = resolve_wikilink("sub/b", root=tmp_path)
        assert len(targets) == 1
        assert targets[0] == tmp_path / "sub" / "b.md"


def test_validate_wikilinks_flags_broken_link() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        (tmp_path / "c.md").write_text("See [[nonexistent]] for details.\n", encoding="utf-8")
        findings = validate_wikilinks_in_file(tmp_path / "c.md", build_name_index(tmp_path))
        assert len(findings) == 1
        assert findings[0]["issue"] == "broken"


def test_validate_wikilinks_flags_ambiguous_link() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        (tmp_path / "c.md").write_text("See [[b]] for details.\n", encoding="utf-8")
        findings = validate_wikilinks_in_file(tmp_path / "c.md", build_name_index(tmp_path))
        assert len(findings) == 1
        assert findings[0]["issue"] == "ambiguous"


def test_validate_wikilinks_passes_clean_unambiguous_link() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        (tmp_path / "c.md").write_text("See [[a]] for details.\n", encoding="utf-8")
        findings = validate_all_wikilinks(tmp_path)
        assert findings == []


def test_add_wikilinks_to_related_section_dry_run_does_not_write() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        original = (tmp_path / "a.md").read_text(encoding="utf-8")
        result = add_wikilinks_to_related_section(tmp_path / "a.md", root=tmp_path, dry_run=True)
        assert result["converted"] == 1
        assert (tmp_path / "a.md").read_text(encoding="utf-8") == original


def test_add_wikilinks_to_related_section_apply_writes_and_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        result = add_wikilinks_to_related_section(tmp_path / "a.md", root=tmp_path, dry_run=False)
        assert result["converted"] == 1
        text = (tmp_path / "a.md").read_text(encoding="utf-8")
        assert "[[b]]" in text
        assert "`b.md`" in text, "original backtick path must be preserved, not removed"

        # Running again must not double-add a wikilink to the same bullet.
        second = add_wikilinks_to_related_section(tmp_path / "a.md", root=tmp_path, dry_run=False)
        assert second["converted"] == 0
        assert second["skipped_already_linked"] == 1


def test_add_wikilinks_disambiguates_ambiguous_stem() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        (tmp_path / "c.md").write_text(
            "# C\n\n## Related files\n\n- `sub/b.md` — the nested b doc\n", encoding="utf-8",
        )
        result = add_wikilinks_to_related_section(tmp_path / "c.md", root=tmp_path, dry_run=False)
        assert result["converted"] == 1
        text = (tmp_path / "c.md").read_text(encoding="utf-8")
        assert "[[sub/b]]" in text, "ambiguous stem 'b' must be disambiguated to a full relative path"
        assert "[[b]]" not in text


def test_resolve_related_bullet_path_own_dir_relative() -> None:
    """librarian-batch2 helper diagnosed this: a bare filename in a
    Related-Files bullet, written from a file in a subdirectory, means a
    path relative to THAT file's own directory (e.g.
    'sub/README.md' -> 'SIBLING.md' means 'sub/SIBLING.md'), not relative
    to the tool's root.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "README.md").write_text("# Sub README\n", encoding="utf-8")
        (tmp_path / "sub" / "SIBLING.md").write_text("# Sibling\n", encoding="utf-8")
        resolved = _resolve_related_bullet_path(
            "SIBLING.md", tmp_path / "sub" / "README.md", root=tmp_path, repo=tmp_path.parent,
        )
        assert resolved == tmp_path / "sub" / "SIBLING.md"


def test_resolve_related_bullet_path_repo_root_relative() -> None:
    """The other convention the helper found: an explicit repo-root-style
    prefix (mirroring MAP_System/... in the real repo) must resolve
    against the repo root, not be doubled onto the tool's root.
    """
    with tempfile.TemporaryDirectory() as tmp:
        repo_path = Path(tmp)
        root_path = repo_path / "MAP_System"
        root_path.mkdir()
        (root_path / "target.md").write_text("# Target\n", encoding="utf-8")
        source = root_path / "sub"
        source.mkdir()
        (source / "referrer.md").write_text("# Referrer\n", encoding="utf-8")

        resolved = _resolve_related_bullet_path(
            "MAP_System/target.md", source / "referrer.md", root=root_path, repo=repo_path,
        )
        assert resolved == root_path / "target.md"


def test_resolve_related_bullet_path_skips_guidelines_prefixed() -> None:
    """Guidelines/ is a separate cross-project scope this tool's
    validate/backlinks commands don't index by default -- resolving (and
    thus wikilinking) a Guidelines/ reference would produce a link
    `validate` could never confirm, so it's intentionally left unresolved.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        resolved = _resolve_related_bullet_path(
            "Guidelines/6.13/MAP-Gap-Register.md", tmp_path / "a.md", root=tmp_path, repo=tmp_path,
        )
        assert resolved is None


def test_add_wikilinks_resolves_own_dir_relative_bullets() -> None:
    """End-to-end regression for the librarian-batch2 finding: a
    subdirectory file whose Related-Files bullet uses a bare, own-dir-
    relative filename must now convert, not silently skip as unresolved."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "SIBLING.md").write_text("# Sibling\n", encoding="utf-8")
        (tmp_path / "sub" / "referrer.md").write_text(
            "# Referrer\n\n## Related files\n\n- `SIBLING.md` — the sibling doc\n", encoding="utf-8",
        )
        result = add_wikilinks_to_related_section(tmp_path / "sub" / "referrer.md", root=tmp_path, dry_run=False)
        assert result["converted"] == 1
        assert result["skipped_unresolved"] == 0
        text = (tmp_path / "sub" / "referrer.md").read_text(encoding="utf-8")
        assert "[[SIBLING]]" in text


def test_build_backlink_index_reflects_real_links() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        add_wikilinks_to_related_section(tmp_path / "a.md", root=tmp_path, dry_run=False)
        index = build_backlink_index(tmp_path)
        assert index.get("b.md") == ["a.md"]


def test_structural_summary_is_much_shorter_than_source() -> None:
    text = "# Title\n\n## Sec1\n\n" + ("word " * 500) + "\n\n## Sec2\n\nmore body text here.\n"
    summary = structural_summary(text)
    assert _tokenish_count(summary) < _tokenish_count(text)


def test_measure_compression_reports_real_ratios() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _make_fixture_tree(tmp_path)
        result = measure_compression([tmp_path / "a.md", tmp_path / "b.md"])
        assert result["file_count"] == 2
        for entry in result["per_file"]:
            assert entry["compression_ratio"] is not None
            assert entry["compression_ratio"] >= 1.0


def main() -> int:
    tests = [
        test_build_name_index_groups_by_stem,
        test_resolve_wikilink_unambiguous_stem,
        test_resolve_wikilink_path_shaped_disambiguates_ambiguous_stem,
        test_validate_wikilinks_flags_broken_link,
        test_validate_wikilinks_flags_ambiguous_link,
        test_validate_wikilinks_passes_clean_unambiguous_link,
        test_add_wikilinks_to_related_section_dry_run_does_not_write,
        test_add_wikilinks_to_related_section_apply_writes_and_is_idempotent,
        test_add_wikilinks_disambiguates_ambiguous_stem,
        test_resolve_related_bullet_path_own_dir_relative,
        test_resolve_related_bullet_path_repo_root_relative,
        test_resolve_related_bullet_path_skips_guidelines_prefixed,
        test_add_wikilinks_resolves_own_dir_relative_bullets,
        test_build_backlink_index_reflects_real_links,
        test_structural_summary_is_much_shorter_than_source,
        test_measure_compression_reports_real_ratios,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
