"""Phase 2 — auth roles and audit helpers."""
from __future__ import annotations

from src.auth import apply_role_host_filter
from src.audit import log_event, read_recent_events


def test_country_role_restricts_hosts():
    user = {"role": "country", "countries": ["CMR", "TCD"]}
    assert apply_role_host_filter([], user, ["CMR", "TCD", "NGA"]) == ["CMR", "TCD"]
    assert apply_role_host_filter(["NGA", "CMR"], user, ["CMR", "TCD", "NGA"]) == ["CMR"]


def test_reader_role_keeps_selection():
    user = {"role": "reader", "countries": []}
    assert apply_role_host_filter(["NGA"], user, ["CMR", "NGA"]) == ["NGA"]


def test_audit_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("src.audit.CACHE_DIR", tmp_path)
    log_event("pdf_generate", user={"name": "Ada", "role": "admin"}, details={"report": "flash"})
    rows = read_recent_events(10)
    assert rows
    assert rows[0]["action"] == "pdf_generate"
    assert rows[0]["user"] == "Ada"
