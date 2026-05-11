"""Tests for ~/.whiteboard-mcp/config.yaml language helpers."""

from __future__ import annotations

import pytest

from whiteboard_mcp import user_config


def test_language_from_accept_language_empty() -> None:
    assert user_config.language_from_accept_language(None) == "en"
    assert user_config.language_from_accept_language("") == "en"


def test_language_from_accept_language_zh() -> None:
    assert user_config.language_from_accept_language("zh-CN,en;q=0.8") == "zh"
    assert user_config.language_from_accept_language("zh-TW") == "zh"


def test_language_from_accept_language_q_weights() -> None:
    header = "en;q=0.5, zh;q=0.8"
    assert user_config.language_from_accept_language(header) == "zh"


def test_resolve_ui_language_prefers_file_over_header(tmp_path, monkeypatch) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("language: zh\n", encoding="utf-8")

    def _path():
        return cfg

    monkeypatch.setattr(user_config, "config_path", _path)
    assert user_config.resolve_ui_language("en-US,en;q=0.9") == "zh"


def test_resolve_ui_language_no_file_uses_header(tmp_path, monkeypatch) -> None:
    def _path():
        return tmp_path / "missing.yaml"

    monkeypatch.setattr(user_config, "config_path", _path)
    assert user_config.resolve_ui_language("zh-CN") == "zh"
    assert user_config.resolve_ui_language("en-GB") == "en"


def test_set_language_roundtrip(tmp_path, monkeypatch) -> None:
    def _path():
        return tmp_path / "config.yaml"

    monkeypatch.setattr(user_config, "config_path", _path)
    user_config.set_language("en")
    assert user_config.file_language_if_set() == "en"
    user_config.set_language("zh")
    assert user_config.file_language_if_set() == "zh"


def test_set_language_invalid() -> None:
    with pytest.raises(ValueError):
        user_config.set_language("fr")
