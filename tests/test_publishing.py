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


class TestEditionCompiler(unittest.TestCase):
    def test_compile_edition_to_static_bundle(self):
        from udos_publishing.src.compiler import compile_edition_to_static

        raw_md = (
            "---\nauthor: private_author\n---\n"
            "# System Architecture\n\n"
            "<!-- section: REQ-001 -->\n"
            "This describes verified architecture [SRC-1].\n"
        )
        with TemporaryDirectory(prefix="udos-edition-tests-") as tmp_dir:
            out_dir = Path(tmp_dir) / "output"
            receipt = compile_edition_to_static(
                edition_markdown=raw_md,
                title="System Architecture",
                edition_num=1,
                output_dir=out_dir,
            )
            self.assertTrue(receipt["sanitized"])
            self.assertEqual(receipt["edition"], 1)
            self.assertTrue((out_dir / "index.html").is_file())
            self.assertTrue((out_dir / "edition_1.clean.md").is_file())
            clean_text = (out_dir / "edition_1.clean.md").read_text()
            self.assertNotIn("<!-- section:", clean_text)
            self.assertNotIn("author: private_author", clean_text)
            self.assertIn("[SRC-1]", clean_text)

    def test_compile_edition_rewrites_manifest_links(self):
        from udos_publishing.src.compiler import compile_edition_to_static

        raw_md = (
            "# Guide\n\n"
            "See [[Setup#Quick|Start]] and [[Secret]].\n"
        )
        with TemporaryDirectory(prefix="udos-manifest-compile-") as tmp_dir:
            out_dir = Path(tmp_dir) / "output"
            receipt = compile_edition_to_static(
                edition_markdown=raw_md,
                title="Guide",
                edition_num=2,
                output_dir=out_dir,
                edition_manifest={"Docs/Setup.md": "https://udo.guide/setup/"},
                known_paths=["Docs/Setup.md", "Secret.md"],
            )
            clean_text = (out_dir / "edition_2.clean.md").read_text()
            self.assertIn("[Start](https://udo.guide/setup/#Quick)", clean_text)
            self.assertIn("Secret", clean_text)
            self.assertNotIn("[Secret](", clean_text)


if __name__ == '__main__':
    unittest.main()