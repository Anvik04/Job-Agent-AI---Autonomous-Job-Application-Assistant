import pandas as pd
import streamlit as st
import json

from app.db import get_conn, init_db, now_iso
from app.notifier import format_notification_log, notify_all
from app.profile_service import get_profile, get_setting, set_setting, upsert_profile

init_db()
st.set_page_config(page_title="Job Agent Dashboard", layout="wide")
st.title("Personal Job Agent Dashboard")

profile = get_profile()


def as_int_setting(key: str, default: int) -> int:
    try:
        return int(get_setting(key, str(default)))
    except ValueError:
        return default


def as_float_setting(key: str, default: float) -> float:
    try:
        return float(get_setting(key, str(default)))
    except ValueError:
        return default

with st.sidebar:
    st.header("Agent Settings")
    enabled_default = [
        part.strip()
        for part in get_setting("enabled_portals", "mock_internships,mock_jobs").split(",")
        if part.strip()
    ]
    auto_apply = st.toggle(
        "Auto-apply eligible jobs",
        value=get_setting("auto_apply_enabled", "true").lower() == "true",
    )
    browser_headless = st.toggle(
        "Browser headless mode",
        value=get_setting("browser_headless", "true").lower() == "true",
    )
    fetch_retries = st.number_input("Fetch retries", min_value=0, max_value=6, value=as_int_setting("fetch_retries", 2))
    apply_retries = st.number_input("Apply retries", min_value=0, max_value=6, value=as_int_setting("apply_retries", 2))
    retry_backoff_sec = st.number_input(
        "Retry backoff seconds",
        min_value=1.0,
        max_value=20.0,
        value=as_float_setting("retry_backoff_sec", 2.0),
        step=1.0,
    )
    portal_daily_limit_default = st.number_input(
        "Per-portal daily apply limit (default)",
        min_value=1,
        max_value=50,
        value=as_int_setting("portal_daily_limit_default", 7),
    )
    internshala_daily_limit = st.number_input(
        "Internshala daily apply limit",
        min_value=1,
        max_value=50,
        value=as_int_setting("portal_daily_limit_internshala", 7),
    )
    naukri_daily_limit = st.number_input(
        "Naukri daily apply limit",
        min_value=1,
        max_value=50,
        value=as_int_setting("portal_daily_limit_naukri", 7),
    )
    portals = st.multiselect(
        "Enabled portals",
        ["mock_internships", "mock_jobs", "internshala", "naukri"],
        default=enabled_default or ["mock_internships", "mock_jobs"],
    )
    st.caption("Internshala credentials (stored locally in SQLite)")
    internshala_email = st.text_input("Internshala email", value=get_setting("internshala_email", ""))
    internshala_password = st.text_input(
        "Internshala password",
        value=get_setting("internshala_password", ""),
        type="password",
    )
    st.caption("Naukri credentials (stored locally in SQLite)")
    naukri_email = st.text_input("Naukri email", value=get_setting("naukri_email", ""))
    naukri_password = st.text_input(
        "Naukri password",
        value=get_setting("naukri_password", ""),
        type="password",
    )
    st.divider()
    st.caption("Notifications")
    notify_email_enabled = st.toggle(
        "Email notifications enabled",
        value=get_setting("notify_email_enabled", "false").lower() == "true",
    )
    notify_email_smtp_host = st.text_input("SMTP host", value=get_setting("notify_email_smtp_host", "smtp.gmail.com"))
    notify_email_smtp_port = st.number_input(
        "SMTP port",
        min_value=1,
        max_value=65535,
        value=as_int_setting("notify_email_smtp_port", 587),
    )
    notify_email_smtp_user = st.text_input("SMTP user", value=get_setting("notify_email_smtp_user", ""))
    notify_email_smtp_pass = st.text_input("SMTP password / app password", value=get_setting("notify_email_smtp_pass", ""), type="password")
    notify_email_from = st.text_input("Email from", value=get_setting("notify_email_from", ""))
    notify_email_to = st.text_input("Email to", value=get_setting("notify_email_to", ""))
    notify_email_use_tls = st.toggle(
        "Use STARTTLS",
        value=get_setting("notify_email_use_tls", "true").lower() == "true",
    )
    notify_telegram_enabled = st.toggle(
        "Telegram notifications enabled",
        value=get_setting("notify_telegram_enabled", "false").lower() == "true",
    )
    notify_telegram_bot_token = st.text_input(
        "Telegram bot token",
        value=get_setting("notify_telegram_bot_token", ""),
        type="password",
    )
    notify_telegram_chat_id = st.text_input("Telegram chat id", value=get_setting("notify_telegram_chat_id", ""))
    notify_summary_always = st.toggle(
        "Send summary every cycle",
        value=get_setting("notify_summary_always", "false").lower() == "true",
    )
    if st.button("Send Test Notification"):
        test_subject = "Job Agent: Test notification"
        test_body = (
            "Test alert from your local job agent.\n"
            "If you received this, notification setup is working."
        )
        test_results = notify_all(test_subject, test_body)
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO events (event_type, payload, created_at) VALUES (?, ?, ?)",
                ("notification_test", format_notification_log(test_results), now_iso()),
            )
        if any(result["ok"] for result in test_results):
            st.success(f"Test sent: {test_results}")
        else:
            st.warning(f"Test failed: {test_results}")
    if st.button("Save Settings"):
        set_setting("auto_apply_enabled", str(auto_apply).lower())
        set_setting("browser_headless", str(browser_headless).lower())
        set_setting("enabled_portals", ",".join(portals))
        set_setting("internshala_email", internshala_email)
        set_setting("internshala_password", internshala_password)
        set_setting("naukri_email", naukri_email)
        set_setting("naukri_password", naukri_password)
        set_setting("fetch_retries", str(fetch_retries))
        set_setting("apply_retries", str(apply_retries))
        set_setting("retry_backoff_sec", str(retry_backoff_sec))
        set_setting("portal_daily_limit_default", str(portal_daily_limit_default))
        set_setting("portal_daily_limit_internshala", str(internshala_daily_limit))
        set_setting("portal_daily_limit_naukri", str(naukri_daily_limit))
        set_setting("notify_email_enabled", str(notify_email_enabled).lower())
        set_setting("notify_email_smtp_host", notify_email_smtp_host)
        set_setting("notify_email_smtp_port", str(notify_email_smtp_port))
        set_setting("notify_email_smtp_user", notify_email_smtp_user)
        set_setting("notify_email_smtp_pass", notify_email_smtp_pass)
        set_setting("notify_email_from", notify_email_from)
        set_setting("notify_email_to", notify_email_to)
        set_setting("notify_email_use_tls", str(notify_email_use_tls).lower())
        set_setting("notify_telegram_enabled", str(notify_telegram_enabled).lower())
        set_setting("notify_telegram_bot_token", notify_telegram_bot_token)
        set_setting("notify_telegram_chat_id", notify_telegram_chat_id)
        set_setting("notify_summary_always", str(notify_summary_always).lower())
        st.success("Settings saved.")

