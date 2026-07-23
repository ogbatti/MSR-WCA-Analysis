"""Feature flags for staged rollout (Phase 4)."""
from __future__ import annotations

from src.config import _setting


def _on(name: str, default: str = "off") -> bool:
    raw = (_setting(name, default) or default).strip().lower()
    return raw in {"on", "1", "true", "yes"}


def feature_assistant() -> bool:
    """Show the Assistant tab. Default on for staging/develop."""
    return _on("FEATURE_ASSISTANT", "on")


def feature_assistant_llm() -> bool:
    """Allow optional LLM rephrase (still never invents numbers)."""
    return _on("ASSISTANT_LLM", "off")
