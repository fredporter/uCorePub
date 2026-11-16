"""Tests for opt-in WordPress publishing and acknowledgement handling."""

import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
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

    def test_configured_adapter_remains_unavailable(self):
        adapter = WordPressCloudAdapter(
            endpoint="https://cloud.udos.invalid",
            username="publisher",
            app_password="secret-app-token",
        )
        self.assertTrue(adapter.is_configured)
        status = adapter.get_status()
        self.assertEqual("configured", status["status"])
        self.assertEqual("scaffolded", status["mode"])
        self.assertFalse(status["ready"])
        result = adapter.publish_post_remote(title="Hello", content="Body")
        self.assertFalse(result["success"])
        self.assertEqual("remote_publishing_unavailable", result["error"])
        self.assertNotIn("remote_id", result)


    def test_opt_in_posts_to_selected_site_with_numeric_taxonomy(self):
        adapter = WordPressCloudAdapter("https://example.invalid/selected-site", "publisher", "fixture", enabled=True)
        with patch("udos_publishing.src.cloud_adapter.build_opener") as opener:
            response = MagicMock(status=201)
            response.read.return_value = b'{"id": 27, "status": "draft"}'
            opener.return_value.open.return_value.__enter__.return_value = response
            result = adapter.publish_post_remote("Edition", "Reviewed content", categories=["3"], tags=[4])
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual("POST", request.get_method())
            self.assertEqual("https://example.invalid/selected-site/wp-json/wp/v2/posts?_fields=id,status", request.full_url)
            self.assertEqual([3], json.loads(request.data)["categories"])
            self.assertTrue(request.get_header("Authorization").startswith("Basic "))
            self.assertEqual({"success": True, "mode": "live", "remote_id": 27, "status": "draft"}, result)

    def test_rejects_insecure_destination_before_sending_credentials(self):
        adapter = WordPressCloudAdapter("http://example.invalid", "publisher", "fixture", enabled=True)
        with patch("udos_publishing.src.cloud_adapter.build_opener") as opener:
            self.assertEqual("invalid_post_request", adapter.publish_post_remote("Edition", "Body")["error"])
            opener.assert_not_called()

    def test_ambiguous_delivery_is_not_retried(self):
        adapter = WordPressCloudAdapter("https://example.invalid", "publisher", "fixture", enabled=True)
        with patch("udos_publishing.src.cloud_adapter.build_opener") as opener:
            opener.return_value.open.side_effect = URLError("timed out")
            result = adapter.publish_post_remote("Edition", "Body")
            self.assertEqual("delivery_unconfirmed", result["error"])
            opener.return_value.open.assert_called_once()

    def test_unauthorized_provider_response_is_rejected(self):
        adapter = WordPressCloudAdapter("https://example.invalid", "publisher", "fixture", enabled=True)
        with patch("udos_publishing.src.cloud_adapter.build_opener") as opener:
            opener.return_value.open.side_effect = HTTPError(adapter.endpoint, 401, "Rejected", {}, None)
            result = adapter.publish_post_remote("Edition", "Body")
            self.assertEqual(401, result["http_status"])
            self.assertFalse(result["success"])
            self.assertNotIn("remote_id", result)

    def test_status_mismatch_reports_created_post_for_review(self):
        adapter = WordPressCloudAdapter("https://example.invalid", "publisher", "fixture", enabled=True)
        with patch("udos_publishing.src.cloud_adapter.build_opener") as opener:
            response = MagicMock(status=201)
            response.read.return_value = b'{"id": 27, "status": "draft"}'
            opener.return_value.open.return_value.__enter__.return_value = response
            result = adapter.publish_post_remote("Edition", "Body", status="publish")
            self.assertEqual("remote_status_mismatch", result["error"])
            self.assertEqual(27, result["remote_id"])
            self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
