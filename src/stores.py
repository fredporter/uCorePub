"""
Core store implementations for udos-publishing.
Contains privacy-aware story storage with publishing-specific semantics.
"""
from __future__ import annotations
import json
import time
from typing import Any, Dict, List, Optional, Union


class PublishingStoryStore:
    """Store for managing publishing stories with privacy and expiry semantics."""
    
    def __init__(self, storage_path: str = "/tmp/publishing_stories.json"):
        self.storage_path = storage_path
        self._stories: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _load(self) -> None:
        """Load stories from persistent storage."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                self._stories = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._stories = {}
    
    def _save(self) -> None:
        """Save stories to persistent storage."""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self._stories, f, indent=2, sort_keys=True)
    
    def create_story(
        self,
        title: str,
        content: str,
        author: str,
        visibility: str = "public",
        expires_at: Optional[int] = None,
        allow_list: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new publishing story with privacy controls.
        
        Args:
            title: Title of the story
            content: Main content body
            author: Author identifier
            visibility: One of "public", "private", "members_only"
            expires_at: Unix timestamp when story should expire
            allow_list: List of user IDs allowed to view (for private/members_only)
            
        Returns:
            Story ID
        """
        story_id = f"story_{int(time.time() * 1000)}"
        
        story = {
            "id": story_id,
            "title": title,
            "content": content,
            "author": author,
            "visibility": visibility,
            "created_at": int(time.time()),
            "expires_at": expires_at or int(time.time() + 31536000),  # 1 year default
            "allow_list": allow_list or [],
            "view_count": 0,
            "privacy_settings": {
                "allow_commenting": True,
                "allow_sharing": visibility in ["public", "members_only"]
            }
        }
        
        self._stories[story_id] = story
        self._save()
        return story_id
    
    def get_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a story by ID, checking expiry and permissions."""
        story = self._stories.get(story_id)
        if not story:
            return None
            
        # Check if expired
        current_time = int(time.time())
        if story["expires_at"] <= current_time:
            # Story expired - mark as expired but keep for audit
            story["is_expired"] = True
            self._save()
            return story
            
        return story
    
    def list_visible_stories(self, user_id: str, current_user_can: str = "public") -> List[Dict[str, Any]]:
        """
        List stories visible to a user based on their permissions.
        
        Args:
            user_id: ID of the user
            current_user_can: Permission level of current user ("public", "members_only", "admin")
            
        Returns:
            List of visible stories
        """
        visible_stories = []
        current_time = int(time.time())
        
        for story_id, story in self._stories.items():
            # Check expiry
            if story["expires_at"] <= current_time:
                continue
                
            # Check visibility permissions
            can_view = False
            if story["visibility"] == "public":
                can_view = True
            elif story["visibility"] == "private":
                can_view = False
            elif story["visibility"] == "members_only":
                can_view = user_id in story.get("allow_list", [])
                
            # Check current user permissions
            if current_user_can == "admin" or current_user_can == story["visibility"]:
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
            
        story = self._stories[story_id]
        story["visibility"] = new_visibility
        
        if allow_list is not None:
            story["allow_list"] = allow_list
            
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
        return {
            "total_stories": len(self._stories),
            "active_stories": sum(
                1 for story in self._stories.values() 
                if story["expires_at"] > int(time.time())
            ),
            "expired_stories": sum(
                1 for story in self._stories.values() 
                if story["expires_at"] <= int(time.time())
            )
        }