from __future__ import annotations

from pathlib import Path

from vibecode.harvest.extractors.inline_comment import InlineCommentExtractor


def test_inline_comment_extractor_reads_vc_rule_and_note_rule_markers() -> None:
    fixture = Path("tests/fixtures/harvest/inline_rules.py")
    extractor = InlineCommentExtractor()

    items = extractor.extract(fixture, "vibecode/config/inline_rules.py")

    assert len(items) == 2
    assert all(item.memory_type == "project_rule" for item in items)
    assert all(item.source_type == "harvest:inline_comment" for item in items)
    assert any(item.severity == "high" for item in items)
    assert any("absolute paths" in item.rule_text.lower() for item in items)
