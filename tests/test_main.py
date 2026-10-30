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


def test_make_handler_solo_cuenta_eventos_terminales():
    """plan §4.1: solo downloaded/skipped_existing/error/filtered_format
    avanzan course_done; file_started/course_started/course_finished no."""
    from utp_scraper.main import make_handler
    from utp_scraper.ui_cli import UiState

    state = UiState()
    rendered = []
    handler = make_handler(state, apply_view=lambda: rendered.append(1))

    handler("course_started", curso="C", total=3)
    handler("file_started", week="Semana_01", title="Doc", filename="f.pdf")
    assert state.course_done == 0

    handler("downloaded", week="Semana_01", title="Doc", filename="f.pdf")
    handler("skipped_existing", week="Semana_01", title="Doc2", filename="g.pdf")
    handler("error", week="Semana_01", title="Doc3", filename="h.pdf", detail="x")
    handler("filtered_format", week="Semana_01", title="Doc4", ext="mp3")
    assert state.course_done == 4

    handler("course_finished", conteos={})
    assert state.course_done == 4  # el fin de curso no es un archivo más
    assert len(rendered) == 7  # la vista se repinta en cada evento recibido
