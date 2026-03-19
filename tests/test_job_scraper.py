"""Tests for job_scraper.py - filters, parsers, helpers, and scraper registry."""

import unittest
from datetime import UTC, datetime, timedelta

from job_scraper import (
    SCRAPERS,
    filter_jobs,
    generate_job_id,
    infer_experience_level,
    normalize_job,
    normalize_location,
    parse_salary_range,
)


class TestNormalizeLocation(unittest.TestCase):
    def test_empty_returns_default(self):
        loc, policy = normalize_location("")
        self.assertEqual(loc, "Remote")
        self.assertEqual(policy, "remote")

    def test_remote_keyword(self):
        _loc, policy = normalize_location("Remote (Worldwide)")
        self.assertEqual(policy, "remote")

    def test_anywhere_keyword(self):
        _loc, policy = normalize_location("Anywhere")
        self.assertEqual(policy, "remote")

    def test_hybrid(self):
        _loc, policy = normalize_location("Hybrid - New York")
        self.assertEqual(policy, "hybrid")

    def test_onsite(self):
        _loc, policy = normalize_location("San Francisco, CA")
        self.assertEqual(policy, "onsite")


class TestGenerateJobId(unittest.TestCase):
    def test_deterministic(self):
        id1 = generate_job_id("Acme", "Dev", "Remote", "remotive")
        id2 = generate_job_id("Acme", "Dev", "Remote", "remotive")
        self.assertEqual(id1, id2)

    def test_different_sources_different_ids(self):
        id1 = generate_job_id("Acme", "Dev", "Remote", "remotive")
        id2 = generate_job_id("Acme", "Dev", "Remote", "linkedin")
        self.assertNotEqual(id1, id2)

    def test_special_chars_stripped(self):
        job_id = generate_job_id("Acme & Co.", "Sr. Dev!", "NYC", "test")
        self.assertNotIn("&", job_id)
        self.assertNotIn("!", job_id)
        self.assertNotIn(".", job_id)


class TestNormalizeJob(unittest.TestCase):
    def test_returns_required_fields(self):
        job = normalize_job(
            "remotive",
            "Acme",
            "Software Engineer",
            "Remote",
            "https://example.com",
            "A job description.",
            "$100k",
            "Full-time",
            "2026-01-01",
            ["python"],
        )
        self.assertIn("id", job)
        self.assertIn("company", job)
        self.assertIn("title", job)
        self.assertIn("location", job)
        self.assertIn("url", job)
        self.assertIn("source", job)
        self.assertIn("source_key", job)
        self.assertIn("salary", job)
        self.assertIn("date_posted", job)
        self.assertIn("date_scraped", job)
        self.assertIn("tags", job)
        self.assertIn("compliance", job)
        self.assertEqual(job["source_key"], "remotive")

    def test_missing_salary_defaults(self):
        job = normalize_job("remotive", "X", "Y", "Z", "", "", "", "", "", [])
        self.assertEqual(job["salary"], "Not specified")

    def test_compliance_for_enabled_source(self):
        job = normalize_job("remotive", "X", "Y", "Z", "", "", "", "", "", [])
        self.assertTrue(job["compliance"]["automation_allowed"])


class TestParseSalaryRange(unittest.TestCase):
    def test_not_specified(self):
        self.assertEqual(parse_salary_range("Not specified"), (None, None))

    def test_empty(self):
        self.assertEqual(parse_salary_range(""), (None, None))

    def test_none(self):
        self.assertEqual(parse_salary_range(None), (None, None))

    def test_k_format(self):
        s_min, s_max = parse_salary_range("$30k-$50k")
        self.assertEqual(s_min, 30000)
        self.assertEqual(s_max, 50000)

    def test_full_number_format(self):
        s_min, s_max = parse_salary_range("$30000-$50000")
        self.assertEqual(s_min, 30000)
        self.assertEqual(s_max, 50000)

    def test_hourly_format(self):
        s_min, s_max = parse_salary_range("$90/hr")
        expected = 90 * 2080
        self.assertEqual(s_min, expected)
        self.assertEqual(s_max, expected)

    def test_single_k_value(self):
        s_min, s_max = parse_salary_range("$100k")
        self.assertEqual(s_min, 100000)
        self.assertEqual(s_max, 100000)

    def test_eur_format(self):
        s_min, s_max = parse_salary_range("EUR30k-EUR50k")
        self.assertEqual(s_min, 30000)
        self.assertEqual(s_max, 50000)

    def test_comma_separated(self):
        s_min, s_max = parse_salary_range("$100,000-$150,000")
        self.assertEqual(s_min, 100000)
        self.assertEqual(s_max, 150000)


