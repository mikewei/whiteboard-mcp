"""Tests for UI string tables."""

from __future__ import annotations

from whiteboard_mcp.ui_i18n import api_detail, ui_strings_for


def test_ui_strings_for_en_and_zh() -> None:
    en = ui_strings_for("en")
    zh = ui_strings_for("zh")
    assert en["title"] == "Whiteboard"
    assert zh["title"] == "白板服务"
    assert set(en.keys()) == set(zh.keys())


def test_api_detail_localized() -> None:
    assert api_detail("en", "history_not_found") == "Record not found or file missing."
    assert api_detail("zh", "history_not_found") == "记录不存在或文件缺失"
