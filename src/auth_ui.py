"""Streamlit UI for invitation-based authentication."""
from __future__ import annotations

import base64
import html

import streamlit as st

from src import auth as auth_mod
from src.config import ROOT
from src.i18n import t
from src.mail import send_invite_notification, smtp_configured
from src.theme import LOGIN_PAGE_CSS

_LOGO_PATH = ROOT / "assets" / "unhcr_logo.svg"


def _logo_data_uri() -> str | None:
    if not _LOGO_PATH.exists():
        return None
    raw = _LOGO_PATH.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    mime = "image/svg+xml" if _LOGO_PATH.suffix.lower() == ".svg" else "image/png"
    return f"data:{mime};base64,{b64}"


def _err_label(code: str | None, lang: str) -> str:
    if not code:
        return ""
    mapping = {
        "invalid_email": t("auth_err_email", lang),
        "user_exists": t("auth_err_exists", lang),
        "user_missing": t("auth_err_missing", lang),
        "password_too_short": t("auth_err_pwd_short", lang),
        "password_spaces": t("auth_err_pwd_spaces", lang),
        "bad_current_password": t("auth_err_pwd_current", lang),
        "need_bootstrap": t("auth_need_bootstrap", lang),
        "smtp_not_configured": t("auth_err_smtp_config", lang),
        "smtp_send_failed": t("auth_err_smtp_send", lang),
    }
    return mapping.get(code, code)


def _login_lang_bar(lang: str) -> str:
    """Compact FR/EN switch on the login canvas (sidebar is hidden)."""
    c1, c2, c3 = st.columns([1, 1, 4])
    with c1:
        if st.button("FR", key="login_lang_fr", use_container_width=True):
            st.session_state.lang = "fr"
            st.rerun()
    with c2:
        if st.button("EN", key="login_lang_en", use_container_width=True):
            st.session_state.lang = "en"
            st.rerun()
    return st.session_state.get("lang", lang)


def render_login_gate(lang: str) -> auth_mod.AuthUser | None:
    """
    Show login until authenticated. Returns the current user, or None if auth disabled.
    Calls st.stop() when not authenticated.
    """
    if not auth_mod.auth_enabled():
        return None

    auth_mod.ensure_bootstrap_admin()

    user = auth_mod.current_user(st.session_state)
    if user and user.active:
        if user.must_change_password:
            _render_auth_card(lang, mode="force_password", user=user)
            st.stop()
        return user

    _render_auth_card(lang, mode="login")
    st.stop()
    return None  # pragma: no cover


def _render_auth_card(
    lang: str,
    *,
    mode: str,
    user: auth_mod.AuthUser | None = None,
) -> None:
    st.markdown(LOGIN_PAGE_CSS, unsafe_allow_html=True)
    lang = _login_lang_bar(lang)

    logo = _logo_data_uri()
    img = f'<img src="{logo}" alt="UNHCR" />' if logo else ""
    kicker = "REGIONAL BUREAU FOR WEST AND CENTRAL AFRICA - DIMA"
    title = t("app_title", lang)
    heading = (
        t("auth_must_change_title", lang)
        if mode == "force_password"
        else t("auth_login_title", lang)
    )

    st.markdown(
        f"""
        <div class="login-brand">
          {img}
          <div>
            <p class="kicker">{kicker}</p>
            <h1>{title}</h1>
          </div>
        </div>
        <p class="login-title">{heading}</p>
        """,
        unsafe_allow_html=True,
    )

    if mode == "force_password":
        st.markdown(
            f'<p class="login-help">{t("auth_must_change", lang)}</p>',
            unsafe_allow_html=True,
        )

    if mode == "login":
        status = auth_mod.auth_status_message()
        if status == "need_bootstrap":
            st.markdown(
                f'<div class="login-note">{_err_label("need_bootstrap", lang)}</div>',
                unsafe_allow_html=True,
            )
        with st.form("auth_login_form"):
            email = st.text_input(t("auth_email", lang), placeholder="name@unhcr.org")
            password = st.text_input(
                t("auth_password", lang), type="password", placeholder="••••••••"
            )
            submitted = st.form_submit_button(
                t("auth_sign_in", lang), type="primary", use_container_width=True
            )
        if submitted:
            found = auth_mod.authenticate(email, password)
            if found is None:
                st.error(t("auth_err_credentials", lang))
            else:
                auth_mod.login_user(st.session_state, found)
                st.rerun()
    else:
        assert user is not None
        with st.form("auth_force_pwd"):
            current = st.text_input(t("auth_password_current", lang), type="password")
            new1 = st.text_input(t("auth_password_new", lang), type="password")
            new2 = st.text_input(t("auth_password_confirm", lang), type="password")
            ok = st.form_submit_button(
                t("auth_password_save", lang), type="primary", use_container_width=True
            )
        if ok:
            if new1 != new2:
                st.error(t("auth_err_pwd_mismatch", lang))
            else:
                err = auth_mod.change_password(user.email, current, new1)
                if err:
                    st.error(_err_label(err, lang))
                else:
                    refreshed = auth_mod.get_user(user.email)
                    if refreshed:
                        auth_mod.login_user(st.session_state, refreshed)
                    st.success(t("auth_password_updated", lang))
                    st.rerun()

    st.markdown(
        f'<p class="login-footer">{t("auth_login_footer", lang)}</p>',
        unsafe_allow_html=True,
    )


