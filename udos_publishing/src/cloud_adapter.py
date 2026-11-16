"""Opt-in WordPress post transport for caller-approved editions."""

from __future__ import annotations

import base64
import json
from http.client import HTTPException
from typing import Any, Dict, List, Optional, Union
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class WordPressCloudAdapter:
    """Send a selected post using a site's HTTPS application password."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        username: Optional[str] = None,
        app_password: Optional[str] = None,
        multisite_id: Optional[str] = None,
        *,
        enabled: bool = False,
    ):
        self.endpoint = (endpoint or "").rstrip("/")
        self.username = username or ""
        self.app_password = app_password or ""
        self.multisite_id = multisite_id or ""
        self.enabled = enabled

    @property
    def is_configured(self) -> bool:
        return bool(self.endpoint and self.username and self.app_password)

    def _post_url(self) -> str:
        try:
            site = urlsplit(self.endpoint)
            port = site.port
        except ValueError:
            raise ValueError("Enter a valid HTTPS WordPress site URL") from None
        if (
            site.scheme != "https" or not site.hostname or site.username is not None
            or site.password is not None or site.query or site.fragment or port == 0
            or any(character.isspace() for character in self.endpoint)
            or "\\" in self.endpoint
        ):
            raise ValueError("Enter an HTTPS WordPress site URL without credentials, query or fragment")
        # Multisite callers supply the full URL for their selected site.
        return f"{self.endpoint}/wp-json/wp/v2/posts?_fields=id,status"

    def get_status(self) -> Dict[str, Any]:
        """Report local configuration without probing the provider."""
        configured = self.is_configured
        status = {
            "status": "configured" if configured else "planned",
            "mode": "scaffolded",
            "ready": False,
            "cloud_host": self.endpoint or None,
        }
        if not configured:
            status["message"] = "The local headless portal is sovereign. Remote credentials are required."
        elif not self.enabled:
            status["message"] = "Remote post transport requires explicit opt-in."
        else:
            try:
                self._post_url()
            except ValueError as error:
                status["message"] = str(error)
            else:
                status["mode"] = "enabled"
                status["message"] = "Transport enabled. Delivery requires WordPress acknowledgement."
        return status

    def publish_post_remote(
        self,
        title: str,
        content: str,
        status: str = "draft",
        categories: Optional[List[Union[int, str]]] = None,
        tags: Optional[List[Union[int, str]]] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured or not self.enabled:
            return {
                "success": False,
                "mode": "scaffolded",
                "error": "remote_publishing_unavailable",
                "message": self.get_status()["message"],
                "post": {"title": title, "status": status, "categories": categories or [], "tags": tags or []},
            }
        try:
            url = self._post_url()
            if status not in {"draft", "pending", "private", "publish"}:
                raise ValueError("Choose draft, pending, private or publish")
            if not isinstance(title, str) or not title.strip() or not isinstance(content, str):
                raise ValueError("A post title and text content are required")
            payload = {"title": title, "content": content, "status": status}
            for key, terms in (("categories", categories), ("tags", tags)):
                if terms is None:
                    continue
                if not isinstance(terms, list) or any(
                    type(term) not in {int, str} or not str(term).isascii()
                    or not str(term).isdigit() or int(term) < 1 for term in terms
                ):
                    raise ValueError(f"Select existing WordPress {key} by numeric ID")
                payload[key] = [int(term) for term in terms]
            credentials = f"{self.username}:{self.app_password}".encode("utf-8")
            request = Request(
                url, method="POST", data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": "Basic " + base64.b64encode(credentials).decode("ascii"),
                    "Content-Type": "application/json", "Accept": "application/json",
                },
            )
        except ValueError as error:
            return {"success": False, "mode": "enabled", "error": "invalid_post_request", "message": str(error)}

        try:
            with build_opener(_NoRedirect()).open(request, timeout=15) as response:
                if response.status != 201:
                    return self._unconfirmed()
                raw = response.read(65537)
            result = json.loads(raw) if len(raw) <= 65536 else None
        except HTTPError as error:
            code = error.code
            error.close()
            if 400 <= code < 500 and code not in {408, 429}:
                return {"success": False, "mode": "enabled", "error": "remote_rejected", "http_status": code}
            return self._unconfirmed()
        except (URLError, OSError, ValueError, HTTPException):
            return self._unconfirmed()

        remote_id = result.get("id") if isinstance(result, dict) else None
        if type(remote_id) is not int or remote_id < 1:
            return self._unconfirmed()
        if result.get("status") != status:
            return {
                "success": False, "mode": "enabled", "error": "remote_status_mismatch",
                "remote_id": remote_id, "message": "Check the post's status on the WordPress site.",
            }
        return {"success": True, "mode": "live", "remote_id": remote_id, "status": status}

    @staticmethod
    def _unconfirmed() -> Dict[str, Any]:
        return {
            "success": False,
            "mode": "enabled",
            "error": "delivery_unconfirmed",
            "message": "Check the WordPress site for the post before retrying.",
        }
