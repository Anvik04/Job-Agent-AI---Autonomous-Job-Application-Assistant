import json


LESS_CROWDED_LOCATIONS = {
    "mysuru": 20,
    "coimbatore": 18,
    "bhubaneswar": 17,
    "indore": 16,
    "trichy": 16,
    "nagpur": 15,
    "vizag": 15,
    "surat": 14,
    "jaipur": 13,
}


def normalize(text: str) -> str:
    return (text or "").strip().lower()


def location_opportunity_score(location: str) -> int:
    city = normalize(location).split(",")[0]
    return LESS_CROWDED_LOCATIONS.get(city, 8)


def preference_score(profile_row, job: dict) -> int:
    preferred_locations = json.loads(profile_row["preferred_locations"] or "[]")
    work_modes = json.loads(profile_row["work_modes"] or "[]")
    job_types = json.loads(profile_row["job_types"] or "[]")

    score = 0
    if normalize(job["location"]) in {normalize(x) for x in preferred_locations}:
        score += 20
    if normalize(job["work_mode"]) in {normalize(x) for x in work_modes}:
        score += 20
    if normalize(job["job_type"]) in {normalize(x) for x in job_types}:
        score += 20
    score += location_opportunity_score(job["location"])
    return score
