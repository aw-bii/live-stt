import json
from dataclasses import dataclass, asdict
from pathlib import Path

CONFIG_PATH = Path.home() / ".livesttt" / "config.json"


@dataclass
class Config:
    hotkey: str = "ctrl+shift+space"
    model: str = "gemma4"
    refine: bool = True
    vad_threshold: float = 0.02


def load() -> Config:
    if CONFIG_PATH.exists():
        return Config(**json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    return Config()


def save(cfg: Config) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
