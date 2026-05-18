from __future__ import annotations

from pathlib import Path

from vibecode.harvest.extractors.markdown_rule import MarkdownRuleExtractor


def test_markdown_rule_extractor_detects_rules_and_failure_sections(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    doc.write_text(
        """
# Project Guide

Always run tests before commit.

## Common Mistake: external player in UI
Using an external player broke the embedded UX.

```python
open_external_player(file_path)
```

Fix: Use the embedded player widget with in-app controls.
""".strip(),
        encoding="utf-8",
    )

    extractor = MarkdownRuleExtractor()
    items = extractor.extract(doc, "README.md")

    assert any(item.memory_type == "project_rule" for item in items)
    failures = [item for item in items if item.memory_type == "failure_pattern"]
    assert failures
    failure = failures[0]
    assert "external player" in failure.title.lower()
    assert "embedded player widget" in failure.prevention_rule.lower()
    assert failure.bad_suggestion
