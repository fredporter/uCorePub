"""Core publishing functionality for udos-publishing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .contracts import PublishingMirrorContract, default_mirror_contract
from .stores import PublishingStoryStore


class PublishingService:
    """Main publishing service that handles story creation and retrieval."""

    def __init__(
        self,
        store: PublishingStoryStore,
        contract: PublishingMirrorContract | None = None,
    ):
        self.store = store
        self.contract = contract or default_mirror_contract()

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

        return self.store.create_story(
            title=title,
            content=content,
            author=author,
            visibility=visibility,
            expires_at=expires_at,
            allow_list=allow_list,
        )

    def get_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a story by ID."""

        return self.store.get_story(story_id)

    def list_visible_stories(self, user_id: str, current_user_can: str = "public") -> List[str]:
        """List story IDs visible to a user."""

        return self.store.list_visible_stories(user_id, current_user_can)

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""

        return self.store.get_stats()

    def get_contract(self) -> Dict[str, Any]:
        """Return the publishing mirror contract."""

        return self.contract.as_dict()