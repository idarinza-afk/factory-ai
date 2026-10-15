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
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx, "num_predict": 2048},
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


def _post(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise LLMError(f"API error {e.code} from {url}: {e.read()[:400]!r}") from e
    except urllib.error.URLError as e:
        raise LLMError(f"Cannot reach {url}: {e}") from e


class OpenAICompatClient:
    """Any OpenAI-compatible chat API: OpenAI, Azure-style gateways, OpenRouter, Groq, DeepSeek,
    LM Studio, vLLM, llama.cpp server... Set IMPROVISE_API_BASE and IMPROVISE_API_KEY."""

    def __init__(self, base_url: str, model: str, api_key: str = "", temperature: float = 0.2, timeout: int = 600):
        self.base_url = base_url.rstrip("/")
        self.model, self.api_key, self.temperature, self.timeout = model, api_key, temperature, timeout

    @staticmethod
    def _to_openai(messages: list[dict]) -> list[dict]:
        out = []
        for m in messages:
            m = dict(m)
            if m.get("tool_calls"):
                m["tool_calls"] = [{"id": c.get("id", f"call_{i}"), "type": "function",
                                    "function": {"name": c["function"]["name"],
                                                 "arguments": c["function"]["arguments"] if isinstance(c["function"]["arguments"], str)
                                                 else json.dumps(c["function"]["arguments"], ensure_ascii=False)}}
                                   for i, c in enumerate(m["tool_calls"])]
                m.setdefault("content", "")
            out.append({k: v for k, v in m.items() if k in ("role", "content", "tool_calls", "tool_call_id")})
        return out

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": self.model, "messages": self._to_openai(messages),
                                   "temperature": self.temperature}
        if tools:
            payload["tools"] = tools
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        data = _post(f"{self.base_url}/chat/completions", payload, headers, self.timeout)
        msg = data["choices"][0]["message"]
        calls = []
        for c in msg.get("tool_calls") or []:
            args = c["function"].get("arguments") or "{}"
            try:
                args = json.loads(args) if isinstance(args, str) else args
            except json.JSONDecodeError:
                args = {}
            calls.append({"id": c.get("id"), "function": {"name": c["function"]["name"], "arguments": args}})
        out = {"role": "assistant", "content": msg.get("content") or ""}
        if calls:
            out["tool_calls"] = calls
        return out


class AnthropicClient:
    """Claude via the Anthropic Messages API. Set IMPROVISE_API_KEY (or ANTHROPIC_API_KEY)."""

    def __init__(self, model: str, api_key: str, base_url: str = "https://api.anthropic.com", temperature: float = 0.2,
                 timeout: int = 600, max_tokens: int = 4096):
        self.model, self.api_key, self.base_url = model, api_key, base_url.rstrip("/")
        self.temperature, self.timeout, self.max_tokens = temperature, timeout, max_tokens

    @staticmethod
    def _convert(messages: list[dict]) -> tuple[str, list[dict]]:
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        out: list[dict] = []
        for m in messages:
            role = m["role"]
            if role == "system":
                continue
            if role == "tool":
                block = {"type": "tool_result", "tool_use_id": m.get("tool_call_id", "call_0"), "content": m.get("content", "")}
                if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list) \
                        and out[-1]["content"] and out[-1]["content"][0].get("type") == "tool_result":
                    out[-1]["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
            elif role == "assistant":
                blocks = [{"type": "text", "text": m["content"]}] if m.get("content") else []
                for i, c in enumerate(m.get("tool_calls") or []):
                    args = c["function"]["arguments"]
                    blocks.append({"type": "tool_use", "id": c.get("id") or f"call_{i}", "name": c["function"]["name"],
                                   "input": args if isinstance(args, dict) else json.loads(args or "{}")})
                out.append({"role": "assistant", "content": blocks or [{"type": "text", "text": "."}]})
            else:
                out.append({"role": "user", "content": m.get("content", "")})
        return system, out

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict[str, Any]:
        system, msgs = self._convert(messages)
        payload: dict[str, Any] = {"model": self.model, "max_tokens": self.max_tokens, "messages": msgs,
                                   "temperature": self.temperature}
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = [{"name": t["function"]["name"], "description": t["function"]["description"],
                                 "input_schema": t["function"]["parameters"]} for t in tools]
        data = _post(f"{self.base_url}/v1/messages", payload,
                     {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}, self.timeout)
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        calls = [{"id": b["id"], "function": {"name": b["name"], "arguments": b.get("input", {})}}
                 for b in data.get("content", []) if b.get("type") == "tool_use"]
        out = {"role": "assistant", "content": text}
        if calls:
            out["tool_calls"] = calls
        return out


def make_client(cfg) -> Any:
    """Pick the 'brain' from settings: IMPROVISE_PROVIDER = ollama (default) | openai | anthropic."""
    p = cfg.provider.lower()
    if p == "anthropic":
        if not cfg.api_key:
            raise LLMError("Set IMPROVISE_API_KEY (or ANTHROPIC_API_KEY) to use the Anthropic API.")
        return AnthropicClient(cfg.model, cfg.api_key, cfg.api_base or "https://api.anthropic.com", cfg.temperature)
    if p in ("openai", "openai-compatible", "compatible"):
        return OpenAICompatClient(cfg.api_base or "https://api.openai.com/v1", cfg.model, cfg.api_key, cfg.temperature)
    return OllamaClient(cfg.ollama_url, cfg.model, cfg.temperature, think=cfg.think, num_ctx=cfg.num_ctx)
