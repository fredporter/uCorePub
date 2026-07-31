"""
API route definitions for udos-publishing.
Defines endpoint signatures and routing logic for publishing stories.
"""
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
        """
        Handle POST /api/publishing/stories endpoint.
        
        Args:
            title: Story title
            content: Story content
            author: Author identifier
            visibility: Story visibility level
            expires_at: Expiration timestamp
            allow_list: Allow list for private stories
            
        Returns:
            JSON response with story ID and status
        """
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
            "message": "Story created successfully"
        }
    
    def get_story(self, story_id: str) -> Dict[str, Any]:
        """
        Handle GET /api/publishing/stories/{id} endpoint.
        
        Args:
            story_id: ID of the story to retrieve
            
        Returns:
            JSON response with story details or error
        """
        story = self.service.get_story(story_id)
        if not story:
            return {
                "status": "error",
                "message": "Story not found or expired"
            }
            
        return {
            "status": "success",
            "data": story
        }
    
    def list_visible(self, user_id: str, current_user_can: str = "public") -> Dict[str, Any]:
        """
        Handle GET /api/publishing/stories/visible endpoint.
        
        Args:
            user_id: ID of the requesting user
            current_user_can: Permission level of current user
            
        Returns:
            JSON response with list of visible story IDs
        """
        visible_story_ids = self.service.list_visible_stories(user_id, current_user_can)
        
        return {
            "status": "success",
            "visible_story_ids": visible_story_ids,
            "count": len(visible_story_ids)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Handle GET /api/publishing/stories/stats endpoint.
        
        Returns:
            JSON response with store statistics
        """
        stats = self.service.get_stats()
        return {
            "status": "success",
            "stats": stats
        }