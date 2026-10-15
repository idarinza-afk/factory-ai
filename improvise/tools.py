"""Tool registry.

Any engineering function decorated with ``@tool`` becomes callable by the
local LLM. The JSON schema the model sees is built from the function's
type hints and docstring, so adding a new capability is just writing a
normal, testable Python function.
"""

from __future__ import annotations

import inspect
import json
import typing
from dataclasses import dataclass
from typing import Any, Callable

_PY_TO_JSON = {
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "array",
    dict: "object",
}


@dataclass
class Tool:
    name: str
    description: str
    func: Callable[..., Any]
    parameters: dict

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def call(self, arguments: dict | str) -> Any:
        if isinstance(arguments, str):
            arguments = json.loads(arguments or "{}")
        return self.func(**arguments)


REGISTRY: dict[str, Tool] = {}


def _json_type(annotation: Any) -> dict:
    origin = typing.get_origin(annotation)
    if origin in (list, typing.List):
        args = typing.get_args(annotation)
        item = _json_type(args[0]) if args else {}
        return {"type": "array", "items": item}
    if origin in (dict, typing.Dict):
        return {"type": "object"}
    if origin is typing.Union:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        return _json_type(args[0]) if args else {"type": "string"}
    return {"type": _PY_TO_JSON.get(annotation, "string")}


def _param_docs(doc: str) -> dict[str, str]:
    """Parse ``name: description`` lines from an 'Args:' docstring section."""
    out: dict[str, str] = {}
    in_args = False
    for line in doc.splitlines():
        s = line.strip()
        if s.lower().startswith("args:"):
            in_args = True
            continue
        if in_args:
            if not s or s.endswith(":") and " " not in s:
                if out:
                    break
                continue
            if ":" in s:
                k, v = s.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def tool(func: Callable[..., Any]) -> Callable[..., Any]:
    doc = inspect.getdoc(func) or ""
    summary = doc.split("\n\n")[0].strip()
    pdocs = _param_docs(doc)
    hints = typing.get_type_hints(func)
    sig = inspect.signature(func)
    props: dict[str, dict] = {}
    required: list[str] = []
    for name, p in sig.parameters.items():
        schema = _json_type(hints.get(name, str))
        if name in pdocs:
            schema["description"] = pdocs[name]
        props[name] = schema
        if p.default is inspect.Parameter.empty:
            required.append(name)
    REGISTRY[func.__name__] = Tool(
        name=func.__name__,
        description=summary,
        func=func,
        parameters={"type": "object", "properties": props, "required": required},
    )
    return func


PLUGINS: dict[str, object] = {}


def load_plugins() -> dict[str, object]:
    """Load add-on packages (e.g. improvise-pro) declared under the
    'improvise.plugins' entry-point group. A plugin module may expose
    register() to add tools, KNOWLEDGE_DIR, PROMPT and register_cli(subparsers)."""
    if PLUGINS:
        return PLUGINS
    from importlib.metadata import entry_points
    for ep in entry_points(group="improvise.plugins"):
        try:
            mod = ep.load()
        except Exception as e:  # a broken plugin must not break the core
            print(f"[improvise] plugin {ep.name} failed to load: {e}")
            continue
        if hasattr(mod, "register"):
            mod.register()
        PLUGINS[ep.name] = mod
    return PLUGINS


def load_all() -> dict[str, Tool]:
    """Import every module that registers tools, then any installed plugins."""
    from . import calc, coding, documents, layout, skills  # noqa: F401
    from .memory import register_memory_tools

    register_memory_tools()
    load_plugins()
    return REGISTRY
