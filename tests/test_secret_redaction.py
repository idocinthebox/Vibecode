from vibecode.core.security import redact_secrets


def test_secret_redaction_removes_api_keys() -> None:
    text = "OPENAI_API_KEY=sk-abc123def456\nANTHROPIC_API_KEY=sk-ant-xyz"
    result = redact_secrets(text)
    assert "sk-abc123def456" not in result
    assert "sk-ant-xyz" not in result
    assert "[REDACTED_SECRET]" in result


def test_secret_redaction_removes_passwords() -> None:
    text = "DATABASE_URL=postgres://user:secret@localhost/db\nPASSWORD=hunter2"
    result = redact_secrets(text)
    assert "hunter2" not in result
    assert "[REDACTED_SECRET]" in result


def test_secret_redaction_removes_private_keys() -> None:
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
    result = redact_secrets(text)
    assert "MIIEpAIBAAKCAQEA" not in result
    assert "[REDACTED_SECRET]" in result
