import unittest
from unittest.mock import patch

from jobintel.application_autofill import detect_application_provider, launch_autofill_session


class ApplicationAutofillTests(unittest.TestCase):
    def test_detects_known_application_providers(self):
        self.assertEqual(detect_application_provider("https://boards.greenhouse.io/example/jobs/123"), "greenhouse")
        self.assertEqual(detect_application_provider("https://jobs.lever.co/example/123"), "lever")
        self.assertEqual(
            detect_application_provider("https://example.myworkdayjobs.com/en-US/careers/job/123"), "workday"
        )

    def test_unknown_provider_falls_back_to_generic(self):
        self.assertEqual(detect_application_provider("https://example.com/careers/backend-engineer"), "generic")

    def test_launch_autofill_returns_structured_failure_when_selenium_unavailable(self):
        with patch("jobintel.application_autofill.webdriver", None):
            result = launch_autofill_session({"url": "https://example.com/jobs/123"}, {})

        self.assertFalse(result["success"])
        self.assertEqual(result["provider"], "generic")
        self.assertIn("Selenium is not installed", result["message"])


if __name__ == "__main__":
    unittest.main()
