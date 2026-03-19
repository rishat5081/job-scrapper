"""Tests for source_registry.py"""

import unittest

from jobintel.source_registry import (
    SOURCE_DEFINITIONS,
    get_source,
    list_enabled_sources,
    list_sources,
)


class TestSourceDefinition(unittest.TestCase):
    def test_source_definition_is_frozen(self):
        source = SOURCE_DEFINITIONS[0]
        with self.assertRaises(AttributeError):
            source.key = "changed"

    def test_to_dict_returns_all_fields(self):
        source = SOURCE_DEFINITIONS[0]
        d = source.to_dict()
        self.assertIn("key", d)
        self.assertIn("name", d)
        self.assertIn("homepage", d)
        self.assertIn("regions", d)
        self.assertIn("supports_remote", d)
        self.assertIn("ingestion_mode", d)
        self.assertIn("enabled_by_default", d)
        self.assertIn("automation_allowed", d)
        self.assertIn("notes", d)
        self.assertIn("tags", d)


class TestSourceRegistry(unittest.TestCase):
    def test_list_sources_returns_all(self):
        sources = list_sources()
        self.assertIsInstance(sources, list)
        self.assertGreaterEqual(len(sources), 14)
        for source in sources:
            self.assertIsInstance(source, dict)
            self.assertIn("key", source)

    def test_get_source_found(self):
        source = get_source("remotive")
        self.assertIsNotNone(source)
        self.assertEqual(source.key, "remotive")
        self.assertEqual(source.name, "Remotive")

    def test_get_source_not_found(self):
        source = get_source("nonexistent_source")
        self.assertIsNone(source)

    def test_list_enabled_sources(self):
        enabled = list_enabled_sources()
        self.assertGreaterEqual(len(enabled), 8)
        for source in enabled:
            self.assertTrue(source.enabled_by_default)
            self.assertTrue(source.automation_allowed)

    def test_linkedin_enabled_via_jobspy(self):
        source = get_source("linkedin")
        self.assertIsNotNone(source)
        self.assertTrue(source.enabled_by_default)
        self.assertTrue(source.automation_allowed)
        self.assertEqual(source.ingestion_mode, "library")

    def test_indeed_enabled_via_jobspy(self):
        source = get_source("indeed")
        self.assertIsNotNone(source)
        self.assertTrue(source.enabled_by_default)
        self.assertEqual(source.ingestion_mode, "library")

    def test_glassdoor_enabled_via_jobspy(self):
        source = get_source("glassdoor")
        self.assertIsNotNone(source)
        self.assertTrue(source.enabled_by_default)
        self.assertEqual(source.ingestion_mode, "library")

    def test_himalayas_source(self):
        source = get_source("himalayas")
        self.assertIsNotNone(source)
        self.assertTrue(source.enabled_by_default)
        self.assertEqual(source.ingestion_mode, "public_api")
        self.assertIn("himalayas.app", source.api_url)

    def test_jobicy_source(self):
        source = get_source("jobicy")
        self.assertIsNotNone(source)
        self.assertTrue(source.enabled_by_default)
        self.assertEqual(source.ingestion_mode, "public_api")

    def test_adzuna_disabled_by_default(self):
        source = get_source("adzuna")
        self.assertIsNotNone(source)
        self.assertFalse(source.enabled_by_default)
        self.assertTrue(source.automation_allowed)

    def test_all_sources_have_unique_keys(self):
        keys = [s.key for s in SOURCE_DEFINITIONS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_all_sources_have_homepage(self):
        for source in SOURCE_DEFINITIONS:
            self.assertTrue(source.homepage, f"{source.key} missing homepage")
            self.assertTrue(
                source.homepage.startswith("http"),
                f"{source.key} homepage not a URL",
            )

    def test_all_sources_have_regions(self):
        for source in SOURCE_DEFINITIONS:
            self.assertIsInstance(source.regions, list)
            self.assertGreaterEqual(len(source.regions), 1, f"{source.key} has no regions")


if __name__ == "__main__":
    unittest.main()
