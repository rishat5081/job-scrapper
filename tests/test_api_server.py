"""Tests for api_server.py Flask endpoints."""

import json
from io import BytesIO
import unittest
from unittest.mock import patch

from jobintel.api_server import app


class TestAPIServer(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "ok")

    def test_sources_endpoint(self):
        response = self.client.get("/api/sources")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("sources", data)
        self.assertIsInstance(data["sources"], list)
        self.assertGreaterEqual(len(data["sources"]), 14)
        self.assertIn("last_scrape", data)

    def test_profile_endpoint_no_profile(self):
        with patch("jobintel.api_server.load_resume_profile", return_value=None):
            response = self.client.get("/api/profile")
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data["success"])
            self.assertIsNone(data["profile"])

    def test_stats_endpoint(self):
        response = self.client.get("/api/stats")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("stats", data)
        stats = data["stats"]
        self.assertIn("jobs_scraped", stats)
        self.assertIn("sources_in_catalog", stats)
        self.assertIn("strong_matches", stats)
        self.assertIn("generated_resumes", stats)
        self.assertIn("has_profile", stats)
        self.assertIn("jobs_by_source", stats)

    def test_scraped_jobs_endpoint(self):
        response = self.client.get("/api/scraped-jobs")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("jobs", data)
        self.assertIn("total", data)

    def test_scraped_jobs_with_pagination(self):
        response = self.client.get("/api/scraped-jobs?page=1&per_page=5")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("page", data)
        self.assertIn("per_page", data)
        self.assertIn("total_pages", data)

    def test_scraped_jobs_with_search(self):
        response = self.client.get("/api/scraped-jobs?search=python")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])

    def test_scraped_jobs_with_advanced_filters(self):
        response = self.client.get(
            "/api/scraped-jobs?"
            "salary_min=50000&salary_max=200000"
            "&experience_level=senior"
            "&date_posted=week"
            "&job_type=Full-time"
            "&skills=python,aws"
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])

    def test_filter_options_endpoint(self):
        response = self.client.get("/api/filter-options")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("tags", data)
        self.assertIn("job_types", data)
        self.assertIn("sources", data)
        self.assertIn("experience_levels", data)
        self.assertIn("date_ranges", data)
        self.assertIsInstance(data["tags"], list)
        self.assertEqual(data["experience_levels"], ["junior", "mid", "senior", "lead"])
        self.assertEqual(data["date_ranges"], ["today", "3days", "week", "month"])

    def test_matches_without_profile(self):
        with patch("jobintel.api_server.load_resume_profile", return_value=None):
            response = self.client.get("/api/matches")
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 412)
            self.assertFalse(data["success"])

    def test_tailor_without_profile(self):
        with patch("jobintel.api_server.load_resume_profile", return_value=None):
            response = self.client.post("/api/jobs/test-job/tailor")
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 412)
            self.assertFalse(data["success"])

    def test_pipeline_run_without_profile(self):
        with patch("jobintel.api_server.load_resume_profile", return_value=None):
            response = self.client.post(
                "/api/pipeline/run",
                data=json.dumps({"limit": 3}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 412)

    def test_generated_resumes_endpoint(self):
        response = self.client.get("/api/generated-resumes")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["success"])
        self.assertIn("artifacts", data)

    def test_generated_resumes_public_view_includes_packet_urls(self):
        sample_artifact = {
            "job_id": "job-1",
            "company": "Example Corp",
            "title": "Backend Engineer",
            "location": "Remote",
            "source": "Remotive",
            "url": "https://example.com/jobs/1",
            "pdf_filename": "job-1.pdf",
            "validation": {
                "score": 88,
                "fit_label": "strong_alignment",
                "matched_keywords": [],
                "issues": [],
                "warnings": [],
            },
            "match": {"score": 91},
            "cover_letter": {"pdf_filename": "job-1_cover_letter.pdf", "markdown_filename": "job-1_cover_letter.md"},
            "draft_answers": {
                "markdown_filename": "job-1_draft_answers.md",
                "json_filename": "job-1_draft_answers.json",
            },
        }
        with patch("jobintel.api_server.load_tailored_resumes", return_value=[sample_artifact]):
            response = self.client.get("/api/generated-resumes")
            data = json.loads(response.data)
            artifact = data["artifacts"][0]
            self.assertEqual(response.status_code, 200)
            self.assertEqual(artifact["download_url"], "/api/generated-resumes/job-1.pdf")
            self.assertEqual(artifact["cover_letter"]["pdf_url"], "/api/generated-files/job-1_cover_letter.pdf")
            self.assertEqual(artifact["draft_answers"]["markdown_url"], "/api/generated-files/job-1_draft_answers.md")

    def test_download_nonexistent_resume(self):
        response = self.client.get("/api/generated-resumes/nonexistent.pdf")
        self.assertEqual(response.status_code, 404)

    def test_download_nonexistent_generated_file(self):
        response = self.client.get("/api/generated-files/nonexistent.md")
        self.assertEqual(response.status_code, 404)

    def test_application_status_update_endpoint(self):
        with patch(
            "jobintel.api_server.upsert_application_status",
            return_value={"status": "applied", "notes": "", "updated_at": "2026-03-20T00:00:00Z"},
        ):
            response = self.client.post(
                "/api/jobs/job-1/status",
                data=json.dumps({"status": "applied"}),
                content_type="application/json",
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data["success"])
            self.assertEqual(data["status"]["status"], "applied")

    def test_application_status_rejects_invalid_values(self):
        response = self.client.post(
            "/api/jobs/job-1/status",
            data=json.dumps({"status": "not_real"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_autofill_without_profile(self):
        with patch("jobintel.api_server.load_resume_profile", return_value=None):
            response = self.client.post("/api/jobs/test-job/autofill")
            self.assertEqual(response.status_code, 412)

    def test_upload_without_file(self):
        response = self.client.post("/api/profile/upload")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])

    def test_upload_returns_json_error_when_resume_parsing_fails(self):
        with patch("jobintel.api_server.extract_resume_text", side_effect=ValueError("Could not parse resume.")):
            response = self.client.post(
                "/api/profile/upload",
                data={"resume": (BytesIO(b"%PDF-1.4 fake"), "resume.pdf")},
                content_type="multipart/form-data",
            )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Could not parse resume.")

    def test_cors_headers(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "*")

    def test_index_serves_dashboard(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"JobIntel", response.data)


if __name__ == "__main__":
    unittest.main()
