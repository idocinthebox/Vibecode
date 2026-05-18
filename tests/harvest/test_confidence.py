from __future__ import annotations

import math

from vibecode.harvest.confidence import compute_confidence


def test_confidence_formula_matches_expected_value() -> None:
    # Hand-computed from spec formula:
    # score = 0.4*0.9 + 0.3*0.8 + 0.2*exp(-30/180) + 0.1*0.7
    expected = 0.4 * 0.9 + 0.3 * 0.8 + 0.2 * math.exp(-(30 / 180)) + 0.1 * 0.7
    score = compute_confidence(0.9, 0.8, 30.0, 0.7)
    assert score == round(expected, 4)
