from typing import List, Dict


class BasePortal:
    name = "base"

    def fetch_jobs(self) -> List[Dict]:
        raise NotImplementedError

    def apply(self, job: Dict, profile: dict, cover_letter: str) -> tuple[bool, str]:
        """
        Return (success, notes). Replace with browser automation per portal.
        """
        return True, "Application submitted in MVP mode (replace with real portal logic)."
