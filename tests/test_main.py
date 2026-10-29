import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: F401

import utp_scraper.main as m


def test_main_exits_without_credentials(monkeypatch, capsys):
    for var in ("AUTH_TOKEN", "USER_ID", "TENANT_ID"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(SystemExit) as e:
        m.main()
    assert e.value.code == 1
    out = capsys.readouterr().out
    assert "AUTH_TOKEN" in out or "credenciales" in out.lower()
