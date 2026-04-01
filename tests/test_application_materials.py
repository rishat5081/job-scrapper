import unittest

from jobintel.application_materials import build_cover_letter, validate_application_packet


PROFILE = {
    "name": "Jane Engineer",
    "summary": "Backend engineer delivering Python services, APIs, and cloud deployments for product teams.",
    "projects": ["Created an internal analytics platform using Python, SQL, and ETL workflows."],
    "contact": {
        "email": "jane@example.com",
        "phone": "+31 600000000",
        "linkedin": "https://www.linkedin.com/in/jane-engineer",
    },
}

JOB = {
    "id": "job-good",
    "company": "Example Corp",
    "title": "Senior Python Platform Engineer",
    "location": "Remote",
    "source": "Remotive",
    "url": "https://example.com/jobs/1",
}

ARTIFACT = {
    "company": "Example Corp",
    "title": "Senior Python Platform Engineer",
    "resume": {
        "summary": PROFILE["summary"],
        "skills": ["Python", "AWS", "Docker"],
        "experience": [
            "Led migration of a monolith into Python microservices with REST APIs and PostgreSQL.",
            "Built CI/CD pipelines, Docker images, and Kubernetes deployments on AWS.",
        ],
        "work_history": [],
    },
    "match": {
        "family_supported_terms": ["python", "aws"],
        "matched_keywords": ["python", "docker"],
        "evidenced_keywords": ["aws"],
    },
}


class ApplicationMaterialsTests(unittest.TestCase):
    def test_cover_letter_uses_role_company_and_resume_evidence(self):
        text = build_cover_letter(PROFILE, JOB, ARTIFACT)

        self.assertIn("Example Corp", text)
        self.assertIn("Senior Python Platform Engineer", text)
        self.assertIn("Led migration of a monolith into Python microservices", text)

    def test_packet_validation_requires_resume_backed_evidence(self):
        packet = {
            "cover_letter": {
                "text": (
                    "Dear Hiring Team at Example Corp,\n\n"
                    "I am applying for the Senior Python Platform Engineer role because it looks exciting.\n\n"
                    "Sincerely,\nJane Engineer"
                )
            },
            "draft_answers": {
                "items": [
                    {"question": "Why are you interested in this role?", "answer": "I like Python and AWS engineering work."},
                    {"question": "Why are you interested in this company?", "answer": "The company seems like a good fit."},
                    {"question": "Summarize your most relevant experience.", "answer": "I have backend experience."},
                    {"question": "What should we know before reviewing your application?", "answer": "I care about quality."},
                ]
            },
        }

        validation = validate_application_packet(JOB, ARTIFACT, packet)

        self.assertIn("Cover letter does not include resume-backed evidence for the claimed fit.", validation["issues"])


if __name__ == "__main__":
    unittest.main()
