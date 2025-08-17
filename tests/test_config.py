import sys
import types
from pathlib import Path

import pytest

# Provide a minimal stub for the yaml module to avoid external dependency
yaml_stub = types.SimpleNamespace(
    safe_load=lambda stream: {},
    dump=lambda data, stream, default_flow_style=False, indent=2: None,
)
sys.modules.setdefault("yaml", yaml_stub)

# Ensure the module path is discoverable
sys.path.append(str(Path(__file__).resolve().parents[1] / "usr/lib/ai-terminal-assistant"))

from config import ConfigManager


def test_deep_merge(tmp_path, monkeypatch):
    """ConfigManager deep merge should recursively update dictionaries."""
    monkeypatch.setattr(ConfigManager, "USER_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(ConfigManager, "USER_CONFIG_PATH", tmp_path / "config.yaml")
    cm = ConfigManager()

    base = {"a": {"b": 1, "c": 2}, "d": 4}
    override = {"a": {"b": 3}, "e": 5}

    cm._deep_merge(base, override)
    assert base == {"a": {"b": 3, "c": 2}, "d": 4, "e": 5}


def test_is_configured(tmp_path, monkeypatch):
    """is_configured should reflect presence of stored API key."""
    monkeypatch.setattr(ConfigManager, "USER_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(ConfigManager, "USER_CONFIG_PATH", tmp_path / "config.yaml")
    cm = ConfigManager()

    assert cm.is_configured() is False

    cm._store_api_key("sk-test")
    assert cm.is_configured() is True
