"""Runtime configuration.

Everything private (experience memory, your own knowledge files, outputs)
lives under IMPROVISE_HOME (default: ~/.improvise), which is outside the
repository and is never pushed to GitHub.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default=None):
    """IMPROVISE_* settings; the old FACTORY_AI_* names still work."""
    return os.environ.get(f"IMPROVISE_{name}", os.environ.get(f"FACTORY_AI_{name}", default))


def _default_key() -> str:
    """API key from IMPROVISE_API_KEY, else the provider's usual variable. Never stored in files."""
    key = _env("API_KEY", "")
    if key:
        return key
    provider = str(_env("PROVIDER", "ollama")).lower()
    return os.environ.get("ANTHROPIC_API_KEY", "") if provider == "anthropic" else os.environ.get("OPENAI_API_KEY", "")


def _home() -> Path:
    explicit = _env("HOME")
    if explicit:
        return Path(explicit)
    new, old = Path.home() / ".improvise", Path.home() / ".factory-ai"
    if not new.exists() and old.exists():
        try:
            old.rename(new)  # carry experience over from the factory-ai name
        except OSError:
            return old
    return new


@dataclass
class Config:
    home: Path = field(default_factory=_home)
    ollama_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_URL", "http://localhost:11434"))
    model: str = field(default_factory=lambda: _env("MODEL", "qwen2.5:14b"))
    provider: str = field(default_factory=lambda: _env("PROVIDER", "ollama"))
    api_base: str = field(default_factory=lambda: _env("API_BASE", ""))
    api_key: str = field(default_factory=lambda: _default_key())
    # optional second "brain" the local model can consult (ask_expert)
    expert_provider: str = field(default_factory=lambda: _env("EXPERT_PROVIDER", ""))
    expert_model: str = field(default_factory=lambda: _env("EXPERT_MODEL", ""))
    expert_api_base: str = field(default_factory=lambda: _env("EXPERT_API_BASE", ""))
    expert_api_key: str = field(default_factory=lambda: _env("EXPERT_API_KEY", ""))
    temperature: float = 0.2
    think: bool = field(default_factory=lambda: str(_env("THINK", "0")).lower() in ("1", "true", "yes"))
    max_tool_rounds: int = 8
    number_audit: bool = field(default_factory=lambda: str(_env("NUMBER_AUDIT", "1")) not in ("0", "false", "no"))
    num_ctx: int = field(default_factory=lambda: int(_env("NUM_CTX", "8192")))
    max_tools: int = field(default_factory=lambda: int(_env("MAX_TOOLS", "10")))

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
