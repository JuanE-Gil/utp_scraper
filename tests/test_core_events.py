# Task 2.1 — contrato de eventos ampliado (plan §4.1, spec de payloads).
# Sin red: core.download_file es fake por monkeypatch; no hay red.

import os

import pytest

from utp_scraper import core


def _job(url="https://x/f.pdf", ext="pdf", week="Semana_01", title="Doc"):
    return (week, title, f"curso/{week}", url, ext)


@pytest.fixture
def recorder():
    out = []

    def on_event(name, **kw):
        out.append((name, kw))

    return out, on_event


@pytest.fixture
def fake_download_ok(monkeypatch):
    """download_file falso: sin red, siempre ok; replica la regla de nombre
    real del downloader (basename del URL + fallback)."""
    from urllib.parse import urlparse
    from utp_scraper.downloader import sanitize

    seen_calls = []
    def fake(url, ext, dest_folder, fallback_name):
        seen_calls.append((url, ext, dest_folder, fallback_name))
        name = sanitize(os.path.basename(urlparse(url).path)) or f"{sanitize(fallback_name)}.{ext}"
        return "ok", name
    monkeypatch.setattr(core, "download_file", fake)
    return seen_calls


def test_course_started_primero_con_curso_y_total(recorder, fake_download_ok, tmp_path):
    out, cb = recorder
    core.run_jobs([_job(), _job(url="https://x/g.pdf")], str(tmp_path), cb, course="Mecánica")
    name, kw = out[0]
    assert name == "course_started"
    assert kw["curso"] == "Mecánica"
    assert kw["total"] == 2


def test_course_finished_ultimo_con_conteos_iguales_al_retorno(recorder, fake_download_ok, tmp_path):
    out, cb = recorder
    counts = core.run_jobs([_job(), _job(ext="mp3")], str(tmp_path), cb, course="C")
    name, kw = out[-1]
    assert name == "course_finished"
    assert kw["conteos"] == counts


def test_file_started_para_todos_los_intentos_y_no_para_filtrados(
    recorder, fake_download_ok, tmp_path
):
    out, cb = recorder
    core.run_jobs([_job(), _job(url="https://x/a.mp3", ext="mp3")], str(tmp_path), cb, course="C")
    names = [n for n, _ in out]
    # mp3 se filtra sin intento; solo el pdf disparó file_started
    assert names.count("file_started") == 1
    # course_started < file_started < downloaded < course_finished
    assert names.index("course_started") < names.index("file_started") < (
        names.index("downloaded")) < names.index("course_finished")


def test_file_started_y_terminal_coinciden_en_filename(recorder, fake_download_ok, tmp_path):
    out, cb = recorder
    core.run_jobs([_job(url="https://x/mi%20doc.pdf")], str(tmp_path), cb, course="C")
    fs_kw = next(kw for n, kw in out if n == "file_started")
    dl_kw = next(kw for n, kw in out if n == "downloaded")
    assert fs_kw["filename"] == dl_kw["filename"] == "mi doc.pdf"
    assert fs_kw["week"] == "Semana_01" and fs_kw["title"] == "Doc"


def test_filtrado_no_lanza_file_started(recorder, fake_download_ok, tmp_path):
    out, cb = recorder
    core.run_jobs([_job(url="https://x/a.mp3", ext="mp3")], str(tmp_path), cb, course="C")
    assert all(n != "file_started" for n, _ in out)
    assert sum(1 for n, _ in out if n == "filtered_format") == 1
