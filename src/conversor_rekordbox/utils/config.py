from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

DEFAULT_PATH = Path.home() / ".conversor_audio" / "config.json"
DEFAULT_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class AppConfig:
    output_dir: str | None = None
    use_source_dir: bool = True
    last_format: str = "mp3"

    @classmethod
    def load(cls, path: Path = DEFAULT_PATH) -> "AppConfig":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)

    def save(self, path: Path = DEFAULT_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
