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


def test_secret_redaction_removes_additional_phase0_patterns() -> None:
    slack_token = "xoxb-" + "1234567890-" + "ABCDEFGHIJKLMNOP"
    jwt_token = "eyJ" + "hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" + ".abc12345.def67890"
    text = (
        "MONGO=mongodb+srv://user:pass@cluster.mongodb.net/db\n"
        f"SLACK={slack_token}\n"
        f"JWT={jwt_token}\n"
        "AWS_SESSION_TOKEN=verylongsessiontoken"
    )
    result = redact_secrets(text)
    assert "mongodb+srv://user:pass@cluster.mongodb.net/db" not in result
    assert slack_token not in result
    assert jwt_token not in result
    assert "verylongsessiontoken" not in result
    assert result.count("[REDACTED_SECRET]") >= 4
