import unittest

from udos_publishing.src.edition_links import preview_wiki_links, rewrite_wiki_links


class EditionLinkPreviewTests(unittest.TestCase):
    def test_only_included_targets_have_urls_and_ambiguity_is_reported(self):
        preview = preview_wiki_links(
            "[[Setup]] [[Guides/Setup#Install|Read this]] [[Private]] [[Missing]] ![[diagram.png]]",
            known_paths=["Guides/Setup.md", "Old/Setup.md", "Private.md"],
            edition_manifest={"Guides/Setup.md": "../setup/", "Assets/diagram.png": "../diagram.png"},
        )
        self.assertEqual(
            [row["status"] for row in preview],
            ["ambiguous", "included", "outside_edition", "missing", "included"],
        )
        self.assertEqual([row["url"] for row in preview], [None, "../setup/", None, None, "../diagram.png"])
        self.assertEqual((preview[1]["anchor"], preview[1]["label"]), ("Install", "Read this"))
        self.assertTrue(preview[4]["embed"])

    def test_ignores_examples_and_uses_current_note_for_heading_only_links(self):
        preview = preview_wiki_links(
            "```md\n[[Example]]\n```\n`[[Inline example]]` [[#Intro]]",
            known_paths=[],
            edition_manifest={"Notes/Start.md": "./"},
            source_path="Notes/Start.md",
        )
        self.assertEqual([(row["line"], row["anchor"], row["url"]) for row in preview], [(4, "Intro", "./")])

    def test_rewrite_wiki_links_transforms_included_targets_and_sanitizes_unincluded(self):
        rewritten = rewrite_wiki_links(
            "[[Setup]] [[Guides/Setup#Install|Read this]] [[Private]] `[[Keep Code]]` ![[diagram.png]]",
            known_paths=["Guides/Setup.md", "Old/Setup.md", "Private.md"],
            edition_manifest={"Guides/Setup.md": "../setup/", "Assets/diagram.png": "../diagram.png"},
        )
        self.assertIn("Setup", rewritten)
        self.assertIn("[Read this](../setup/#Install)", rewritten)
        self.assertIn("Private", rewritten)
        self.assertIn("`[[Keep Code]]`", rewritten)
        self.assertIn("![diagram.png](../diagram.png)", rewritten)
        self.assertNotIn("[Private](", rewritten)
        self.assertNotIn("[Setup](", rewritten)
