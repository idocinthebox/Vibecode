from __future__ import annotations

from pathlib import Path

from vibecode.harvest.extractors.adr import ADRExtractor


def test_adr_extractor_emits_accepted_decision_as_architecture_rule() -> None:
    fixture = Path("tests/fixtures/harvest/ADR-0001.adr.md")
    extractor = ADRExtractor()

    items = extractor.extract(fixture, "docs/adr/ADR-0001.adr.md")

    assert len(items) == 1
    item = items[0]
    assert item.memory_type == "project_rule"
    assert item.rule_type == "architecture"
    assert item.source_type == "harvest:adr"
    assert "sqlite" in item.rule_text.lower()
