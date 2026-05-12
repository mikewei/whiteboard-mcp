"""HTTP API integration tests (FastAPI TestClient)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from whiteboard_mcp import history_store
from whiteboard_mcp import user_config
from whiteboard_mcp.app import app


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    # FastMCP session_manager.run() must not be entered twice on the same app instance.
    with TestClient(app) as c:
        yield c


def test_get_content_default(client: TestClient) -> None:
    r = client.get("/api/content")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "html"
    assert "Welcome" in data["content"]
    assert data["history_id"] == history_store.content_hash(data["type"], data["content"])


def test_post_and_get_content_html(client: TestClient) -> None:
    body = {"type": "html", "content": "<p>api test</p>"}
    pr = client.post("/api/content", json=body)
    assert pr.status_code == 200
    gr = client.get("/api/content")
    payload = gr.json()
    assert payload["content"] == "<p>api test</p>"
    assert payload["type"] == "html"
    assert payload["history_id"] == history_store.content_hash("html", "<p>api test</p>")


def test_post_and_get_content_markdown(client: TestClient) -> None:
    body = {"type": "markdown", "content": "# Title\n"}
    pr = client.post("/api/content", json=body)
    assert pr.status_code == 200
    gr = client.get("/api/content")
    assert gr.json()["content"] == "# Title\n"
    assert gr.json()["type"] == "markdown"


def test_post_content_invalid_type(client: TestClient) -> None:
    r = client.post("/api/content", json={"type": "image", "content": "x"})
    assert r.status_code == 422


def test_history_list_after_updates(client: TestClient) -> None:
    client.post("/api/content", json={"type": "html", "content": "<span>h1</span>"})
    client.post("/api/content", json={"type": "url", "content": "https://hist.example/p"})
    r = client.get("/api/history")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 2
    types = {row["type"] for row in rows}
    assert "html" in types and "url" in types
    url_rows = [x for x in rows if x["type"] == "url"]
    assert url_rows[0].get("url") == "https://hist.example/p"


def test_history_restore_markdown(client: TestClient) -> None:
    client.post("/api/content", json={"type": "markdown", "content": "# A"})
    client.post("/api/content", json={"type": "markdown", "content": "# B"})
    rows = client.get("/api/history").json()
    md_rows = sorted(
        [x for x in rows if x["type"] == "markdown"],
        key=lambda x: x["updated_at"],
    )
    first_row, last_row = md_rows[0], md_rows[-1]
    rr = client.post(f"/api/history/{first_row['id']}/restore")
    assert rr.status_code == 200
    cur = client.get("/api/content").json()
    assert cur["content"] == "# A"
    assert cur["type"] == "markdown"


def test_history_restore_and_get_content(client: TestClient) -> None:
    client.post("/api/content", json={"type": "html", "content": "<p>before</p>"})
    client.post("/api/content", json={"type": "html", "content": "<p>after</p>"})
    rows = client.get("/api/history").json()
    html_rows = sorted(
        [x for x in rows if x["type"] == "html"],
        key=lambda x: x["updated_at"],
    )
    before_row, after_row = html_rows[0], html_rows[-1]
    assert before_row["id"] != after_row["id"]
    rr = client.post(f"/api/history/{before_row['id']}/restore")
    assert rr.status_code == 200
    cur = client.get("/api/content").json()
    assert cur["content"] == "<p>before</p>"


def test_history_restore_404_zh_detail(client: TestClient) -> None:
    r = client.post(
        "/api/history/" + "a" * 64 + "/restore",
        headers={"Accept-Language": "zh-CN,zh;q=0.9"},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "记录不存在或文件缺失"


def test_history_raw_html_ok(client: TestClient) -> None:
    html = "<main>raw</main>"
    client.post("/api/content", json={"type": "html", "content": html})
    hid = client.get("/api/history").json()[0]["id"]
    r = client.get(f"/api/history/{hid}/html")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert r.text == html


def test_history_raw_html_404_for_url_record(client: TestClient) -> None:
    client.post("/api/content", json={"type": "url", "content": "https://only.url/"})
    hid = client.get("/api/history").json()[0]["id"]
    r = client.get(f"/api/history/{hid}/html")
    assert r.status_code == 404


def test_history_raw_md_ok(client: TestClient) -> None:
    md = "# raw md\n"
    client.post("/api/content", json={"type": "markdown", "content": md})
    hid = client.get("/api/history").json()[0]["id"]
    r = client.get(f"/api/history/{hid}/md")
    assert r.status_code == 200
    assert "markdown" in r.headers.get("content-type", "")
    assert r.text == md


def test_history_raw_md_404_for_html_record(client: TestClient) -> None:
    client.post("/api/content", json={"type": "html", "content": "<p>x</p>"})
    hid = client.get("/api/history").json()[0]["id"]
    r = client.get(f"/api/history/{hid}/md")
    assert r.status_code == 404


def test_history_delete_ok(client: TestClient) -> None:
    client.post("/api/content", json={"type": "html", "content": "<p>api-delete-test</p>"})
    rows = client.get("/api/history").json()
    html_rows = [x for x in rows if x["type"] == "html"]
    assert html_rows
    hid = html_rows[0]["id"]
    dr = client.delete(f"/api/history/{hid}")
    assert dr.status_code == 200
    assert dr.json() == {"ok": True}
    rows2 = client.get("/api/history").json()
    assert all(r["id"] != hid for r in rows2)


def test_history_delete_404_zh_detail(client: TestClient) -> None:
    r = client.delete(
        "/api/history/" + "c" * 64,
        headers={"Accept-Language": "zh-CN,zh;q=0.9"},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "记录不存在或文件缺失"


def test_ui_config_valid(client: TestClient) -> None:
    assert client.post("/api/ui-config", json={"language": "en"}).json() == {"ok": True}
    assert client.post("/api/ui-config", json={"language": "zh"}).json() == {"ok": True}


def test_ui_config_invalid_language(client: TestClient) -> None:
    # Pydantic rejects values outside Literal before the route handler runs.
    r = client.post("/api/ui-config", json={"language": "de"})
    assert r.status_code == 422


def test_index_english_strings(client: TestClient) -> None:
    r = client.get("/", headers={"Accept-Language": "en-US"})
    assert r.status_code == 200
    assert "Whiteboard" in r.text


def test_index_chinese_accept_language(client: TestClient) -> None:
    r = client.get("/", headers={"Accept-Language": "zh-CN"})
    assert r.status_code == 200
    assert "白板服务" in r.text


def test_index_respects_saved_config_language(client: TestClient, monkeypatch) -> None:
    user_config.set_language("zh")
    r = client.get("/", headers={"Accept-Language": "en-GB"})
    assert r.status_code == 200
    assert "白板服务" in r.text


def test_openapi_lists_events_route() -> None:
    """SSE body schema is not modeled in OpenAPI; still expose the GET route."""
    spec = app.openapi()
    assert "/api/events" in spec["paths"]
    assert "get" in spec["paths"]["/api/events"]
