from __future__ import annotations

from pathlib import Path

from vibecode.harvest.extractors.linter_config import LinterConfigExtractor


def test_linter_config_extractor_emits_low_severity_style_rules() -> None:
    fixture = Path("tests/fixtures/harvest/pyproject.toml")
    extractor = LinterConfigExtractor()

    items = extractor.extract(fixture, "pyproject.toml")

    assert items
    assert all(item.memory_type == "project_rule" for item in items)
    assert all(item.rule_type == "style" for item in items)
    assert all(item.severity == "low" for item in items)
    assert all(item.source_type == "harvest:linter" for item in items)
    assert any("line-length" in item.rule_text for item in items)
