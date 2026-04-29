import json

from app.db import get_conn, now_iso


def ask(prompt: str) -> str:
    return input(f"{prompt}: ").strip()


def run_intake() -> None:
    print("\n--- Job Agent Profile Intake ---")
    print("Enter details once; you can rerun anytime.\n")

    full_name = ask("Full name")
    email = ask("Email")
    phone = ask("Phone")
    print("\nPaste a short resume summary (skills, projects, experience).")
    resume_text = ask("Resume text")
    join_timeline = ask("When can you join? (immediate/15 days/1 month/etc)")
    open_to_relocate = ask("Open to other cities? (yes/no)").lower() == "yes"
    preferred_locations = ask("Preferred locations (comma separated)")
    work_modes = ask("Work mode preferences (online/offline/hybrid, comma separated)")
    job_types = ask("Job type preferences (internship/full-time/part-time, comma separated)")
    international_ok = ask("Open to international roles? (yes/no)").lower() == "yes"

    with get_conn() as conn:
        conn.execute("DELETE FROM profile WHERE id = 1")
        conn.execute(
            """
            INSERT INTO profile (
                id, full_name, email, phone, resume_text, join_timeline,
                open_to_relocate, preferred_locations, work_modes, job_types,
                international_ok, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                full_name,
                email,
                phone,
                resume_text,
                join_timeline,
                int(open_to_relocate),
                json.dumps([x.strip() for x in preferred_locations.split(",") if x.strip()]),
                json.dumps([x.strip().lower() for x in work_modes.split(",") if x.strip()]),
                json.dumps([x.strip().lower() for x in job_types.split(",") if x.strip()]),
                int(international_ok),
                now_iso(),
            ),
        )
    print("\nProfile saved.")


if __name__ == "__main__":
    run_intake()
