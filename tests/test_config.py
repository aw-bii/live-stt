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


def test_default_cancel_hotkey():
    cfg = config.Config()
    assert cfg.cancel_hotkey == "escape"


def test_cancel_hotkey_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    cfg = config.Config(cancel_hotkey="ctrl+z")
    config.save(cfg)
    loaded = config.load()
    assert loaded.cancel_hotkey == "ctrl+z"


def test_load_invalid_hotkey_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text('{"hotkey": ""}')
    loaded = config.load()
    assert loaded.hotkey == "ctrl+shift+space"


def test_load_invalid_vad_threshold_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text('{"vad_threshold": 2.0}')
    loaded = config.load()
    assert loaded.vad_threshold == 0.02


def test_load_invalid_vad_threshold_negative(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text('{"vad_threshold": -0.5}')
    loaded = config.load()
    assert loaded.vad_threshold == 0.02


def test_load_invalid_refine_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text('{"refine": "yes"}')
    loaded = config.load()
    assert loaded.refine is True


def test_load_invalid_json_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text("not valid json")
    loaded = config.load()
    assert loaded == config.Config()


def test_load_partial_valid_data(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text('{"hotkey": "ctrl+b"}')
    loaded = config.load()
    assert loaded.hotkey == "ctrl+b"
    assert loaded.model == "gemma4"
