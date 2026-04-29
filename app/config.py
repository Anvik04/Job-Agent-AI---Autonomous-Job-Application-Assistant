from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "job_agent.db"

SCHEDULE_HOURS = [10, 22]
TIMEZONE = "Asia/Kolkata"

MAX_DAILY_APPLICATIONS = 20
MIN_MATCH_SCORE_TO_APPLY = 60
