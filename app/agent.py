import json
import time

from app.config import MAX_DAILY_APPLICATIONS, MIN_MATCH_SCORE_TO_APPLY
from app.cover_letter import generate_cover_letter
from app.db import get_conn, now_iso
from app.notifier import (
    format_notification_log,
    load_last_notified_application_id,
    notify_all,
    progressed_alert_payload,
    save_last_notified_application_id,
    should_send_cycle_summary,
)
from app.portals.registry import enabled_portals
from app.profile_service import get_profile, get_setting
from app.scoring import preference_score

def load_profile():
    return get_profile()


def persist_job(conn, portal_name: str, job: dict, score: int) -> int:
    conn.execute(
        """
        INSERT OR IGNORE INTO jobs (
            portal, external_id, company, title, location, work_mode, job_type,
            description, apply_url, discovered_at, score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            portal_name,
            job["external_id"],
            job["company"],
            job["title"],
            job["location"],
            job["work_mode"],
            job["job_type"],
            job["description"],
            job["apply_url"],
            now_iso(),
            score,
        ),
    )
    row = conn.execute(
        "SELECT id FROM jobs WHERE portal = ? AND external_id = ?",
        (portal_name, job["external_id"]),
    ).fetchone()
    return row["id"]


def already_applied(conn, job_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM applications WHERE job_id = ? AND status IN ('applied', 'accepted', 'replied', 'shortlisted', 'interview')",
        (job_id,),
    ).fetchone()
    return bool(row)


def already_pending(conn, job_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM applications WHERE job_id = ? AND status IN ('needs_approval', 'approved')",
        (job_id,),
    ).fetchone()
    return bool(row)


def approved_application(conn, job_id: int):
    return conn.execute(
        """
        SELECT id FROM applications
        WHERE job_id = ? AND status = 'approved'
        ORDER BY id DESC
        LIMIT 1
        """,
        (job_id,),
    ).fetchone()


def daily_applied_count(conn) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM applications WHERE date(created_at) = date('now', 'localtime') AND status = 'applied'"
    ).fetchone()
    return int(row["c"])


def daily_applied_count_for_portal(conn, portal_name: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        WHERE date(a.created_at) = date('now', 'localtime')
          AND a.status = 'applied'
          AND j.portal = ?
        """,
        (portal_name,),
    ).fetchone()
    return int(row["c"])


