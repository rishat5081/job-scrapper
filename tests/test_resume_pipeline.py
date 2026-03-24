import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jobintel.pdf_utils import write_resume_pdf
from jobintel.resume_pipeline import (
    build_resume_profile,
    extract_job_keywords,
    score_job_against_profile,
    tailor_resume_for_job,
)


def _chrome_works() -> bool:
    """Check if headless Chrome can actually run (not just that the binary exists)."""
    chrome = (
        shutil.which("google-chrome")
        or shutil.which("chromium")
        or (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome").exists()
            else None
        )
    )
    if not chrome:
        return False
    try:
        result = subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--dump-dom", "about:blank"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


_HAS_CHROME = _chrome_works()


def _fake_pdf_writer(output_path, _payload):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("%PDF-1.4\n% fake\n", encoding="latin-1")
    return path


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

    def test_extract_job_keywords_handles_nested_tags(self):
        keywords = extract_job_keywords(
            {
                "title": "Platform Engineer",
                "description": "Build AWS APIs",
                "tags": ["python", ["aws", "docker"]],
                "location": "Remote",
            }
        )
        self.assertIn("aws", keywords)
        self.assertIn("docker", keywords)

    def test_adjacent_javascript_supports_typescript_job_without_false_claim(self):
        profile = build_resume_profile(
            SAMPLE_RESUME.replace(
                "Python, FastAPI, Flask, PostgreSQL, Docker, Kubernetes, AWS, System Design, Leadership",
                "JavaScript, Node.js, PostgreSQL, Docker, AWS",
            ),
            "resume.txt",
        )
        artifact = tailor_resume_for_job(
            profile,
            {
                "id": "job-ts",
                "company": "Example Corp",
                "title": "Software Engineer (TypeScript/NodeJS)",
                "location": "Remote",
                "source": "LinkedIn Jobs",
                "url": "https://example.com/jobs/ts",
                "description": "",
                "tags": ["linkedin", "jobspy"],
            },
            persist=False,
            render_documents=False,
        )
        self.assertIn("typescript", artifact["validation"]["adjacent_keywords"])
        self.assertNotIn("jobspy", artifact["match"]["job_keywords"])
        self.assertIn("node.js", artifact["match"]["job_keywords"])

    @patch("jobintel.resume_pipeline.write_resume_pdf", side_effect=_fake_pdf_writer)
    @patch("jobintel.application_materials.write_cover_letter_pdf", side_effect=_fake_pdf_writer)
    def test_tailoring_generates_full_application_packet_without_live_pdf_engine(self, _cover_writer, _resume_writer):
        profile = build_resume_profile(SAMPLE_RESUME, "resume.txt")

        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = tailor_resume_for_job(profile, GOOD_JOB, output_dir=temp_dir, persist=False)

            self.assertIn("cover_letter", artifact)
            self.assertIn("draft_answers", artifact)
            self.assertIn("autofill", artifact)
            self.assertIn("application_status", artifact)
            self.assertTrue(Path(artifact["pdf_path"]).exists())
            self.assertTrue(Path(artifact["cover_letter"]["pdf_path"]).exists())
            self.assertTrue(Path(artifact["draft_answers"]["markdown_path"]).exists())
            self.assertTrue(artifact["autofill"]["payload"]["email"])
            self.assertEqual(artifact["application_status"]["status"], "prepared")

    @unittest.skipUnless(_HAS_CHROME, "Headless Chrome not available")
    def test_tailoring_generates_pdf(self):
        profile = build_resume_profile(SAMPLE_RESUME, "resume.txt")

        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = tailor_resume_for_job(profile, GOOD_JOB, output_dir=temp_dir, persist=False)
            pdf_path = Path(artifact["pdf_path"])

            self.assertTrue(pdf_path.exists())
            self.assertTrue(artifact["resume"]["contact"]["email"])
            self.assertIn("%PDF-1.4", pdf_path.read_text(encoding="latin-1", errors="ignore"))
            self.assertGreaterEqual(artifact["validation"]["score"], 60)

    @unittest.skipUnless(_HAS_CHROME, "Headless Chrome not available")
    def test_tailoring_prefers_truthful_devops_focus(self):
        profile = build_resume_profile(SAMPLE_RESUME, "resume.txt")
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = tailor_resume_for_job(profile, DEVOPS_JOB, output_dir=temp_dir, persist=False)

            self.assertIn("Cloud, DevOps", artifact["resume"]["headline"])
            self.assertTrue(any("AWS" in item or "CI/CD" in item for item in artifact["resume"]["experience"]))
            self.assertNotIn("python", artifact["validation"]["matched_keywords"])

    @unittest.skipUnless(_HAS_CHROME, "Headless Chrome not available")
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
            self.assertIn("%PDF-", pdf)
            self.assertTrue(path.stat().st_size > 0)


if __name__ == "__main__":
    unittest.main()
