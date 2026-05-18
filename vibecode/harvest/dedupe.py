from __future__ import annotations

from vibecode.harvest.normalizer import CandidateMemory
from vibecode.services.embedding_service import EmbeddingService


def dedupe_candidates(candidates: list[CandidateMemory]) -> tuple[list[CandidateMemory], int]:
    unique: list[CandidateMemory] = []
    seen_hashes: set[str] = set()
    duplicates = 0
    for candidate in candidates:
        content_hash = candidate.content_hash()
        if content_hash in seen_hashes:
            duplicates += 1
            continue
        seen_hashes.add(content_hash)
        unique.append(candidate)
    return unique, duplicates


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = sum(a * a for a in vec_a) ** 0.5
    mag_b = sum(b * b for b in vec_b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def is_near_duplicate(
    embedding_service: EmbeddingService,
    text_a: str,
    text_b: str,
    threshold: float = 0.92,
) -> bool:
    if not embedding_service.is_available():
        return False
    vec_a = embedding_service.embed(text_a)
    vec_b = embedding_service.embed(text_b)
    if vec_a is None or vec_b is None:
        return False
    return cosine_similarity(vec_a, vec_b) >= threshold


def dedupe_candidates_with_embeddings(
    candidates: list[CandidateMemory],
    embedding_service: EmbeddingService,
    threshold: float = 0.92,
) -> tuple[list[CandidateMemory], int]:
    if not embedding_service.is_available():
        return candidates, 0

    unique: list[CandidateMemory] = []
    duplicates = 0

    for candidate in candidates:
        candidate_text = candidate.dedupe_text() or ""
        is_duplicate = False
        for existing in unique:
            if existing.memory_type != candidate.memory_type:
                continue
            if (existing.language or "") != (candidate.language or ""):
                continue
            existing_text = existing.dedupe_text() or ""
            if is_near_duplicate(
                embedding_service=embedding_service,
                text_a=candidate_text,
                text_b=existing_text,
                threshold=threshold,
            ):
                duplicates += 1
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(candidate)

    return unique, duplicates
