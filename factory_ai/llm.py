"""Minimal client for a local Ollama server (no extra dependencies).

Any model that supports tool calling in Ollama works (e.g. Qwen, Llama,
Mistral families). Set FACTORY_AI_MODEL to choose one.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class LLMError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, model: str, temperature: float = 0.2, timeout: int = 600):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if tools:
            payload["tools"] = tools
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read())
        except urllib.error.URLError as e:
            raise LLMError(
                f"Cannot reach Ollama at {self.base_url}. Is it running? "
                f"Install from https://ollama.com and run: ollama pull {self.model}"
            ) from e
        return data.get("message", {})
