"""Story storage for udos-publishing."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class PublishingStoryStore:
    """Store for publishing stories with privacy and expiry semantics."""

    _ALLOWED_VISIBILITIES = {"public", "private", "members_only"}

    def __init__(self, storage_path: str = "/tmp/udos_publishing_stories.json"):
        self.storage_path = Path(storage_path)
        self._stories: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load stories from persistent storage."""

        try:
            self._stories = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            self._stories = {}

    def _save(self) -> None:
        """Save stories to persistent storage."""

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(
            json.dumps(self._stories, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def create_story(
        self,
        title: str,
        content: str,
        author: str,
        visibility: str = "public",
        expires_at: Optional[int] = None,
        allow_list: Optional[List[str]] = None,
    ) -> str:
        """Create a new publishing story."""

        if visibility not in self._ALLOWED_VISIBILITIES:
            raise ValueError(f"Unsupported visibility: {visibility}")

        story_id = f"story_{uuid.uuid4().hex}"
        now = int(time.time())
        story = {
            "id": story_id,
            "title": title,
            "content": content,
            "author": author,
            "visibility": visibility,
            "created_at": now,
            "expires_at": expires_at or (now + 31536000),
            "allow_list": list(allow_list or []),
            "view_count": 0,
            "mirror": {
                "guide": "udo.guide",
                "place": "udo.place",
            },
            "privacy_settings": {
                "allow_commenting": True,
                "allow_sharing": visibility in {"public", "members_only"},
            },
        }

        self._stories[story_id] = story
        self._save()
        return story_id

    def get_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a story by ID, checking expiry."""

        story = self._stories.get(story_id)
        if not story:
            return None

        current_time = int(time.time())
        if story["expires_at"] <= current_time:
            story["is_expired"] = True
            self._save()

        return dict(story)

    def list_visible_stories(self, user_id: str, current_user_can: str = "public") -> List[str]:
        """List story IDs visible to a user."""

        visible_stories: List[str] = []
        current_time = int(time.time())

        for story_id, story in self._stories.items():
            if story["expires_at"] <= current_time:
                continue

            can_view = False
            if story["visibility"] == "public":
                can_view = True
            elif story["visibility"] == "members_only":
                can_view = user_id in story.get("allow_list", [])

            if current_user_can == "admin":
                can_view = True
            elif current_user_can == "members_only" and story["visibility"] == "members_only":
                can_view = user_id in story.get("allow_list", [])

            if can_view:
                visible_stories.append(story_id)

        return visible_stories

    def update_story_visibility(
        self,
        story_id: str,
        new_visibility: str,
        allow_list: Optional[List[str]] = None,
    ) -> bool:
        """Update visibility settings of an existing story."""

        if story_id not in self._stories:
            return False
        if new_visibility not in self._ALLOWED_VISIBILITIES:
            raise ValueError(f"Unsupported visibility: {new_visibility}")

        story = self._stories[story_id]
        story["visibility"] = new_visibility
        if allow_list is not None:
            story["allow_list"] = list(allow_list)

        self._save()
        return True

    def delete_story(self, story_id: str) -> bool:
        """Delete a story permanently."""

        if story_id not in self._stories:
            return False

        del self._stories[story_id]
        self._save()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""

        now = int(time.time())
        return {
            "total_stories": len(self._stories),
            "active_stories": sum(1 for story in self._stories.values() if story["expires_at"] > now),
            "expired_stories": sum(1 for story in self._stories.values() if story["expires_at"] <= now),
        }