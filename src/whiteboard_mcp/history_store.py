"""Persist cast history under a configurable store directory."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def get_store_root() -> Path:
    raw = os.environ.get("WHITEBOARD_STORE_DIR")
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / ".whiteboard-mcp" / "store").resolve()


def content_hash(content_type: str, content: str) -> str:
    """SHA256 hex of type + NUL + content for stable dedupe keys."""
    h = hashlib.sha256()
    h.update(content_type.encode("utf-8"))
    h.update(b"\0")
    h.update(content.encode("utf-8"))
    return h.hexdigest()


def _preview_html(html: str, max_len: int = 120) -> str:
    text = _HTML_TAG_RE.sub(" ", html)
    text = " ".join(text.split())
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text or "(HTML)"


def _preview_markdown(md: str, max_len: int = 120) -> str:
    line = md.strip().split("\n", 1)[0].strip()
    line = line.lstrip("#").strip() or line
    if len(line) > max_len:
        return line[: max_len - 1] + "…"
    return line or "(Markdown)"


def _history_json_path(root: Path) -> Path:
    return root / "history.json"


def _history_jsonl_path(root: Path) -> Path:
    return root / "history.jsonl"


def _migrate_jsonl_if_needed(root: Path) -> dict[str, dict[str, Any]]:
    """Import legacy history.jsonl into hash-keyed entries (best-effort)."""
    jsonl = _history_jsonl_path(root)
    if not jsonl.is_file():
        return {}
    entries: dict[str, dict[str, Any]] = {}
    with open(jsonl, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = rec.get("type")
            ts = rec.get("created_at") or datetime.now().isoformat()
            prev = rec.get("preview") or ""
            if t == "url":
                url = rec.get("url")
                if not isinstance(url, str):
                    continue
                key = content_hash("url", url)
                cur = entries.get(key)
                if cur and (cur.get("updated_at") or "") >= ts:
                    continue
                preview = url if len(url) <= 120 else url[:119] + "…"
                entries[key] = {
                    "type": "url",
                    "updated_at": ts,
                    "preview": preview,
                    "url": url,
                }
            elif t == "html":
                rel = rec.get("html_file")
                if not isinstance(rel, str):
                    continue
                path = root / rel
                if not path.is_file():
                    continue
                body = path.read_text(encoding="utf-8")
                key = content_hash("html", body)
                cur = entries.get(key)
                if cur and (cur.get("updated_at") or "") >= ts:
                    continue
                html_name = f"{key}.html"
                new_rel = f"files/{html_name}"
                new_path = root / new_rel
                new_path.parent.mkdir(parents=True, exist_ok=True)
                if path.resolve() != new_path.resolve():
                    new_path.write_text(body, encoding="utf-8")
                entries[key] = {
                    "type": "html",
                    "updated_at": ts,
                    "preview": rec.get("preview") or _preview_html(body),
                    "html_file": new_rel,
                }
    try:
        jsonl.rename(jsonl.with_suffix(".jsonl.bak"))
    except OSError:
        pass
    return entries


def _load_entries_raw(root: Path) -> dict[str, dict[str, Any]]:
    path = _history_json_path(root)
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            raw = data.get("entries")
            if isinstance(raw, dict):
                return dict(raw)
        except (json.JSONDecodeError, OSError):
            pass
    migrated = _migrate_jsonl_if_needed(root)
    if migrated:
        _save_entries(root, migrated)
    return migrated


def _save_entries(root: Path, entries: dict[str, dict[str, Any]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    path = _history_json_path(root)
    tmp = root / "history.json.tmp"
    payload = {"entries": entries}
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def upsert_record(*, content_type: str, content: str) -> str:
    """
    Content-addressed history: one row per distinct (type, content).
    HTML files are named {sha256}.html. Repeated content only bumps updated_at.
    Returns content hash (used as record id in APIs).
    """
    root = get_store_root()
    key = content_hash(content_type, content)
    entries = _load_entries_raw(root)

    now = datetime.now().isoformat()
    if content_type == "html":
        files_dir = root / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        html_name = f"{key}.html"
        rel = f"files/{html_name}"
        path = root / rel
        path.write_text(content, encoding="utf-8")
        preview = _preview_html(content)
        entries[key] = {
            "type": "html",
            "updated_at": now,
            "preview": preview,
            "html_file": rel,
        }
    elif content_type == "markdown":
        files_dir = root / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        md_name = f"{key}.md"
        rel = f"files/{md_name}"
        path = root / rel
        path.write_text(content, encoding="utf-8")
        preview = _preview_markdown(content)
        entries[key] = {
            "type": "markdown",
            "updated_at": now,
            "preview": preview,
            "md_file": rel,
        }
    elif content_type == "url":
        preview = content if len(content) <= 120 else content[:119] + "…"
        entries[key] = {
            "type": "url",
            "updated_at": now,
            "preview": preview,
            "url": content,
        }
    else:
        raise ValueError(f"unknown content type: {content_type}")

    _save_entries(root, entries)
    return key


def list_records_newest_first() -> list[dict[str, Any]]:
    root = get_store_root()
    entries = _load_entries_raw(root)
    rows = []
    for hid, rec in entries.items():
        row = {"id": hid, **rec}
        rows.append(row)
    rows.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
    return rows


def find_record(record_id: str) -> dict[str, Any] | None:
    root = get_store_root()
    entries = _load_entries_raw(root)
    rec = entries.get(record_id)
    if rec is None:
        return None
    return {"id": record_id, **rec}


def resolve_restore_payload(record_id: str) -> tuple[str, str] | None:
    """Returns (type, content) for ContentUpdate, or None if missing."""
    rec = find_record(record_id)
    if not rec:
        return None
    t = rec.get("type")
    if t == "url":
        url = rec.get("url")
        if not isinstance(url, str):
            return None
        return ("url", url)
    if t == "html":
        rel = rec.get("html_file")
        if not isinstance(rel, str):
            return None
        path = get_store_root() / rel
        if not path.is_file():
            return None
        return ("html", path.read_text(encoding="utf-8"))
    if t == "markdown":
        rel = rec.get("md_file")
        if not isinstance(rel, str):
            return None
        path = get_store_root() / rel
        if not path.is_file():
            return None
        return ("markdown", path.read_text(encoding="utf-8"))
    return None


def html_file_path(record_id: str) -> Path | None:
    """Absolute path to stored HTML file for this hash id, if any."""
    rec = find_record(record_id)
    if not rec or rec.get("type") != "html":
        return None
    rel = rec.get("html_file")
    if not isinstance(rel, str):
        return None
    path = get_store_root() / rel
    return path if path.is_file() else None


def delete_record(record_id: str) -> bool:
    """Remove one history entry and delete stored HTML or Markdown file if applicable."""
    root = get_store_root()
    entries = _load_entries_raw(root)
    rec = entries.pop(record_id, None)
    if rec is None:
        return False
    file_rel: str | None = None
    if rec.get("type") == "html":
        rel = rec.get("html_file")
        if isinstance(rel, str):
            file_rel = rel
    elif rec.get("type") == "markdown":
        rel = rec.get("md_file")
        if isinstance(rel, str):
            file_rel = rel
    _save_entries(root, entries)
    if file_rel:
        path = root / file_rel
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    return True


def md_file_path(record_id: str) -> Path | None:
    """Absolute path to stored Markdown file for this hash id, if any."""
    rec = find_record(record_id)
    if not rec or rec.get("type") != "markdown":
        return None
    rel = rec.get("md_file")
    if not isinstance(rel, str):
        return None
    path = get_store_root() / rel
    return path if path.is_file() else None
