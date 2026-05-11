"""Pytest fixtures: isolate filesystem side effects from the real home and package tree."""

from __future__ import annotations

import pytest

import whiteboard_mcp.app as app_module
import whiteboard_mcp.user_config as user_config


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Per-test temp store, content file, and UI config path."""
    store = tmp_path / "store"
    monkeypatch.setenv("WHITEBOARD_STORE_DIR", str(store))
    monkeypatch.setattr(app_module, "CONTENT_FILE", tmp_path / "whiteboard_content.json")

    cfg = tmp_path / "config.yaml"

    def _config_path():
        return cfg

    monkeypatch.setattr(user_config, "config_path", _config_path)
