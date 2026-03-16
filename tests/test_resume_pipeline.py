import re
import tempfile
import unittest
from pathlib import Path

from pdf_utils import write_resume_pdf
from resume_pipeline import build_resume_profile, score_job_against_profile, tailor_resume_for_job


SAMPLE_RESUME = """
Jane Engineer
Senior Backend Engineer
jane@example.com | +31 600000000 | https://www.linkedin.com/in/jane-engineer | Amsterdam

Summary
Backend engineer delivering Python services, APIs, distributed systems, and cloud deployments for product teams.

Skills
Python, FastAPI, Flask, PostgreSQL, Docker, Kubernetes, AWS, System Design, Leadership

Experience
- Led migration of a monolith into Python microservices with REST APIs and PostgreSQL.
- Built CI/CD pipelines, Docker images, and Kubernetes deployments on AWS.
- Mentored engineers and partnered with product teams on architecture decisions.

Projects
- Created an internal analytics platform using Python, SQL, and ETL workflows.

Education
- BSc Computer Science
"""


GOOD_JOB = {
    "id": "job-good",
    "company": "Example Corp",
    "title": "Senior Python Platform Engineer",
    "location": "Netherlands",
    "source": "Remotive",
    "url": "https://example.com/jobs/1",
    "description": "Build Python APIs, Docker services, Kubernetes workloads, PostgreSQL data paths, and AWS infrastructure.",
    "tags": ["python", "kubernetes", "aws"],
}


WEAK_JOB = {
    "id": "job-weak",
    "company": "Example Corp",
    "title": "Senior Sales Manager",
    "location": "Netherlands",
    "source": "Remotive",
    "url": "https://example.com/jobs/2",
    "description": "Own pipeline forecasting, quota attainment, territory planning, and enterprise account expansion.",
    "tags": ["sales", "quotas", "forecasting"],
}

DEVOPS_JOB = {
    "id": "job-devops",
    "company": "Cloud Corp",
    "title": "Senior DevOps Engineer",
    "location": "Remote",
    "source": "Remotive",
    "url": "https://example.com/jobs/3",
    "description": "Own AWS infrastructure, CI/CD pipelines, deployment automation, observability, and platform reliability.",
    "tags": ["aws", "ci/cd", "devops", "platform"],
}


class ResumePipelineTests(unittest.TestCase):
    def test_build_resume_profile_extracts_core_fields(self):
        profile = build_resume_profile(SAMPLE_RESUME, "resume.txt")

        self.assertEqual(profile["name"], "Jane Engineer")
        self.assertEqual(profile["contact"]["email"], "jane@example.com")
        self.assertIn("Python", profile["skills"])
        self.assertGreaterEqual(len(profile["experience"]), 3)

    def test_score_prefers_aligned_engineering_job(self):
        profile = build_resume_profile(SAMPLE_RESUME, "resume.txt")
        strong = score_job_against_profile(profile, GOOD_JOB)
        weak = score_job_against_profile(profile, WEAK_JOB)

        self.assertGreater(strong["score"], weak["score"])
        self.assertIn("python", strong["matched_keywords"])

    def test_tailoring_generates_pdf(self):
        profile = build_resume_profile(SAMPLE_RESUME, "resume.txt")

        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = tailor_resume_for_job(profile, GOOD_JOB, output_dir=temp_dir, persist=False)
            pdf_path = Path(artifact["pdf_path"])

            self.assertTrue(pdf_path.exists())
            self.assertTrue(artifact["resume"]["contact"]["email"])
            self.assertIn("%PDF-1.4", pdf_path.read_text(encoding="latin-1", errors="ignore"))
            self.assertGreaterEqual(artifact["validation"]["score"], 60)

    def test_tailoring_prefers_truthful_devops_focus(self):
        profile = build_resume_profile(SAMPLE_RESUME, "resume.txt")
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = tailor_resume_for_job(profile, DEVOPS_JOB, output_dir=temp_dir, persist=False)

            self.assertIn("Cloud, DevOps", artifact["resume"]["headline"])
            self.assertTrue(any("AWS" in item or "CI/CD" in item for item in artifact["resume"]["experience"]))
            self.assertNotIn("python", artifact["validation"]["matched_keywords"])

    def test_pdf_writer_links_pages_correctly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_resume_pdf(
                Path(temp_dir) / "sample.pdf",
                {
                    "name": "Jane Engineer",
                    "headline": "Senior Software Engineer",
                    "contact": {"email": "jane@example.com"},
                    "summary": "Example summary for PDF validation.",
                    "target_role": "Backend Engineer",
                    "skills": ["Node.js", "AWS", "React"],
                    "experience": ["Built APIs", "Owned cloud deployments", "Improved CI/CD pipelines"],
                    "projects": [],
                    "education": [],
                    "certifications": [],
                },
            )
            pdf = path.read_text(encoding="latin-1", errors="ignore")
            pages_match = re.search(r"(\d+) 0 obj\n<< /Type /Pages ", pdf)
            self.assertIsNotNone(pages_match)
            self.assertIn(f"/Parent {pages_match.group(1)} 0 R", pdf)


if __name__ == "__main__":
    unittest.main()