st.subheader("Your Profile")
with st.form("profile_form"):
    full_name = st.text_input("Full name", value=profile["full_name"] if profile else "")
    email = st.text_input("Email", value=profile["email"] if profile else "")
    phone = st.text_input("Phone", value=profile["phone"] if profile else "")
    resume_text = st.text_area("Resume summary", value=profile["resume_text"] if profile else "", height=180)
    join_timeline = st.text_input("When can you join?", value=profile["join_timeline"] if profile else "")
    open_to_relocate = st.checkbox(
        "Open to other cities",
        value=bool(profile["open_to_relocate"]) if profile else False,
    )
    international_ok = st.checkbox(
        "Open to international roles",
        value=bool(profile["international_ok"]) if profile else False,
    )
    preferred_locations = st.text_input(
        "Preferred locations (comma separated)",
        value=", ".join(json.loads(profile["preferred_locations"])) if profile and profile["preferred_locations"] else "",
    )
    work_modes = st.text_input(
        "Work modes (comma separated)",
        value=", ".join(json.loads(profile["work_modes"])) if profile and profile["work_modes"] else "",
    )
    job_types = st.text_input(
        "Job types (comma separated)",
        value=", ".join(json.loads(profile["job_types"])) if profile and profile["job_types"] else "",
    )
    if st.form_submit_button("Save Profile"):
        upsert_profile(
            {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "resume_text": resume_text,
                "join_timeline": join_timeline,
                "open_to_relocate": open_to_relocate,
                "international_ok": international_ok,
                "preferred_locations": json.dumps([x.strip() for x in preferred_locations.split(",") if x.strip()]),
                "work_modes": json.dumps([x.strip().lower() for x in work_modes.split(",") if x.strip()]),
                "job_types": json.dumps([x.strip().lower() for x in job_types.split(",") if x.strip()]),
            }
        )
        st.success("Profile saved.")