class TestInferExperienceLevel(unittest.TestCase):
    def test_senior(self):
        self.assertEqual(infer_experience_level("Senior Software Engineer"), "senior")

    def test_junior(self):
        self.assertEqual(infer_experience_level("Junior Developer"), "junior")

    def test_lead(self):
        self.assertEqual(infer_experience_level("Staff Engineer"), "lead")

    def test_principal(self):
        self.assertEqual(infer_experience_level("Principal Architect"), "lead")

    def test_mid_default(self):
        self.assertEqual(infer_experience_level("Software Engineer"), "mid")

    def test_sr_abbreviation(self):
        self.assertEqual(infer_experience_level("Sr. Backend Dev"), "senior")

    def test_intern(self):
        self.assertEqual(infer_experience_level("Engineering Intern"), "junior")

    def test_description_override(self):
        self.assertEqual(
            infer_experience_level("Engineer", "Looking for a senior developer"),
            "senior",
        )


class TestFilterJobs(unittest.TestCase):
    def setUp(self):
        now = datetime.now(UTC)
        self.jobs = [
            {
                "id": "1",
                "title": "Senior Python Engineer",
                "company": "Acme",
                "location": "Remote",
                "remote_policy": "remote",
                "source_key": "remotive",
                "description": "Build APIs with Python and Django",
                "tags": ["python", "django"],
                "salary": "$120k-$160k",
                "job_type": "Full-time",
                "date_posted": now.isoformat().replace("+00:00", "Z"),
            },
            {
                "id": "2",
                "title": "Junior React Developer",
                "company": "Beta Corp",
                "location": "New York",
                "remote_policy": "onsite",
                "source_key": "linkedin",
                "description": "Frontend development with React and TypeScript",
                "tags": ["react", "typescript"],
                "salary": "$60k-$80k",
                "job_type": "Full-time",
                "date_posted": (now - timedelta(days=5)).isoformat().replace("+00:00", "Z"),
            },
            {
                "id": "3",
                "title": "DevOps Contractor",
                "company": "Cloud Inc",
                "location": "Remote",
                "remote_policy": "remote",
                "source_key": "remoteok",
                "description": "AWS infrastructure and CI/CD pipelines",
                "tags": ["aws", "devops"],
                "salary": "$90/hr",
                "job_type": "Contract",
                "date_posted": (now - timedelta(days=40)).isoformat().replace("+00:00", "Z"),
            },
        ]

    def test_no_filters(self):
        result = filter_jobs(self.jobs)
        self.assertEqual(len(result), 3)

    def test_search_term(self):
        result = filter_jobs(self.jobs, search_term="python")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "1")

    def test_location_filter(self):
        result = filter_jobs(self.jobs, location="Remote")
        self.assertEqual(len(result), 2)

    def test_remote_policy_filter(self):
        result = filter_jobs(self.jobs, remote_policy="onsite")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "2")

    def test_source_key_filter(self):
        result = filter_jobs(self.jobs, source_key="linkedin")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "2")

    def test_salary_min_filter(self):
        result = filter_jobs(self.jobs, salary_min=100000)
        self.assertEqual(len(result), 2)  # $120k-$160k and $90/hr (~$187k)

    def test_salary_max_filter(self):
        result = filter_jobs(self.jobs, salary_max=90000)
        self.assertEqual(len(result), 1)  # only $60k-$80k
        self.assertEqual(result[0]["id"], "2")

    def test_experience_level_filter(self):
        result = filter_jobs(self.jobs, experience_level="senior")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "1")

    def test_experience_level_junior(self):
        result = filter_jobs(self.jobs, experience_level="junior")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "2")

    def test_skills_filter(self):
        result = filter_jobs(self.jobs, skills=["react"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "2")

    def test_skills_filter_multiple(self):
        result = filter_jobs(self.jobs, skills=["python", "aws"])
        self.assertEqual(len(result), 2)

    def test_date_posted_today(self):
        result = filter_jobs(self.jobs, date_posted="today")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "1")

    def test_date_posted_week(self):
        result = filter_jobs(self.jobs, date_posted="week")
        self.assertEqual(len(result), 2)

    def test_date_posted_month(self):
        result = filter_jobs(self.jobs, date_posted="month")
        self.assertEqual(len(result), 2)

    def test_job_type_filter(self):
        result = filter_jobs(self.jobs, job_type="Contract")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "3")

    def test_combined_filters(self):
        result = filter_jobs(
            self.jobs,
            remote_policy="remote",
            search_term="python",
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "1")


class TestScrapersRegistry(unittest.TestCase):
    def test_all_expected_scrapers_registered(self):
        expected = [
            "remotive",
            "weworkremotely",
            "remoteok",
            "linkedin",
            "indeed",
            "glassdoor",
            "himalayas",
            "jobicy",
            "adzuna",
        ]
        for key in expected:
            self.assertIn(key, SCRAPERS, f"Missing scraper: {key}")

    def test_all_scrapers_are_callable(self):
        for key, func in SCRAPERS.items():
            self.assertTrue(callable(func), f"{key} scraper is not callable")


if __name__ == "__main__":
    unittest.main()
