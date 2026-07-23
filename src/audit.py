"""Lightweight audit trail for sensitive actions (PDF exports, logins)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import CACHE_DIR


def _audit_path() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / "audit_log.jsonl"


def log_event(
    action: str,
    *,
    user: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Append one JSON line to the local audit log (best-effort)."""
    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "action": action,
        "user": (user or {}).get("name") or (user or {}).get("email") or "anonymous",
        "role": (user or {}).get("role"),
        "auth_mode": (user or {}).get("auth_mode"),
        "details": details or {},
    }
    try:
        path = _audit_path()
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        # Never break the app for audit failures
        pass


def read_recent_events(limit: int = 50) -> list[dict[str, Any]]:
    path = _audit_path()
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]
        return rows[-limit:][::-1]
    except Exception:  # noqa: BLE001
        return []
