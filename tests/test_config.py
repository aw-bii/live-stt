import json
from pathlib import Path
import pytest
from livesttt import config


def test_defaults():
    cfg = config.Config()
    assert cfg.hotkey == "ctrl+shift+space"
    assert cfg.model == "gemma4"
    assert cfg.refine is True
    assert cfg.vad_threshold == 0.02


def test_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    cfg = config.Config(hotkey="ctrl+r", model="gemma4", refine=False, vad_threshold=0.05)
    config.save(cfg)
    loaded = config.load()
    assert loaded.hotkey == "ctrl+r"
    assert loaded.refine is False
    assert loaded.vad_threshold == 0.05


def test_load_missing_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "nonexistent.json")
    cfg = config.load()
    assert cfg == config.Config()


def test_save_creates_parent_dir(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "dir" / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", target)
    config.save(config.Config())
    assert target.exists()
