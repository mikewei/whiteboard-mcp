"""User-level UI config under ~/.whiteboard-mcp/config.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

import yaml

Language = Literal["en", "zh"]

_ALLOWED: frozenset[str] = frozenset({"en", "zh"})


def config_path() -> Path:
    return (Path.home() / ".whiteboard-mcp" / "config.yaml").resolve()


def file_language_if_set() -> Language | None:
    """Return en/zh only when `language` is explicitly set and valid in config.yaml."""
    path = config_path()
    if not path.is_file():
        return None
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        v = raw.get("language")
        if not isinstance(v, str):
            return None
        cand = v.strip().lower()
        if cand in _ALLOWED:
            return cast(Language, cand)
    except (yaml.YAMLError, OSError, TypeError):
        return None
    return None


def language_from_accept_language(header: str | None) -> Language:
    """Use the browser's top-weighted language tag: zh* → zh, otherwise en."""
    if not header or not header.strip():
        return cast(Language, "en")
    scored: list[tuple[float, int, str]] = []
    for idx, part in enumerate(header.split(",")):
        part = part.strip()
        if not part:
            continue
        if ";" in part:
            langtag, rest = part.split(";", 1)
            langtag = langtag.strip()
            q = 1.0
            for sub in rest.split(";"):
                sub = sub.strip()
                if sub.lower().startswith("q="):
                    try:
                        q = float(sub[2:].strip())
                    except ValueError:
                        q = 0.0
                    break
        else:
            langtag = part.strip()
            q = 1.0
        primary = langtag.lower().split("-")[0].split("_")[0]
        if primary:
            scored.append((q, idx, primary))
    if not scored:
        return cast(Language, "en")
    scored.sort(key=lambda t: (-t[0], t[1]))
    _q, _idx, first_primary = scored[0]
    if first_primary.startswith("zh"):
        return cast(Language, "zh")
    return cast(Language, "en")


def resolve_ui_language(accept_language_header: str | None) -> Language:
    """Explicit config wins; else Accept-Language (zh → zh); else en."""
    f = file_language_if_set()
    if f is not None:
        return f
    return language_from_accept_language(accept_language_header)


def set_language(lang: str) -> None:
    if lang not in _ALLOWED:
        raise ValueError("invalid language")
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {}
    if path.is_file():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = dict(loaded)
        except (yaml.YAMLError, OSError, TypeError):
            data = {}
    data["language"] = lang
    tmp = path.with_suffix(".yaml.tmp")
    tmp.write_text(
        yaml.safe_dump(
            data,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    tmp.replace(path)
