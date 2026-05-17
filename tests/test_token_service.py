from vibecode.services.token_service import TokenService


def test_estimate_tokens() -> None:
    assert TokenService.estimate_tokens("") == 0
    assert TokenService.estimate_tokens("abcd") == 1
    assert TokenService.estimate_tokens("a" * 8) == 2


def test_estimate_tokens_saved() -> None:
    assert TokenService.estimate_tokens_saved(100, 20) == 80
    assert TokenService.estimate_tokens_saved(20, 100) == 0


def test_savings_percent() -> None:
    assert TokenService.savings_percent(100, 25) == 25.0
    assert TokenService.savings_percent(0, 25) == 0.0
