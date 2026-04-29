def generate_cover_letter(profile, job: dict) -> str:
    # Keep tone direct and human, avoid generic AI phrasing.
    return (
        f"Hi Hiring Team,\n\n"
        f"I'm {profile['full_name']}, and I would like to apply for the {job['title']} role at "
        f"{job['company']}. I am interested in this role because it matches my current skill focus "
        f"and the kind of hands-on work I want to contribute to.\n\n"
        f"My background includes: {profile['resume_text']}\n\n"
        f"I can join {profile['join_timeline']}. If shortlisted, I am happy to take an assignment "
        f"or a technical discussion at your convenience.\n\n"
        f"Thank you for your time.\n"
        f"{profile['full_name']}\n"
        f"{profile['email']} | {profile['phone']}"
    )
