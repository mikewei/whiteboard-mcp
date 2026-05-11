"""Tests for content-addressed history persistence."""

from __future__ import annotations

import json
import time

import pytest

from whiteboard_mcp import history_store


def test_content_hash_stable() -> None:
    h1 = history_store.content_hash("html", "<p>a</p>")
    h2 = history_store.content_hash("html", "<p>a</p>")
    assert h1 == h2
    assert h1 != history_store.content_hash("url", "<p>a</p>")


def test_upsert_html_writes_file_and_history(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    body = "<article>hello</article>"
    key = history_store.upsert_record(content_type="html", content=body)
    assert len(key) == 64
    root = history_store.get_store_root()
    html_path = root / "files" / f"{key}.html"
    assert html_path.read_text(encoding="utf-8") == body
    data = json.loads((root / "history.json").read_text(encoding="utf-8"))
    assert key in data["entries"]
    assert data["entries"][key]["type"] == "html"
    assert "preview" in data["entries"][key]


def test_upsert_url_record(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    url = "https://example.com/page"
    key = history_store.upsert_record(content_type="url", content=url)
    root = history_store.get_store_root()
    data = json.loads((root / "history.json").read_text(encoding="utf-8"))
    assert data["entries"][key]["url"] == url
    assert data["entries"][key]["type"] == "url"


def test_upsert_same_content_same_key_updates_timestamp(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    html = "<p>x</p>"
    k1 = history_store.upsert_record(content_type="html", content=html)
    time.sleep(0.02)
    k2 = history_store.upsert_record(content_type="html", content=html)
    assert k1 == k2
    rows = history_store.list_records_newest_first()
    assert len(rows) == 1


def test_list_records_newest_first(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    history_store.upsert_record(content_type="html", content="<p>old</p>")
    time.sleep(0.02)
    history_store.upsert_record(content_type="url", content="https://new.example/")
    rows = history_store.list_records_newest_first()
    assert len(rows) == 2
    assert rows[0]["type"] == "url"
    assert rows[1]["type"] == "html"


def test_resolve_restore_payload_html(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    html = "<div>restore me</div>"
    key = history_store.upsert_record(content_type="html", content=html)
    assert history_store.resolve_restore_payload(key) == ("html", html)


def test_resolve_restore_payload_url(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    url = "https://example.com/x"
    key = history_store.upsert_record(content_type="url", content=url)
    assert history_store.resolve_restore_payload(key) == ("url", url)


def test_resolve_restore_payload_unknown_id(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    assert history_store.resolve_restore_payload("0" * 64) is None


def test_resolve_restore_payload_missing_html_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    key = history_store.upsert_record(content_type="html", content="<p>x</p>")
    root = history_store.get_store_root()
    rel = history_store.find_record(key)["html_file"]
    (root / rel).unlink()
    assert history_store.resolve_restore_payload(key) is None


def test_html_file_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    html = "<p>f</p>"
    key = history_store.upsert_record(content_type="html", content=html)
    path = history_store.html_file_path(key)
    assert path is not None
    assert path.read_text(encoding="utf-8") == html


def test_html_file_path_url_record(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    key = history_store.upsert_record(content_type="url", content="https://a.test/")
    assert history_store.html_file_path(key) is None


def test_upsert_unknown_type_raises(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(tmp_path / "store"))
    with pytest.raises(ValueError, match="unknown content type"):
        history_store.upsert_record(content_type="image", content="x")
