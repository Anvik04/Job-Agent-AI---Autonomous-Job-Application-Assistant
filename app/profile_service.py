import json

from app.db import get_conn, now_iso


PROFILE_FIELDS = {
    "full_name": "",
    "email": "",
    "phone": "",
    "resume_text": "",
    "join_timeline": "",
    "open_to_relocate": 0,
    "preferred_locations": "[]",
    "work_modes": "[]",
    "job_types": "[]",
    "international_ok": 0,
}


def normalize_list(raw: str) -> str:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return json.dumps(values)


def get_profile():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()


def upsert_profile(data: dict) -> None:
    payload = PROFILE_FIELDS | data
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO profile (
                id, full_name, email, phone, resume_text, join_timeline,
                open_to_relocate, preferred_locations, work_modes, job_types,
                international_ok, updated_at
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                full_name = excluded.full_name,
                email = excluded.email,
                phone = excluded.phone,
                resume_text = excluded.resume_text,
                join_timeline = excluded.join_timeline,
                open_to_relocate = excluded.open_to_relocate,
                preferred_locations = excluded.preferred_locations,
                work_modes = excluded.work_modes,
                job_types = excluded.job_types,
                international_ok = excluded.international_ok,
                updated_at = excluded.updated_at
            """,
            (
                payload["full_name"],
                payload["email"],
                payload["phone"],
                payload["resume_text"],
                payload["join_timeline"],
                int(bool(payload["open_to_relocate"])),
                payload["preferred_locations"],
                payload["work_modes"],
                payload["job_types"],
                int(bool(payload["international_ok"])),
                now_iso(),
            ),
        )


def get_setting(key: str, default: str = "") -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, now_iso()),
        )
