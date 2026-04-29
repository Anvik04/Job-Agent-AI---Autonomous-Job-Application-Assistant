from app.portals.base import BasePortal


class MockInternshipPortal(BasePortal):
    name = "mock_internships"

    def fetch_jobs(self):
        return [
            {
                "external_id": "m1",
                "company": "Nova Labs",
                "title": "Python Intern",
                "location": "Mysuru",
                "work_mode": "hybrid",
                "job_type": "internship",
                "description": "Python + APIs + debugging.",
                "apply_url": "https://example.com/m1",
            },
            {
                "external_id": "m2",
                "company": "DataSpring",
                "title": "ML Intern",
                "location": "Bengaluru",
                "work_mode": "online",
                "job_type": "internship",
                "description": "ML experimentation and model evaluation.",
                "apply_url": "https://example.com/m2",
            },
        ]


class MockJobsPortal(BasePortal):
    name = "mock_jobs"

    def fetch_jobs(self):
        return [
            {
                "external_id": "j1",
                "company": "RuralTech Systems",
                "title": "Junior Python Developer",
                "location": "Coimbatore",
                "work_mode": "offline",
                "job_type": "full-time",
                "description": "Build backend tools and internal dashboards.",
                "apply_url": "https://example.com/j1",
            }
        ]
