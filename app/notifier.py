import json
import smtplib
import ssl
from email.message import EmailMessage
from urllib import parse, request

from app.profile_service import get_setting, set_setting


def _is_true(key: str, default: str = "false") -> bool:
    return get_setting(key, default).lower() == "true"


def send_email(subject: str, body: str) -> tuple[bool, str]:
    if not _is_true("notify_email_enabled"):
        return False, "Email notifications disabled."
    smtp_host = get_setting("notify_email_smtp_host", "")
    smtp_port = int(get_setting("notify_email_smtp_port", "587"))
    smtp_user = get_setting("notify_email_smtp_user", "")
    smtp_pass = get_setting("notify_email_smtp_pass", "")
    to_email = get_setting("notify_email_to", "")
    from_email = get_setting("notify_email_from", smtp_user)
    use_tls = _is_true("notify_email_use_tls", "true")

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass, to_email, from_email]):
        return False, "Email settings incomplete."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)

    try:
        if use_tls:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        return True, "Email sent."
    except Exception as exc:
        return False, f"Email send failed: {exc}"


def send_telegram(message: str) -> tuple[bool, str]:
    if not _is_true("notify_telegram_enabled"):
        return False, "Telegram notifications disabled."
    token = get_setting("notify_telegram_bot_token", "")
    chat_id = get_setting("notify_telegram_chat_id", "")
    if not token or not chat_id:
        return False, "Telegram settings incomplete."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = parse.urlencode({"chat_id": chat_id, "text": message[:3900]}).encode()
    req = request.Request(url=url, data=data, method="POST")
    try:
        with request.urlopen(req, timeout=20) as resp:
            if resp.status >= 300:
                return False, f"Telegram send failed with status {resp.status}"
        return True, "Telegram sent."
    except Exception as exc:
        return False, f"Telegram send failed: {exc}"


def notify_all(subject: str, body: str) -> list[dict]:
    results = []
    ok_email, note_email = send_email(subject, body)
    results.append({"channel": "email", "ok": ok_email, "note": note_email})
    ok_telegram, note_telegram = send_telegram(f"{subject}\n\n{body}")
    results.append({"channel": "telegram", "ok": ok_telegram, "note": note_telegram})
    return results


def progressed_alert_payload(rows) -> str:
    lines = ["New progress updates:"]
    for row in rows:
        lines.append(f"- {row['company']} | {row['title']} | status={row['status']}")
    return "\n".join(lines)


def should_send_cycle_summary(applied_now: int, failed_now: int, pending_now: int) -> bool:
    if _is_true("notify_summary_always", "false"):
        return True
    return applied_now > 0 or failed_now > 0 or pending_now > 0


def save_last_notified_application_id(app_id: int) -> None:
    set_setting("last_notified_application_id", str(app_id))


def load_last_notified_application_id() -> int:
    try:
        return int(get_setting("last_notified_application_id", "0"))
    except ValueError:
        return 0


def format_notification_log(results: list[dict]) -> str:
    return json.dumps(results)
