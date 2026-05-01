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

    title_desc = normalize(job.get("title", "")) + " " + normalize(job.get("description", ""))
    if "conference" in title_desc or "meeting" in title_desc:
        return -1000  # Strictly exclude conferences and meetings

    score = 0
    if normalize(job["location"]) in {normalize(x) for x in preferred_locations}:
        score += 20
    if normalize(job["work_mode"]) in {normalize(x) for x in work_modes}:
        score += 20
        
    # Strictly prefer internships
    if normalize(job["job_type"]) == "internship" or "intern" in title_desc:
        score += 40
    else:
        return -1000 # Only apply for internships

    score += location_opportunity_score(job["location"])
    return score
