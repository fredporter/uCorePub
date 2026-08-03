import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from udos_publishing.src.contracts import default_mirror_contract
from udos_publishing.src.publishing import PublishingService
from udos_publishing.src.routes import PublishingRoutes
from udos_publishing.src.stores import PublishingStoryStore


class TestPublishingContract(unittest.TestCase):
    def test_default_contract_exposes_guide_and_place(self):
        contract = default_mirror_contract()

        self.assertEqual(contract.guide_name, "udo.guide")
        self.assertEqual(contract.place_name, "udo.place")
        self.assertIn("title", contract.frontmatter_keys)
        self.assertIn("location", contract.location_keys)


class TestPublishingStore(unittest.TestCase):
    def test_create_story_and_route_contract(self):
        with TemporaryDirectory(prefix="udos-publishing-tests-") as tmp_dir:
            storage_path = str(Path(tmp_dir) / "stories.json")
            store = PublishingStoryStore(storage_path=storage_path)
            story_id = store.create_story(
                title="Test Story",
                content="Test content",
                author="test_author",
                visibility="members_only",
                allow_list=["reader"],
            )

            self.assertIsInstance(story_id, str)
            self.assertTrue(story_id.startswith("story_"))

            service = PublishingService(store)
            routes = PublishingRoutes(service)

            self.assertEqual(routes.get_contract()["contract"]["guide_name"], "udo.guide")
            self.assertEqual(routes.health()["place"], "udo.place")
            self.assertEqual(
                routes.list_visible("reader", current_user_can="members_only")["count"],
                1,
            )


if __name__ == '__main__':
    unittest.main()