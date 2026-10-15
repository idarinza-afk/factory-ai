"""A second brain: let the local model consult a stronger AI (Claude, GPT, a bigger local model).

Opt-in only - nothing leaves the machine unless you configure it:
    IMPROVISE_EXPERT_PROVIDER = anthropic | openai | ollama
    IMPROVISE_EXPERT_MODEL    = e.g. claude-sonnet-5-5, gpt-..., qwen3:32b
    IMPROVISE_EXPERT_API_KEY  = key (environment only, never written to files)
    IMPROVISE_EXPERT_API_BASE = for OpenAI-compatible gateways / another Ollama host
Questions are anonymised first (emails, phone numbers, prices, company names removed).
The expert only advises: numbers still come from Improvise's own calculation tools.
"""

from __future__ import annotations

from dataclasses import replace

from .tools import tool

EXPERT_SYSTEM = ("You are a senior production / automation engineer advising a local engineering assistant. "
                 "Answer concisely and concretely: method, key considerations, typical values marked as typical, "
                 "risks, and what to verify. Do not invent prices or supplier data.")


def expert_client():
    from .config import load
    from .llm import make_client
    cfg = load()
    if not cfg.expert_provider:
        return None
    ecfg = replace(cfg, provider=cfg.expert_provider, model=cfg.expert_model or cfg.model,
                   api_base=cfg.expert_api_base, api_key=cfg.expert_api_key or cfg.api_key,
                   ollama_url=cfg.expert_api_base or cfg.ollama_url)
    return make_client(ecfg)


@tool
def ask_expert(question: str, context: str = "") -> str:
    """Ask a stronger AI expert for advice on a hard engineering question (only if configured by the user).

    Args:
        question: the question, self-contained
        context: relevant facts (no customer names, prices or personal data)
    """
    from .contribute import anonymise
    client = expert_client()
    if client is None:
        return "No expert AI is configured (IMPROVISE_EXPERT_PROVIDER). Continue with your own tools and knowledge."
    text = anonymise(question + ("\n\nContext:\n" + context if context else ""))
    msg = client.chat([{"role": "system", "content": EXPERT_SYSTEM}, {"role": "user", "content": text}])
    return "[Expert advice - verify numbers with the calculation tools]\n" + (msg.get("content") or "")
