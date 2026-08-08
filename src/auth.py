"""Invitation-based local authentication (no public sign-up).

Users are created by an admin. Passwords are stored as bcrypt hashes.

Primary store: ``data/auth/users.json`` (gitignored).
Durable store (Streamlit Cloud): optional GitHub private file via
``AUTH_GITHUB_TOKEN`` / ``AUTH_GITHUB_REPO`` / ``AUTH_GITHUB_PATH``.

Optional seed from Streamlit secrets ``auth.users.*`` and bootstrap admin
from ``AUTH_ADMIN_*``.
"""
from __future__ import annotations

import base64
import json
import re
import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import bcrypt
import requests

from src.config import ROOT, _setting

USERS_PATH = ROOT / "data" / "auth" / "users.json"
SESSION_USER_KEY = "auth_user"
SESSION_AUTH_KEY = "auth_authenticated"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_REMOTE_SHA: str | None = None


@dataclass
class AuthUser:
    email: str
    name: str
    role: str  # admin | user
    active: bool = True
    must_change_password: bool = False
    created_at: str = ""
    updated_at: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "active": self.active,
            "must_change_password": self.must_change_password,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def auth_enabled() -> bool:
    raw = (_setting("AUTH_ENABLED", "true") or "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def validate_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(_normalize_email(email)))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:  # noqa: BLE001
        return False


def validate_password_strength(password: str) -> str | None:
    if password is None or len(password) < 8:
        return "password_too_short"
    if password.strip() != password:
        return "password_spaces"
    return None


def _empty_store() -> dict[str, Any]:
    return {"version": 1, "users": {}}


def _normalize_store(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return _empty_store()
    data.setdefault("version", 1)
    data.setdefault("users", {})
    if not isinstance(data["users"], dict):
        data["users"] = {}
    return data


def _read_file_store() -> dict[str, Any]:
    if not USERS_PATH.exists():
        return _empty_store()
    try:
        data = json.loads(USERS_PATH.read_text(encoding="utf-8"))
        return _normalize_store(data)
    except Exception:  # noqa: BLE001
        return _empty_store()


def _write_file_store(store: dict[str, Any]) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = USERS_PATH.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(USERS_PATH)


def remote_auth_configured() -> bool:
    """True when durable GitHub user store secrets are present."""
    return bool(
        (_setting("AUTH_GITHUB_TOKEN", "") or "").strip()
        and (_setting("AUTH_GITHUB_REPO", "") or "").strip()
    )


def _github_cfg() -> dict[str, str]:
    return {
        "token": (_setting("AUTH_GITHUB_TOKEN", "") or "").strip(),
        "repo": (_setting("AUTH_GITHUB_REPO", "") or "").strip(),
        "path": (_setting("AUTH_GITHUB_PATH", "users.json") or "users.json").strip(),
        "branch": (_setting("AUTH_GITHUB_BRANCH", "main") or "main").strip(),
    }


def _github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _read_remote_store() -> dict[str, Any] | None:
    """Load users.json from GitHub Contents API. None if unavailable."""
    global _REMOTE_SHA
    if not remote_auth_configured():
        return None
    cfg = _github_cfg()
    url = (
        f"https://api.github.com/repos/{cfg['repo']}/contents/{cfg['path']}"
        f"?ref={cfg['branch']}"
    )
    try:
        resp = requests.get(url, headers=_github_headers(cfg["token"]), timeout=30)
        if resp.status_code == 404:
            _REMOTE_SHA = None
            return _empty_store()
        if resp.status_code >= 400:
            return None
        payload = resp.json()
        _REMOTE_SHA = str(payload.get("sha") or "") or None
        raw = base64.b64decode(payload.get("content") or "").decode("utf-8")
        return _normalize_store(json.loads(raw))
    except Exception:  # noqa: BLE001
        return None


def _write_remote_store(store: dict[str, Any]) -> bool:
    """Persist users.json to GitHub. Returns True on success."""
    global _REMOTE_SHA
    if not remote_auth_configured():
        return False
    cfg = _github_cfg()
    api = f"https://api.github.com/repos/{cfg['repo']}/contents/{cfg['path']}"
    headers = _github_headers(cfg["token"])
    # Refresh SHA to avoid update conflicts
    try:
        current = requests.get(
            f"{api}?ref={cfg['branch']}", headers=headers, timeout=30
        )
        if current.status_code == 200:
            _REMOTE_SHA = str(current.json().get("sha") or "") or None
        elif current.status_code == 404:
            _REMOTE_SHA = None
    except Exception:  # noqa: BLE001
        pass

    body: dict[str, Any] = {
        "message": "chore(auth): update users store",
        "content": base64.b64encode(
            (json.dumps(store, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        ).decode("ascii"),
        "branch": cfg["branch"],
    }
    if _REMOTE_SHA:
        body["sha"] = _REMOTE_SHA
    try:
        resp = requests.put(api, headers=headers, json=body, timeout=30)
        if resp.status_code >= 400:
            return False
        content = (resp.json() or {}).get("content") or {}
        _REMOTE_SHA = str(content.get("sha") or "") or _REMOTE_SHA
        return True
    except Exception:  # noqa: BLE001
        return False


def _secrets_users() -> dict[str, Any]:
    """Optional users map from Streamlit secrets: auth.users.<email>."""
    try:
        import streamlit as st

        auth = st.secrets.get("auth", None)
        if auth is None:
            return {}
        users = auth.get("users", {}) if hasattr(auth, "get") else {}
        if users is None:
            return {}
        # AttrDict / dict compatibility
        out: dict[str, Any] = {}
        for key in users:
            row = users[key]
            email = _normalize_email(
                str(row.get("email", key) if hasattr(row, "get") else key)
            )
            if not email:
                continue
            out[email] = {
                "email": email,
                "name": str(row.get("name", email) if hasattr(row, "get") else email),
                "role": str(row.get("role", "user") if hasattr(row, "get") else "user"),
                "active": bool(row.get("active", True) if hasattr(row, "get") else True),
                "must_change_password": bool(
                    row.get("must_change_password", False)
                    if hasattr(row, "get")
                    else False
                ),
                "password_hash": str(
                    row.get("password_hash", "") if hasattr(row, "get") else ""
                ),
                "created_at": str(
                    row.get("created_at", "") if hasattr(row, "get") else ""
                ),
                "updated_at": str(
                    row.get("updated_at", "") if hasattr(row, "get") else ""
                ),
            }
        return out
    except Exception:  # noqa: BLE001
        return {}


def load_store() -> dict[str, Any]:
    # Prefer durable remote store when configured (Streamlit Cloud)
    remote = _read_remote_store()
    if remote is not None:
        store = remote
        # Keep a local cache for faster subsequent reads / offline admin tools
        try:
            _write_file_store(store)
        except Exception:  # noqa: BLE001
            pass
    else:
        store = _read_file_store()

    # Secrets users fill gaps / bootstrap (file/remote wins for password_hash if present)
    for email, row in _secrets_users().items():
        if email not in store["users"]:
            store["users"][email] = row
        else:
            existing = store["users"][email]
            if not existing.get("password_hash") and row.get("password_hash"):
                existing["password_hash"] = row["password_hash"]
            for k in ("name", "role", "active", "must_change_password"):
                if k in row and row[k] is not None:
                    existing.setdefault(k, row[k])
    return store


def save_store(store: dict[str, Any]) -> None:
    _write_file_store(store)
    if remote_auth_configured():
        _write_remote_store(store)


def ensure_bootstrap_admin() -> AuthUser | None:
    """Create first admin from AUTH_ADMIN_EMAIL / AUTH_ADMIN_PASSWORD if store empty."""
    store = load_store()
    if store["users"]:
        return None
    email = _normalize_email(_setting("AUTH_ADMIN_EMAIL", ""))
    password = _setting("AUTH_ADMIN_PASSWORD", "")
    if not email or not password:
        return None
    if not validate_email(email):
        return None
    if validate_password_strength(password):
        return None
    now = _now()
    store["users"][email] = {
        "email": email,
        "name": _setting("AUTH_ADMIN_NAME", "") or email.split("@")[0],
        "role": "admin",
        "active": True,
        "must_change_password": True,
        "password_hash": hash_password(password),
        "created_at": now,
        "updated_at": now,
    }
    save_store(store)
    return get_user(email)


def get_user(email: str) -> AuthUser | None:
    email = _normalize_email(email)
    row = load_store()["users"].get(email)
    if not row:
        return None
    return AuthUser(
        email=email,
        name=str(row.get("name") or email),
        role=str(row.get("role") or "user"),
        active=bool(row.get("active", True)),
        must_change_password=bool(row.get("must_change_password", False)),
        created_at=str(row.get("created_at") or ""),
        updated_at=str(row.get("updated_at") or ""),
    )


def list_users() -> list[AuthUser]:
    users = []
    for email in sorted(load_store()["users"].keys()):
        u = get_user(email)
        if u:
            users.append(u)
    return users


def authenticate(email: str, password: str) -> AuthUser | None:
    email = _normalize_email(email)
    store = load_store()
    row = store["users"].get(email)
    if not row or not row.get("active", True):
        return None
    if not verify_password(password, str(row.get("password_hash") or "")):
        return None
    return get_user(email)


def create_user(
    *,
    email: str,
    name: str,
    password: str,
    role: str = "user",
    must_change_password: bool = True,
) -> tuple[AuthUser | None, str | None]:
    email = _normalize_email(email)
    if not validate_email(email):
        return None, "invalid_email"
    err = validate_password_strength(password)
    if err:
        return None, err
    role = role if role in {"admin", "user"} else "user"
    store = load_store()
    if email in store["users"]:
        return None, "user_exists"
    now = _now()
    store["users"][email] = {
        "email": email,
        "name": (name or email.split("@")[0]).strip(),
        "role": role,
        "active": True,
        "must_change_password": must_change_password,
        "password_hash": hash_password(password),
        "created_at": now,
        "updated_at": now,
    }
    save_store(store)
    return get_user(email), None


def set_password(
    email: str,
    new_password: str,
    *,
    clear_must_change: bool = True,
    force_must_change: bool | None = None,
) -> str | None:
    email = _normalize_email(email)
    err = validate_password_strength(new_password)
    if err:
        return err
    store = load_store()
    if email not in store["users"]:
        return "user_missing"
    store["users"][email]["password_hash"] = hash_password(new_password)
    if force_must_change is not None:
        store["users"][email]["must_change_password"] = bool(force_must_change)
    elif clear_must_change:
        store["users"][email]["must_change_password"] = False
    store["users"][email]["updated_at"] = _now()
    save_store(store)
    return None


def change_password(email: str, current_password: str, new_password: str) -> str | None:
    email = _normalize_email(email)
    store = load_store()
    row = store["users"].get(email)
    if not row:
        return "user_missing"
    if not verify_password(current_password, str(row.get("password_hash") or "")):
        return "bad_current_password"
    return set_password(email, new_password, clear_must_change=True)


def set_user_active(email: str, active: bool) -> str | None:
    email = _normalize_email(email)
    store = load_store()
    if email not in store["users"]:
        return "user_missing"
    store["users"][email]["active"] = bool(active)
    store["users"][email]["updated_at"] = _now()
    save_store(store)
    return None


def is_authenticated(session_state: Any) -> bool:
    return bool(session_state.get(SESSION_AUTH_KEY)) and bool(
        session_state.get(SESSION_USER_KEY)
    )


def current_user(session_state: Any) -> AuthUser | None:
    raw = session_state.get(SESSION_USER_KEY)
    if not isinstance(raw, dict):
        return None
    email = _normalize_email(str(raw.get("email", "")))
    return get_user(email) if email else None


def login_user(session_state: Any, user: AuthUser) -> None:
    session_state[SESSION_AUTH_KEY] = True
    session_state[SESSION_USER_KEY] = user.to_public_dict()


def logout_user(session_state: Any) -> None:
    session_state[SESSION_AUTH_KEY] = False
    session_state[SESSION_USER_KEY] = None


def auth_status_message() -> str:
    """Help text when bootstrap admin is missing."""
    if load_store()["users"]:
        return ""
    if _setting("AUTH_ADMIN_EMAIL") and _setting("AUTH_ADMIN_PASSWORD"):
        return ""
    return "need_bootstrap"


def _generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def request_password_reset(email: str) -> tuple[str, str | None, AuthUser | None]:
    """Prepare a password reset for an active account.

    Returns ``(status, temp_password, user)``. The password is **not** saved
    until ``complete_password_reset`` is called after a successful notification.
    """
    email = _normalize_email(email)
    if not validate_email(email):
        return "invalid_email", None, None
    user = get_user(email)
    if user is None or not user.active:
        return "reset_requested", None, None
    temp_pwd = _generate_temp_password()
    err = validate_password_strength(temp_pwd)
    if err:
        return err, None, None
    return "reset_requested", temp_pwd, user


def complete_password_reset(email: str, temp_password: str) -> str | None:
    return set_password(email, temp_password, force_must_change=True)
