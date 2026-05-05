import json
from dataclasses import dataclass, asdict
from pathlib import Path

from livesttt import logging as log_module

CONFIG_PATH = Path.home() / ".livesttt" / "config.json"

logger = log_module.logger


@dataclass
class Config:
    hotkey: str = "ctrl+shift+space"
    cancel_hotkey: str = "escape"
    model: str = "gemma4"
    refine: bool = True
    vad_threshold: float = 0.02
    stt_timeout: int = 60
    llm_timeout: int = 30
    injection_delay: float = 0.05


def _validate_value(key: str, value, default):
    if key in ("hotkey", "cancel_hotkey"):
        if not isinstance(value, str) or not value.strip():
            logger.warning(f"Invalid {key}: {value!r}, using default {default!r}")
            return default
    elif key == "model":
        if not isinstance(value, str) or not value.strip():
            logger.warning(f"Invalid model: {value!r}, using default {default!r}")
            return default
    elif key == "refine":
        if not isinstance(value, bool):
            logger.warning(f"Invalid refine: {value!r}, using default {default!r}")
            return default
    elif key == "vad_threshold":
        if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
            logger.warning(f"Invalid vad_threshold: {value!r}, using default {default!r}")
            return default
    elif key in ("stt_timeout", "llm_timeout"):
        if not isinstance(value, int) or value <= 0:
            logger.warning(f"Invalid {key}: {value!r}, using default {default!r}")
            return default
    elif key == "injection_delay":
        if not isinstance(value, (int, float)) or value < 0:
            logger.warning(f"Invalid {key}: {value!r}, using default {default!r}")
            return default
    return value


def _validate(data: dict) -> Config:
    defaults = Config()
    defaults_dict = asdict(defaults)

    validated = {}
    for key, default in defaults_dict.items():
        validated[key] = _validate_value(key, data.get(key), default)

    return Config(**validated)


def load() -> Config:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return _validate(data)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(f"Config load failed: {e}, using defaults")
    return Config()


def save(cfg: Config) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
