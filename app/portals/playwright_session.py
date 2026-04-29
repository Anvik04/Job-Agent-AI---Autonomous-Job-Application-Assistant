from pathlib import Path

from app.config import DATA_DIR
from app.profile_service import get_setting


def session_file_for(portal_name: str) -> Path:
    custom = get_setting(f"{portal_name}_session_file", "")
    if custom.strip():
        return Path(custom).expanduser()
    return DATA_DIR / f"{portal_name}_session.json"
