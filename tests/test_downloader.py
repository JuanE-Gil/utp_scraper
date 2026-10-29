import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: F401

from utp_scraper.downloader import UTP_FILE_DOMAIN, download_file, extract_urls_from_html, sanitize

S3_URL_PDF = f"https://{UTP_FILE_DOMAIN}/a/b.pdf"


def test_sanitize_legal_chars():
    assert sanitize('a<b>c:d"e') == "a_b_c_d_e"


def test_sanitize_remove_accents():
    assert sanitize("Método") == "Metodo"


def test_sanitize_empty_fallback():
    assert sanitize(" ") == "sin_nombre"


def test_extract_only_s3_with_whitelist_ext():
    html = (
        '<a href="https://utp-prd-upload-file-storage.s3.amazonaws.com/a/b.pdf">'
        '<img src="https://cdn.externa.com/icon.png"> https://otro-s3.com/x.pdf'
    )
    assert extract_urls_from_html(html) == [(S3_URL_PDF, "pdf")]


def test_extract_dedup_preserves_order():
    html = (
        "dos veces: "
        f"https://{UTP_FILE_DOMAIN}/x.mp4 "
        f"https://{UTP_FILE_DOMAIN}/x.mp4"
    )
    out = extract_urls_from_html(html)
    assert out == [(f"https://{UTP_FILE_DOMAIN}/x.mp4", "mp4")]


def test_extract_empty_html():
    assert extract_urls_from_html("") == []
    assert extract_urls_from_html(None) == []


def test_skip_existing_zero_byte_redownloads(tmp_path, monkeypatch):
    p = tmp_path / "f.pdf"
    p.write_bytes(b"")  # corrupta por una descarga previa: size 0

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def raise_for_status(self):
            pass

        def iter_content(self, *a, **k):
            return iter([b"contenido"])

    monkeypatch.setattr(
        "utp_scraper.downloader.requests.get", lambda *a, **k: FakeResp()
    )
    result, name = download_file(
        S3_URL_PDF.replace("/a/b.pdf", "/f.pdf"), "pdf", str(tmp_path), "f"
    )
    assert result == "ok"
    assert p.stat().st_size > 0


def test_skip_existing_nonempty(tmp_path):
    p = tmp_path / "f.pdf"
    p.write_bytes(b"x")
    result, _ = download_file(
        S3_URL_PDF.replace("/a/b.pdf", "/f.pdf"), "pdf", str(tmp_path), "f"
    )
    assert result == "skip_exist"
