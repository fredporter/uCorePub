"""Tests for scaffolded commercial cloud WordPress publishing adapter."""

import unittest
from udos_publishing.src.cloud_adapter import WordPressCloudAdapter


class TestWordPressCloudAdapter(unittest.TestCase):
    def test_unconfigured_status_is_scaffolded_and_not_ready(self):
        adapter = WordPressCloudAdapter()
        self.assertFalse(adapter.is_configured)
        status = adapter.get_status()
        self.assertEqual("planned", status["status"])
        self.assertEqual("scaffolded", status["mode"])
        self.assertFalse(status["ready"])
        self.assertIn("local headless portal is sovereign", status["message"])

    def test_dry_run_publish_when_unconfigured(self):
        adapter = WordPressCloudAdapter()
        result = adapter.publish_post_remote(title="Hello uDos", content="Article content")
        self.assertFalse(result["success"])
        self.assertEqual("scaffolded", result["mode"])
        self.assertEqual("Hello uDos", result["post"]["title"])

    def test_configured_adapter_reports_live(self):
        adapter = WordPressCloudAdapter(
            endpoint="https://cloud.udos.invalid",
            username="publisher",
            app_password="secret-app-token",
        )
        self.assertTrue(adapter.is_configured)
        status = adapter.get_status()
        self.assertEqual("configured", status["status"])
        self.assertEqual("live", status["mode"])
        self.assertTrue(status["ready"])


if __name__ == "__main__":
    unittest.main()
