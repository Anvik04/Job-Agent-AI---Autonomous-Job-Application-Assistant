from app.portals.internshala_portal import InternshalaPortal
from app.portals.mock_portals import MockInternshipPortal, MockJobsPortal
from app.portals.naukri_portal import NaukriPortal
from app.profile_service import get_setting


def enabled_portals():
    enabled = {
        part.strip().lower()
        for part in get_setting("enabled_portals", "mock_internships,mock_jobs").split(",")
        if part.strip()
    }

    all_portals = [
        MockInternshipPortal(),
        MockJobsPortal(),
        InternshalaPortal(),
        NaukriPortal(),
    ]
    return [portal for portal in all_portals if portal.name in enabled]
