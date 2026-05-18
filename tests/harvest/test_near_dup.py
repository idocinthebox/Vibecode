from __future__ import annotations

from vibecode.harvest.dedupe import dedupe_candidates_with_embeddings
from vibecode.harvest.normalizer import CandidateMemory


class FakeEmbeddingService:
    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self._vectors = vectors

    def is_available(self) -> bool:
        return True

    def embed(self, text: str) -> list[float] | None:
        return self._vectors.get(text)


def _candidate(text: str) -> CandidateMemory:
    return CandidateMemory(
        memory_type="project_rule",
        title=text,
        source_path="README.md",
        line_start=1,
        line_end=1,
        source_type="harvest:test",
        extractor="UnitTest",
        signal_strength=0.5,
        rule_text=text,
        language="python",
    )


def test_dedupe_candidates_with_embeddings_dedupes_when_similarity_meets_threshold() -> None:
    c1 = _candidate("Always run tests before commit")
    c2 = _candidate("Always run the tests before commit")

    service = FakeEmbeddingService(
        {
            c1.rule_text: [1.0, 0.0, 0.0],
            c2.rule_text: [0.98, 0.02, 0.0],
        }
    )

    unique, duplicates = dedupe_candidates_with_embeddings([c1, c2], service, threshold=0.92)

    assert len(unique) == 1
    assert duplicates == 1


def test_dedupe_candidates_with_embeddings_keeps_items_below_threshold() -> None:
    c1 = _candidate("Always run tests before commit")
    c2 = _candidate("Never commit secrets")

    service = FakeEmbeddingService(
        {
            c1.rule_text: [1.0, 0.0, 0.0],
            c2.rule_text: [0.0, 1.0, 0.0],
        }
    )

    unique, duplicates = dedupe_candidates_with_embeddings([c1, c2], service, threshold=0.92)

    assert len(unique) == 2
    assert duplicates == 0
