"""Minimal client for a local Ollama server (no extra dependencies).

Any model that supports tool calling in Ollama works (e.g. Qwen, Llama,
Mistral families). Set IMPROVISE_MODEL to choose one.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class LLMError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, model: str, temperature: float = 0.2, timeout: int = 600,
                 think: bool = False, num_ctx: int = 8192):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        # Thinking models (e.g. Qwen3) answer far faster with thinking off; tools still do the maths.
        self.think: bool | None = think
        # Ollama's default context (4096) silently cuts the start of long prompts - the instructions.
        self.num_ctx = num_ctx

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx},
        }
        if tools:
            payload["tools"] = tools
        if self.think is not None:
            payload["think"] = self.think
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            if self.think is not None and e.code == 400:  # model without a thinking switch
                self.think = None
                return self.chat(messages, tools)
            raise LLMError(f"Ollama error {e.code}: {e.read()[:300]!r}") from e
        except urllib.error.URLError as e:
            raise LLMError(
                f"Cannot reach Ollama at {self.base_url}. Is it running? "
                f"Install from https://ollama.com and run: ollama pull {self.model}"
            ) from e
        return data.get("message", {})