with get_conn() as conn:
    jobs_df = pd.read_sql_query(
        """
        SELECT
            a.id AS application_id,
            a.job_id,
            j.company,
            j.title,
            j.location,
            j.portal,
            j.score,
            j.apply_url,
            a.status,
            a.notes,
            a.cover_letter,
            a.created_at,
            a.updated_at
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        ORDER BY a.created_at DESC
        """,
        conn,
    )
    daily_digest_df = pd.read_sql_query(
        """
        SELECT
            date(a.created_at) AS day,
            j.portal,
            COUNT(*) AS total_events,
            SUM(CASE WHEN a.status = 'applied' THEN 1 ELSE 0 END) AS applied,
            SUM(CASE WHEN a.status = 'failed' THEN 1 ELSE 0 END) AS failed,
            SUM(CASE WHEN a.status = 'needs_approval' THEN 1 ELSE 0 END) AS needs_approval,
            SUM(CASE WHEN a.status IN ('replied', 'shortlisted', 'interview', 'accepted') THEN 1 ELSE 0 END) AS progressed
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        GROUP BY date(a.created_at), j.portal
        ORDER BY day DESC, j.portal ASC
        LIMIT 60
        """,
        conn,
    )
    notifications_df = pd.read_sql_query(
        """
        SELECT event_type, payload, created_at
        FROM events
        WHERE event_type IN ('notification_progress', 'notification_summary', 'notification_test', 'portal_fetch_failed')
        ORDER BY id DESC
        LIMIT 50
        """,
        conn,
    )

if jobs_df.empty:
    st.info("No applications yet. Save your profile, then run `python3 -m app.agent`.")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(jobs_df))
    c2.metric("Applied", int((jobs_df["status"] == "applied").sum()))
    c3.metric("Needs Approval", int((jobs_df["status"] == "needs_approval").sum()))
    c4.metric("Replied/Progress", int(jobs_df["status"].isin(["replied", "shortlisted", "interview", "accepted"]).sum()))

    st.subheader("Approval Queue")
    approval_df = jobs_df[jobs_df["status"] == "needs_approval"]
    if approval_df.empty:
        st.caption("No pending approvals.")
    else:
        st.dataframe(
            approval_df[["application_id", "company", "title", "location", "portal", "score", "notes", "apply_url"]],
            use_container_width=True,
        )
        approve_id = st.number_input("Approve application ID", min_value=1, step=1, key="approve_id")
        if st.button("Mark Approved"):
            with get_conn() as conn:
                conn.execute(
                    "UPDATE applications SET status = 'approved', updated_at = datetime('now', 'localtime') WHERE id = ?",
                    (int(approve_id),),
                )
            st.success("Marked approved. The next cycle can submit it.")

    st.subheader("Recent updates")
    st.dataframe(
        jobs_df[["application_id", "company", "title", "location", "portal", "score", "status", "notes", "created_at", "updated_at"]],
        use_container_width=True,
    )

    st.subheader("Daily Digest")
    if daily_digest_df.empty:
        st.caption("Digest will appear after application records are created.")
    else:
        st.dataframe(daily_digest_df, use_container_width=True)

    st.subheader("Notification Log")
    if notifications_df.empty:
        st.caption("No notification events yet.")
    else:
        st.dataframe(notifications_df, use_container_width=True)

    st.subheader("Application Details")
    target_id = st.number_input("Application ID", min_value=1, step=1, key="status_id")
    new_status = st.selectbox(
        "Set status",
        ["applied", "replied", "shortlisted", "interview", "accepted", "rejected", "failed"],
    )
    if st.button("Update status"):
        with get_conn() as conn:
            conn.execute(
                "UPDATE applications SET status = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
                (new_status, int(target_id)),
            )
        st.success("Status updated.")
