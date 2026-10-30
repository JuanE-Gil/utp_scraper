import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: F401

from utp_scraper.core import collect_jobs, run_jobs
from utp_scraper.downloader import UTP_FILE_DOMAIN

S3 = f"https://{UTP_FILE_DOMAIN}/f.pdf"


class FakeResp:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def raise_for_status(self):
        pass

    def iter_content(self, *a, **k):
        return iter([b"contenido"])


@pytest.fixture
def s3_ok(monkeypatch):
    monkeypatch.setattr("utp_scraper.downloader.requests.get", lambda *a, **k: FakeResp())


def _data(contents=(("FILE", "Guia semana 1", {"url": S3, "filetype": "pdf"}),)):
    return {
        "unities": [
            {
                "themes": [
                    {
                        "weekNumber": 1,
                        "name": "Tema A",
                        "contents": [
                            {"type": t, "title": ti, "metadata": md}
                            for t, ti, md in contents
                        ],
                    }
                ]
            }
        ]
    }


def test_collect_jobs_maps_fields():
    jobs = collect_jobs(_data(), "Mecánica")
    assert len(jobs) == 1
    week_label, title, folder, url, ext = jobs[0]
    assert week_label == "Semana_01"
    assert title == "Guia semana 1"
    assert ext == "pdf"
    assert url == S3
    assert "Mecanica" in folder and "Tema A" in folder
    assert os.sep in folder


def test_collect_jobs_empty_course():
    assert collect_jobs({}, "X") == []
    assert collect_jobs({"unities": []}, "X") == []


def test_collect_jobs_content_without_title_or_id():
    data = _data((("FILE", None, {"url": S3, "filetype": "pdf"}),))
    jobs = collect_jobs(data, "X")
    assert len(jobs) == 1
    assert jobs[0][1] == "contenido"  # fallback, nunca None -> no crash en sanitize


def test_run_jobs_filters_redundant_format(tmp_path):
    data = _data(
        (
            ("FILE", "a", {"url": S3, "filetype": "pdf"}),
            ("FILE", "b", {"url": S3, "filetype": "mp3"}),  # mp3 excluido por defecto
        )
    )
    counts = run_jobs(collect_jobs(data, "C"), str(tmp_path), lambda *a, **k: None)
    assert counts["filtered_format"] == 1


def test_run_jobs_counts_and_events(tmp_path, s3_ok):
    events = []
    counts = run_jobs(collect_jobs(_data(), "C"), str(tmp_path), lambda n, **kw: events.append((n, kw)))
    assert counts["ok"] >= 1
    assert any(n in ("downloaded", "skipped_existing", "error") for n, _ in events)