def render_auth_sidebar(lang: str, user: auth_mod.AuthUser | None) -> None:
    if user is None:
        return
    role_lbl = (
        t("auth_role_admin", lang)
        if user.role == "admin"
        else t("auth_role_user", lang)
    )
    st.sidebar.markdown(
        f"""
        <div style="margin:0.35rem 0 0.75rem 0;padding:0.55rem 0.7rem;
                    background:#F7FBFE;border-left:3px solid #0072BC;border-radius:0 4px 4px 0;">
          <div style="font-size:0.72rem;color:#737373;font-weight:600;text-transform:uppercase;
                      letter-spacing:0.04em;">{t("auth_signed_in_as", lang)}</div>
          <div style="font-size:0.98rem;font-weight:700;color:#0B3754;margin-top:0.15rem;">
            {html.escape(user.name)}
          </div>
          <div style="font-size:0.78rem;color:#05568B;margin-top:0.1rem;">{html.escape(role_lbl)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.sidebar.expander(t("auth_account", lang), expanded=False):
        st.caption(user.email)
        if st.button(t("auth_sign_out", lang), key="auth_logout"):
            auth_mod.logout_user(st.session_state)
            st.rerun()

        st.markdown(f"**{t('auth_change_password', lang)}**")
        with st.form("auth_change_pwd_form"):
            current = st.text_input(t("auth_password_current", lang), type="password")
            new1 = st.text_input(t("auth_password_new", lang), type="password")
            new2 = st.text_input(t("auth_password_confirm", lang), type="password")
            save = st.form_submit_button(t("auth_password_save", lang))
        if save:
            if new1 != new2:
                st.error(t("auth_err_pwd_mismatch", lang))
            else:
                err = auth_mod.change_password(user.email, current, new1)
                if err:
                    st.error(_err_label(err, lang))
                else:
                    st.success(t("auth_password_updated", lang))


def render_admin_users_panel(lang: str, user: auth_mod.AuthUser | None) -> None:
    if user is None or user.role != "admin":
        return

    st.markdown(f"### {t('auth_admin_title', lang)}")
    st.caption(t("auth_admin_help", lang))
    if not smtp_configured():
        st.info(t("auth_notify_smtp_hint", lang))

    with st.form("auth_invite_form"):
        c1, c2 = st.columns(2)
        with c1:
            email = st.text_input(t("auth_email", lang), key="invite_email")
            name = st.text_input(t("auth_name", lang), key="invite_name")
        with c2:
            temp_pwd = st.text_input(
                t("auth_temp_password", lang), type="password", key="invite_pwd"
            )
            role = st.selectbox(
                t("auth_role", lang),
                options=["user", "admin"],
                format_func=lambda r: (
                    t("auth_role_admin", lang) if r == "admin" else t("auth_role_user", lang)
                ),
            )
        must_change = st.checkbox(t("auth_must_change_flag", lang), value=True)
        send_notify = st.checkbox(t("auth_notify_send", lang), value=True)
        create = st.form_submit_button(t("auth_invite", lang), type="primary")

    if create:
        created, err = auth_mod.create_user(
            email=email,
            name=name,
            password=temp_pwd,
            role=role,
            must_change_password=must_change,
        )
        if err:
            st.error(_err_label(err, lang))
        elif created:
            st.success(t("auth_invite_ok", lang).format(email=created.email))
            if send_notify:
                mail_err = send_invite_notification(
                    to_email=created.email,
                    name=created.name,
                    temp_password=temp_pwd,
                    lang=lang,
                    must_change=must_change,
                )
                if mail_err:
                    st.warning(_err_label(mail_err, lang))
                else:
                    st.success(t("auth_notify_ok", lang).format(email=created.email))

    rows = auth_mod.list_users()
    if not rows:
        st.info("—")
        return

    for u in rows:
        cols = st.columns([3, 2, 1, 1, 2])
        cols[0].write(f"**{u.name}**  \n{u.email}")
        cols[1].write(
            t("auth_role_admin", lang) if u.role == "admin" else t("auth_role_user", lang)
        )
        cols[2].write(
            t("auth_active", lang) if u.active else t("auth_inactive", lang)
        )
        if u.email == user.email:
            cols[3].caption("—")
        else:
            label = t("auth_deactivate", lang) if u.active else t("auth_activate", lang)
            if cols[3].button(label, key=f"toggle_{u.email}"):
                auth_mod.set_user_active(u.email, not u.active)
                st.rerun()
        with cols[4]:
            with st.popover(t("auth_reset_password", lang)):
                with st.form(f"reset_{u.email}"):
                    npwd = st.text_input(
                        t("auth_password_new", lang),
                        type="password",
                        key=f"reset_pwd_{u.email}",
                    )
                    if st.form_submit_button(t("auth_password_save", lang)):
                        err = auth_mod.set_password(
                            u.email, npwd, force_must_change=True
                        )
                        if err:
                            st.error(_err_label(err, lang))
                        else:
                            st.success(t("auth_password_updated", lang))
