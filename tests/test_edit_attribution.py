from vibecode.core.edit_attribution import normalize_agent_source


def test_normalize_agent_source_values() -> None:
    assert normalize_agent_source("human") == "human"
    assert normalize_agent_source("agent:GitHub.copilot") == "agent:GitHub.copilot"
    assert normalize_agent_source("GitHub.copilot") == "agent:GitHub.copilot"
    assert normalize_agent_source("") == "unknown"