def int_setting(key: str, default: int) -> int:
    raw = get_setting(key, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def float_setting(key: str, default: float) -> float:
    raw = get_setting(key, str(default))
    try:
        return float(raw)
    except ValueError:
        return default


def with_retries(fn, retries: int, base_delay_s: float):
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as exc:
            if attempt > retries:
                raise exc
            time.sleep(base_delay_s * attempt)


def run_cycle() -> None:
    profile = load_profile()
    if not profile:
        print("Profile missing. Run: python3 -m app.intake")
        return

    auto_apply_enabled = get_setting("auto_apply_enabled", "true").lower() == "true"
    fetch_retries = int_setting("fetch_retries", 2)
    apply_retries = int_setting("apply_retries", 2)
    retry_backoff_sec = float_setting("retry_backoff_sec", 2.0)
    portal_daily_limit_default = int_setting("portal_daily_limit_default", 7)
    applied_now = 0
    failed_now = 0
    pending_now = 0
    portal_applied_now = {}
    with get_conn() as conn:
        for portal in enabled_portals():
            portal_limit = int_setting(f"portal_daily_limit_{portal.name}", portal_daily_limit_default)
            try:
                jobs = with_retries(
                    lambda: portal.fetch_jobs(),
                    retries=fetch_retries,
                    base_delay_s=retry_backoff_sec,
                )
            except Exception as fetch_exc:
                conn.execute(
                    "INSERT INTO events (event_type, payload, created_at) VALUES (?, ?, ?)",
                    (
                        "portal_fetch_failed",
                        json.dumps({"portal": portal.name, "error": str(fetch_exc)}),
                        now_iso(),
                    ),
                )
                continue
            for job in jobs:
                score = preference_score(profile, job)
                job_id = persist_job(conn, portal.name, job, score)
                approved_row = approved_application(conn, job_id)
                if already_applied(conn, job_id):
                    continue
                if daily_applied_count(conn) >= MAX_DAILY_APPLICATIONS:
                    break
                if daily_applied_count_for_portal(conn, portal.name) >= portal_limit:
                    break
                if approved_row:
                    cover_letter = generate_cover_letter(profile, job)
                    try:
                        ok, notes = with_retries(
                            lambda: portal.apply(job, dict(profile), cover_letter),
                            retries=apply_retries,
                            base_delay_s=retry_backoff_sec,
                        )
                    except Exception as apply_exc:
                        ok, notes = False, f"Apply error after retries: {apply_exc}"
                    status = "applied" if ok else "failed"
                    conn.execute(
                        """
                        UPDATE applications
                        SET status = ?, cover_letter = ?, notes = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (status, cover_letter, notes, now_iso(), approved_row["id"]),
                    )
                    if ok:
                        applied_now += 1
                        portal_applied_now[portal.name] = portal_applied_now.get(portal.name, 0) + 1
                    else:
                        failed_now += 1
                    continue
                if already_pending(conn, job_id):
                    continue
                if score < MIN_MATCH_SCORE_TO_APPLY or not auto_apply_enabled:
                    conn.execute(
                        """
                        INSERT INTO applications (job_id, status, cover_letter, notes, created_at, updated_at)
                        VALUES (?, 'needs_approval', '', ?, ?, ?)
                        """,
                        (
                            job_id,
                            (
                                f"Low score ({score}). Review before apply."
                                if score < MIN_MATCH_SCORE_TO_APPLY
                                else "Auto-apply disabled. Waiting for approval."
                            ),
                            now_iso(),
                            now_iso(),
                        ),
                    )
                    pending_now += 1
                    continue

                cover_letter = generate_cover_letter(profile, job)
                try:
                    ok, notes = with_retries(
                        lambda: portal.apply(job, dict(profile), cover_letter),
                        retries=apply_retries,
                        base_delay_s=retry_backoff_sec,
                    )
                except Exception as apply_exc:
                    ok, notes = False, f"Apply error after retries: {apply_exc}"
                status = "applied" if ok else "failed"
                conn.execute(
                    """
                    INSERT INTO applications (job_id, status, cover_letter, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (job_id, status, cover_letter, notes, now_iso(), now_iso()),
                )
                if ok:
                    applied_now += 1
                    portal_applied_now[portal.name] = portal_applied_now.get(portal.name, 0) + 1
                else:
                    failed_now += 1

        conn.execute(
            "INSERT INTO events (event_type, payload, created_at) VALUES (?, ?, ?)",
            (
                "cycle_complete",
                json.dumps(
                    {
                        "applied_now": applied_now,
                        "failed_now": failed_now,
                        "pending_now": pending_now,
                        "portal_applied_now": portal_applied_now,
                    }
                ),
                now_iso(),
            ),
        )

        last_notified_id = load_last_notified_application_id()
        progressed_rows = conn.execute(
            """
            SELECT a.id, a.status, j.company, j.title
            FROM applications a
            JOIN jobs j ON j.id = a.job_id
            WHERE a.id > ? AND a.status IN ('replied', 'shortlisted', 'interview', 'accepted')
            ORDER BY a.id ASC
            """,
            (last_notified_id,),
        ).fetchall()
        if progressed_rows:
            progress_body = progressed_alert_payload(progressed_rows)
            progress_results = notify_all("Job Agent: New progress update", progress_body)
            conn.execute(
                "INSERT INTO events (event_type, payload, created_at) VALUES (?, ?, ?)",
                ("notification_progress", format_notification_log(progress_results), now_iso()),
            )
            save_last_notified_application_id(progressed_rows[-1]["id"])

        if should_send_cycle_summary(applied_now, failed_now, pending_now):
            body = (
                f"Cycle completed.\n"
                f"Applied now: {applied_now}\n"
                f"Failed now: {failed_now}\n"
                f"Needs approval now: {pending_now}\n"
                f"Portal breakdown: {json.dumps(portal_applied_now)}"
            )
            summary_results = notify_all("Job Agent: Cycle summary", body)
            conn.execute(
                "INSERT INTO events (event_type, payload, created_at) VALUES (?, ?, ?)",
                ("notification_summary", format_notification_log(summary_results), now_iso()),
            )

    print(f"Cycle complete. Applied now: {applied_now}")


if __name__ == "__main__":
    run_cycle()
