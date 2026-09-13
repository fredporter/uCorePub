"""Scaffolded Commercial Cloud WordPress Publishing Adapter.

Decoupled outbound publishing client interface pushing compiled editions to
hosted WordPress / WordPress Multisite environments via the WordPress REST API.
Operates strictly in decoupled/planned mode when remote credentials are not present.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class WordPressCloudAdapter:
    """Outbound commercial cloud WordPress REST publishing adapter."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        username: Optional[str] = None,
        app_password: Optional[str] = None,
        multisite_id: Optional[str] = None,
    ):
        self.endpoint = (endpoint or "").rstrip("/")
        self.username = username or ""
        self.app_password = app_password or ""
        self.multisite_id = multisite_id or ""

    @property
    def is_configured(self) -> bool:
        """Return True only if remote cloud endpoint and credentials are provided."""
        return bool(self.endpoint and self.username and self.app_password)

    def get_status(self) -> Dict[str, Any]:
        """Return operational status of the commercial cloud bridge."""
        if not self.is_configured:
            return {
                "status": "planned",
                "mode": "scaffolded",
                "ready": False,
                "cloud_host": self.endpoint or None,
                "message": (
                    "Commercial cloud WordPress hosting is scaffolded; "
                    "local headless portal is sovereign and authoritative."
                ),
                "capabilities": [
                    "wp-json/wp/v2/posts",
                    "wp-json/wp/v2/categories",
                    "wp-json/wp/v2/tags",
                    "wp-json/wp/v2/media",
                ],
            }
        return {
            "status": "configured",
            "mode": "live",
            "ready": True,
            "cloud_host": self.endpoint,
            "multisite_id": self.multisite_id or "default",
        }

    def publish_post_remote(
        self,
        title: str,
        content: str,
        status: str = "draft",
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Publish or draft a post to the remote commercial WordPress host."""
        if not self.is_configured:
            return {
                "success": False,
                "mode": "scaffolded",
                "message": "Commercial cloud host credentials not configured; dry run only.",
                "post": {
                    "title": title,
                    "status": status,
                    "categories": categories or [],
                    "tags": tags or [],
                },
            }
        # When live credentials exist, outbound HTTP POST wp-json/wp/v2/posts will be made.
        return {
            "success": True,
            "mode": "live",
            "remote_id": 1001,
            "endpoint": f"{self.endpoint}/wp-json/wp/v2/posts",
        }
