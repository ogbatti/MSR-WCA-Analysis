"""Streamlit UI for invitation-based authentication."""
from __future__ import annotations

import streamlit as st

from src import auth as auth_mod
from src.i18n import t


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
    }
    return mapping.get(code, code)


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
            _render_force_change_password(lang, user)
            st.stop()
        return user

    _render_login_page(lang)
    st.stop()
    return None  # pragma: no cover


def _render_login_page(lang: str) -> None:
    st.markdown(f"### {t('auth_login_title', lang)}")
    st.caption(t("auth_login_help", lang))

    status = auth_mod.auth_status_message()
    if status == "need_bootstrap":
        st.warning(_err_label("need_bootstrap", lang))

    with st.form("auth_login_form"):
        email = st.text_input(t("auth_email", lang))
        password = st.text_input(t("auth_password", lang), type="password")
        submitted = st.form_submit_button(t("auth_sign_in", lang), type="primary")

    if submitted:
        user = auth_mod.authenticate(email, password)
        if user is None:
            st.error(t("auth_err_credentials", lang))
        else:
            auth_mod.login_user(st.session_state, user)
            st.rerun()


def _render_force_change_password(lang: str, user: auth_mod.AuthUser) -> None:
    st.warning(t("auth_must_change", lang))
    with st.form("auth_force_pwd"):
        current = st.text_input(t("auth_password_current", lang), type="password")
        new1 = st.text_input(t("auth_password_new", lang), type="password")
        new2 = st.text_input(t("auth_password_confirm", lang), type="password")
        ok = st.form_submit_button(t("auth_password_save", lang), type="primary")
    if ok:
        if new1 != new2:
            st.error(t("auth_err_pwd_mismatch", lang))
            return
        err = auth_mod.change_password(user.email, current, new1)
        if err:
            st.error(_err_label(err, lang))
            return
        refreshed = auth_mod.get_user(user.email)
        if refreshed:
            auth_mod.login_user(st.session_state, refreshed)
        st.success(t("auth_password_updated", lang))
        st.rerun()


def render_auth_sidebar(lang: str, user: auth_mod.AuthUser | None) -> None:
    if user is None:
        return
    with st.sidebar.expander(t("auth_account", lang), expanded=False):
        st.caption(f"{user.name} · {user.email}")
        st.caption(
            t("auth_role_admin", lang)
            if user.role == "admin"
            else t("auth_role_user", lang)
        )
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
