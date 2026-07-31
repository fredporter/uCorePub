import unittest
from udos_publishing.src.stores import PublishingStoryStore


class TestPublishingStore(unittest.TestCase):
    def test_create_story(self):
        store = PublishingStoryStore()
        story_id = store.create_story(
            title="Test Story",
            content="Test content",
            author="test_author",
            visibility="public"
        )
        self.assertIsInstance(story_id, str)
        self.assertTrue(story_id.startswith("story_"))


if __name__ == '__main__':
    unittest.main()