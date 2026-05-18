from __future__ import annotations

from pathlib import Path

from vibecode.harvest.extractors.changelog_fix import ChangelogFixExtractor


def test_changelog_fix_extractor_emits_failure_patterns_for_fixed_and_security() -> None:
    fixture = Path("tests/fixtures/harvest/CHANGELOG.md")
    extractor = ChangelogFixExtractor()

    items = extractor.extract(fixture, "CHANGELOG.md")

    assert len(items) == 2
    assert all(item.memory_type == "failure_pattern" for item in items)
    assert all(item.source_type == "harvest:changelog" for item in items)
    assert any("duplicate harvest writes" in (item.prevention_rule or "").lower() for item in items)
    assert any(item.severity == "high" for item in items)
