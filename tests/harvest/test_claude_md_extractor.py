from __future__ import annotations

from pathlib import Path

from vibecode.harvest.extractors.claude_md import ClaudeMdExtractor


def test_claude_md_extractor_produces_rules_from_imperative_lines() -> None:
    fixture = Path("tests/fixtures/harvest/CLAUDE.md")
    extractor = ClaudeMdExtractor()

    items = extractor.extract(fixture, "CLAUDE.md")

    assert len(items) >= 3
    assert all(item.memory_type == "project_rule" for item in items)
    assert all(item.source_type == "harvest:claude_md" for item in items)
    texts = [item.rule_text for item in items]
    assert any("Always run the test suite" in t for t in texts)
    assert any("Never add secrets" in t for t in texts)
