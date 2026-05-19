from __future__ import annotations


def test_cmd_doctor_warns_on_service_version_drift(temp_base, monkeypatch, capsys) -> None:
    import vibecode.config.paths as _paths

    monkeypatch.setattr(_paths, "get_vibecode_dir", lambda: temp_base)
    monkeypatch.setattr("vibecode.cli.commands_doctor._fetch_service_openapi_version", lambda: "0.3.0")

    from vibecode.cli.commands_doctor import cmd_doctor

    try:
        cmd_doctor()
    except SystemExit:
        pass

    out = capsys.readouterr().out
    assert "Service version" in out
    assert "WARNING" in out
