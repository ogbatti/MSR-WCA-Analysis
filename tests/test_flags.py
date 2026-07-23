"""Phase 4 — feature flags."""
from __future__ import annotations

from src.flags import feature_assistant, feature_assistant_llm


def test_feature_flags_defaults(monkeypatch):
    monkeypatch.setattr("src.flags._setting", lambda name, default="": default)
    assert feature_assistant() is True  # default on
    assert feature_assistant_llm() is False  # default off


def test_feature_assistant_can_disable(monkeypatch):
    def _set(name, default=""):
        return "off" if name == "FEATURE_ASSISTANT" else default

    monkeypatch.setattr("src.flags._setting", _set)
    assert feature_assistant() is False
