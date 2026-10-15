"""Runtime configuration.

Everything private (experience memory, your own knowledge files, outputs)
lives under FACTORY_AI_HOME (default: ~/.factory-ai), which is outside the
repository and is never pushed to GitHub.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _home() -> Path:
    return Path(os.environ.get("FACTORY_AI_HOME", Path.home() / ".factory-ai"))


@dataclass
class Config:
    home: Path = field(default_factory=_home)
    ollama_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_URL", "http://localhost:11434"))
    model: str = field(default_factory=lambda: os.environ.get("FACTORY_AI_MODEL", "qwen2.5:14b"))
    temperature: float = 0.2
    max_tool_rounds: int = 8

    @property
    def db_path(self) -> Path:
        return self.home / "experience.db"

    @property
    def user_knowledge_dir(self) -> Path:
        return self.home / "knowledge"

    @property
    def output_dir(self) -> Path:
        return self.home / "output"

    def ensure_dirs(self) -> None:
        for p in (self.home, self.user_knowledge_dir, self.output_dir):
            p.mkdir(parents=True, exist_ok=True)


def load() -> Config:
    cfg = Config()
    cfg.ensure_dirs()
    return cfg
