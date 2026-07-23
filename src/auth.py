"""Authentication and role helpers for MSR WCA (Phase 2).

Modes (secret AUTH_MODE, auto-detected if omitted):
  - open      : no login (local / until secrets are set)
  - password  : shared APP_PASSWORD
  - users     : per-user passwords under [app_users.*] in secrets
  - oidc      : Streamlit st.login() when [auth] is configured (Azure AD / Google / …)

Roles: reader | country | admin
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from src.config import APP_CHANNEL, _setting


UserInfo = dict[str, Any]


def _secrets() -> Any:
    try:
        return st.secrets
    except Exception:  # noqa: BLE001
        return None


def _secret_get(key: str, default: str = "") -> str:
    sec = _secrets()
    if sec is not None:
        try:
            if key in sec:
                return str(sec[key])
        except Exception:  # noqa: BLE001
            pass
    return _setting(key, default)


def _has_oidc_config() -> bool:
    sec = _secrets()
    if sec is None:
        return False
    try:
        auth = sec.get("auth", None)
        if auth is None:
            return False
        # Shared keys required by Streamlit OIDC
        return bool(auth.get("redirect_uri") and auth.get("cookie_secret"))
    except Exception:  # noqa: BLE001
        return False


def _app_users() -> dict[str, dict[str, Any]]:
    sec = _secrets()
    if sec is None:
        return {}
    try:
        users = sec.get("app_users", {})
        if not users:
            return {}
        out: dict[str, dict[str, Any]] = {}
        for name, meta in users.items():
            if hasattr(meta, "to_dict"):
                meta = dict(meta)
            elif not isinstance(meta, dict):
                try:
                    meta = dict(meta)
                except Exception:  # noqa: BLE001
                    meta = {"password": str(meta)}
            out[str(name)] = dict(meta)
        return out
    except Exception:  # noqa: BLE001
        return {}


def resolve_auth_mode() -> str:
    explicit = (_secret_get("AUTH_MODE") or "").strip().lower()
    if explicit in {"open", "password", "users", "oidc"}:
        return explicit
    if _has_oidc_config():
        return "oidc"
    if _app_users():
        return "users"
    if _secret_get("APP_PASSWORD"):
        return "password"
    return "open"


def _normalize_role(raw: str | None) -> str:
    role = (raw or "reader").strip().lower()
    if role in {"admin", "dima", "administrator"}:
        return "admin"
    if role in {"country", "pays", "country_officer"}:
        return "country"
    return "reader"


def _parse_countries(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(x).upper() for x in raw if str(x).strip()]
    return [p.strip().upper() for p in str(raw).split(",") if p.strip()]


def current_user() -> UserInfo | None:
    return st.session_state.get("msr_user")


def logout() -> None:
    st.session_state.pop("msr_user", None)
    if hasattr(st, "logout"):
        try:
            st.logout()
        except Exception:  # noqa: BLE001
            pass


def _set_user(user: UserInfo, *, audit: bool = True) -> None:
    previous = st.session_state.get("msr_user")
    st.session_state["msr_user"] = user
    if audit and not previous:
        try:
            from src.audit import log_event

            log_event("login", user=user)
        except Exception:  # noqa: BLE001
            pass


def _login_form_password(lang: str) -> None:
    st.markdown("### " + ("Connexion" if lang == "fr" else "Sign in"))
    st.caption(
        "Environnement de validation — authentification requise."
        if lang == "fr"
        else "Validation environment — authentication required."
    )
    with st.form("msr_login_password"):
        pwd = st.text_input(
            "Mot de passe" if lang == "fr" else "Password",
            type="password",
        )
        name = st.text_input(
            "Votre nom (optionnel)" if lang == "fr" else "Your name (optional)",
            value="",
        )
        submitted = st.form_submit_button("Se connecter" if lang == "fr" else "Sign in")
    if submitted:
        expected = _secret_get("APP_PASSWORD")
        if expected and pwd == expected:
            _set_user(
                {
                    "name": name.strip() or "Staging user",
                    "email": "",
                    "role": "admin" if APP_CHANNEL == "staging" else "reader",
                    "countries": [],
                    "auth_mode": "password",
                }
            )
            st.rerun()
        st.error(
            "Mot de passe incorrect." if lang == "fr" else "Incorrect password."
        )


def _login_form_users(lang: str) -> None:
    users = _app_users()
    st.markdown("### " + ("Connexion" if lang == "fr" else "Sign in"))
    with st.form("msr_login_users"):
        username = st.text_input("Identifiant" if lang == "fr" else "Username")
        pwd = st.text_input(
            "Mot de passe" if lang == "fr" else "Password", type="password"
        )
        submitted = st.form_submit_button("Se connecter" if lang == "fr" else "Sign in")
    if submitted:
        meta = users.get(username.strip())
        if meta and str(meta.get("password", "")) == pwd:
            _set_user(
                {
                    "name": str(meta.get("name") or username),
                    "email": str(meta.get("email") or ""),
                    "role": _normalize_role(str(meta.get("role", "reader"))),
                    "countries": _parse_countries(meta.get("countries")),
                    "auth_mode": "users",
                    "username": username.strip(),
                }
            )
            st.rerun()
        st.error(
            "Identifiants invalides." if lang == "fr" else "Invalid credentials."
        )


def _login_oidc(lang: str) -> None:
    st.markdown("### " + ("Connexion institutionnelle" if lang == "fr" else "Institutional sign-in"))
    st.caption(
        "SSO (OIDC) — Azure AD / Microsoft / autre fournisseur configuré dans les secrets."
        if lang == "fr"
        else "SSO (OIDC) — Azure AD / Microsoft / other provider configured in secrets."
    )
    if not hasattr(st, "login"):
        st.error(
            "Cette version de Streamlit ne supporte pas st.login(). Passez en AUTH_MODE=users."
            if lang == "fr"
            else "This Streamlit version does not support st.login(). Use AUTH_MODE=users."
        )
        st.stop()
    if st.button("Se connecter avec SSO" if lang == "fr" else "Sign in with SSO"):
        st.login()
    # After redirect, st.user is populated
    user_obj = getattr(st, "user", None)
    if user_obj is not None and getattr(user_obj, "is_logged_in", False):
        email = str(getattr(user_obj, "email", "") or "")
        name = str(getattr(user_obj, "name", "") or email or "SSO user")
        # Role mapping by email in [app_users] optional
        role = "reader"
        countries: list[str] = []
        for uname, meta in _app_users().items():
            if str(meta.get("email", "")).lower() == email.lower() or uname.lower() == email.lower():
                role = _normalize_role(str(meta.get("role", "reader")))
                countries = _parse_countries(meta.get("countries"))
                break
        _set_user(
            {
                "name": name,
                "email": email,
                "role": role,
                "countries": countries,
                "auth_mode": "oidc",
            }
        )
        st.rerun()


def require_auth(lang: str) -> UserInfo:
    """Gate the app; return the authenticated user dict."""
    mode = resolve_auth_mode()
    existing = current_user()
    if existing:
        return existing

    if mode == "open":
        user = {
            "name": "Open access",
            "email": "",
            "role": "admin" if APP_CHANNEL == "staging" else "reader",
            "countries": [],
            "auth_mode": "open",
        }
        _set_user(user)
        return user

    if mode == "password":
        if not _secret_get("APP_PASSWORD"):
            st.warning(
                "AUTH_MODE=password mais APP_PASSWORD est vide dans les secrets."
                if lang == "fr"
                else "AUTH_MODE=password but APP_PASSWORD is empty in secrets."
            )
            st.stop()
        _login_form_password(lang)
        st.stop()

    if mode == "users":
        if not _app_users():
            st.warning(
                "AUTH_MODE=users mais [app_users] est vide."
                if lang == "fr"
                else "AUTH_MODE=users but [app_users] is empty."
            )
            st.stop()
        _login_form_users(lang)
        st.stop()

    if mode == "oidc":
        _login_oidc(lang)
        st.stop()

    st.error(f"Unknown AUTH_MODE: {mode}")
    st.stop()
    return {}  # pragma: no cover


def render_user_badge(lang: str, user: UserInfo) -> None:
    role = user.get("role", "reader")
    role_lbl = {
        "admin": "Admin DIMA" if lang == "fr" else "DIMA admin",
        "country": "Pays" if lang == "fr" else "Country",
        "reader": "Lecteur" if lang == "fr" else "Reader",
    }.get(role, role)
    name = user.get("name") or user.get("email") or "—"
    st.sidebar.caption(f"{name} · {role_lbl}")
    mode = user.get("auth_mode", "")
    if mode == "open":
        st.sidebar.caption(
            "Auth ouverte (configurez les secrets pour activer la connexion)."
            if lang == "fr"
            else "Open auth (configure secrets to enable login)."
        )
    if mode != "open" and st.sidebar.button(
        "Déconnexion" if lang == "fr" else "Sign out", key="msr_logout"
    ):
        logout()
        st.rerun()


def apply_role_host_filter(
    selected_hosts: list[str],
    user: UserInfo,
    host_options: list[str],
) -> list[str]:
    """Country role: restrict to configured ISO3 list."""
    if user.get("role") != "country":
        return selected_hosts
    allowed = [c for c in user.get("countries") or [] if c in host_options]
    if not allowed:
        return selected_hosts
    if not selected_hosts:
        return allowed
    return [c for c in selected_hosts if c in allowed] or allowed
