"""API route definitions for udos-publishing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .publishing import PublishingService


class PublishingRoutes:
    """Container for publishing route handlers."""

    def __init__(self, service: PublishingService):
        self.service = service

    def create_story(
        self,
        title: str,
        content: str,
        author: str,
        visibility: str = "public",
        expires_at: Optional[int] = None,
        allow_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Handle POST /api/publishing/stories."""

        story_id = self.service.create_story(
            title=title,
            content=content,
            author=author,
            visibility=visibility,
            expires_at=expires_at,
            allow_list=allow_list,
        )

        return {
            "status": "success",
            "story_id": story_id,
            "message": "Story created successfully",
        }

    def get_story(self, story_id: str) -> Dict[str, Any]:
        """Handle GET /api/publishing/stories/{id}."""

        story = self.service.get_story(story_id)
        if not story:
            return {
                "status": "error",
                "message": "Story not found or expired",
            }

        return {
            "status": "success",
            "data": story,
        }

    def list_visible(self, user_id: str, current_user_can: str = "public") -> Dict[str, Any]:
        """Handle GET /api/publishing/stories/visible."""

        visible_story_ids = self.service.list_visible_stories(user_id, current_user_can)

        return {
            "status": "success",
            "visible_story_ids": visible_story_ids,
            "count": len(visible_story_ids),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Handle GET /api/publishing/stories/stats."""

        return {
            "status": "success",
            "stats": self.service.get_stats(),
        }

    def get_contract(self) -> Dict[str, Any]:
        """Handle GET /api/publishing/contract."""

        return {
            "status": "success",
            "contract": self.service.get_contract(),
        }

    def health(self) -> Dict[str, Any]:
        """Handle GET /api/publishing/health."""

        contract = self.service.get_contract()
        return {
            "status": "ok",
            "service": "udos-publishing",
            "guide": contract["guide_name"],
            "place": contract["place_name"],
        }