"""Transactional email via SMTP (invite notifications)."""
from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from src.config import _setting


def smtp_configured() -> bool:
    return bool(_setting("SMTP_HOST", "").strip() and _setting("SMTP_USER", "").strip())


def app_public_url() -> str:
    return (_setting("APP_PUBLIC_URL", "https://dimawca.app") or "https://dimawca.app").rstrip(
        "/"
    )


def _smtp_settings() -> dict[str, str | int | bool]:
    host = _setting("SMTP_HOST", "").strip()
    port_raw = (_setting("SMTP_PORT", "587") or "587").strip()
    try:
        port = int(port_raw)
    except ValueError:
        port = 587
    user = _setting("SMTP_USER", "").strip()
    password = _setting("SMTP_PASSWORD", "")
    from_addr = (_setting("SMTP_FROM", "") or user).strip()
    starttls = (_setting("SMTP_STARTTLS", "true") or "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "from_addr": from_addr,
        "starttls": starttls,
    }


def build_invite_email(
    *,
    to_email: str,
    name: str,
    temp_password: str,
    lang: str,
    must_change: bool,
) -> EmailMessage:
    url = app_public_url()
    display = (name or to_email).strip()
    if lang == "en":
        subject = "Your access to the MSR WCA dashboard"
        must_line = (
            "On first sign-in you will be asked to set a new password.\n"
            if must_change
            else ""
        )
        body = (
            f"Hello {display},\n\n"
            "An account has been created for you on the MSR WCA dashboard "
            "(Monthly Statistical Report — West & Central Africa).\n\n"
            f"URL: {url}\n"
            f"Email: {to_email}\n"
            f"Temporary password: {temp_password}\n\n"
            f"{must_line}"
            "Please keep these credentials confidential.\n\n"
            "— DIMA / UNHCR Regional Bureau for West and Central Africa\n"
        )
    else:
        subject = "Votre accès au tableau de bord MSR WCA"
        must_line = (
            "Lors de la première connexion, vous devrez définir un nouveau mot de passe.\n"
            if must_change
            else ""
        )
        body = (
            f"Bonjour {display},\n\n"
            "Un compte a été créé pour vous sur le tableau de bord MSR WCA "
            "(Rapport statistique mensuel — Afrique de l'Ouest et du Centre).\n\n"
            f"URL : {url}\n"
            f"E-mail : {to_email}\n"
            f"Mot de passe temporaire : {temp_password}\n\n"
            f"{must_line}"
            "Merci de conserver ces identifiants de façon confidentielle.\n\n"
            "— DIMA / HCR Bureau régional pour l'Afrique de l'Ouest et du Centre\n"
        )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = str(_smtp_settings()["from_addr"])
    msg["To"] = to_email
    msg.set_content(body)
    return msg


def send_email(msg: EmailMessage) -> str | None:
    """Send ``msg``. Returns an error code, or ``None`` on success."""
    cfg = _smtp_settings()
    if not cfg["host"] or not cfg["user"]:
        return "smtp_not_configured"
    try:
        if cfg["starttls"]:
            context = ssl.create_default_context()
            with smtplib.SMTP(str(cfg["host"]), int(cfg["port"]), timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                if cfg["password"]:
                    server.login(str(cfg["user"]), str(cfg["password"]))
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(str(cfg["host"]), int(cfg["port"]), timeout=30) as server:
                if cfg["password"]:
                    server.login(str(cfg["user"]), str(cfg["password"]))
                server.send_message(msg)
    except Exception:  # noqa: BLE001
        return "smtp_send_failed"
    return None


def send_invite_notification(
    *,
    to_email: str,
    name: str,
    temp_password: str,
    lang: str,
    must_change: bool,
) -> str | None:
    msg = build_invite_email(
        to_email=to_email,
        name=name,
        temp_password=temp_password,
        lang=lang,
        must_change=must_change,
    )
    return send_email(msg)
