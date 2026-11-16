import hashlib
import tempfile
import unittest
from pathlib import Path

from udos_publishing.src.compiler import compile_reviewed_library
from udos_publishing.src.edition_feed import preview_edition_feed
from udos_publishing.src.feed_codec import parse_feed


class EditionFeedTest(unittest.TestCase):
    def test_preview_only_uses_approved_edition_projection(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            root = workspace / "edition"
            root.mkdir()
            article = root / "map.md"
            article.write_text("# Map\n\nBody excluded from excerpt")
            (root / "unlisted.md").write_text("unlisted draft sentinel")
            (workspace / "map.md").write_text("personal overlay sentinel")
            included = {
                "path": "map.md", "sha256": hashlib.sha256(article.read_bytes()).hexdigest(),
                "uid": "urn:udos:map", "visibility": "public", "review_status": "approved",
                "title": "Map", "url": "https://example.org/map",
                "excerpt": "Reviewed navigation excerpt", "tags": ["navigation"],
                "published": "2026-11-12T00:00:00+00:00",
            }
            manifest = {
                "schema_version": 1, "visibility": "public", "title": "Knowledge",
                "home_url": "https://example.org", "author": "uDOS",
                "updated": "2026-11-14T00:00:00+00:00",
                "feed_urls": {wire: f"https://example.org/{wire}" for wire in ("rss", "atom", "json")},
                "items": [
                    included,
                    {"visibility": "private", "review_status": "approved", "title": "private sentinel"},
                    {"visibility": "public", "review_status": "draft", "title": "draft sentinel"},
                ],
            }
            for wire in manifest["feed_urls"]:
                with self.subTest(wire=wire):
                    payload = preview_edition_feed(manifest, root, wire)
                    self.assertNotIn(b"sentinel", payload)
                    self.assertNotIn(b"Body excluded", payload)
                    item, = parse_feed(payload).items
                    self.assertEqual(item.uid, included["uid"])
                    self.assertEqual(item.url, included["url"])
                    self.assertEqual(item.tags, ("navigation",))
                    self.assertEqual(item.text or item.html, included["excerpt"])

            dataset = root / "datasets" / "length.json"
            dataset.parent.mkdir()
            dataset.write_bytes(b'{"inch_in_meters": 0.0254}')
            dataset_record = {
                "path": "datasets/length.json", "sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
                "visibility": "public", "review_status": "approved",
            }
            manifest["datasets"] = [dataset_record, {"visibility": "private", "review_status": "approved"}]
            output = workspace / "package"
            packaged = compile_reviewed_library(manifest, root, output)
            self.assertEqual(packaged["items"], [included])
            self.assertEqual(packaged["datasets"], [dataset_record])
            self.assertEqual((output / "datasets/length.json").read_bytes(), dataset.read_bytes())
            for path in (output / "feeds").iterdir():
                self.assertEqual([item.uid for item in parse_feed(path.read_bytes()).items], [included["uid"]])
            second = workspace / "second-package"
            compile_reviewed_library(manifest, root, second)
            self.assertEqual(
                {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()},
                {p.relative_to(second): p.read_bytes() for p in second.rglob("*") if p.is_file()},
            )
            with self.assertRaises(FileExistsError):
                compile_reviewed_library(manifest, root, output)
            dataset.write_text("changed")
            with self.assertRaisesRegex(ValueError, "dataset revision changed"):
                compile_reviewed_library(manifest, root, workspace / "changed")
            self.assertFalse((workspace / "changed").exists())
            self.assertEqual((output / "map.md").read_bytes(), article.read_bytes())
            self.assertFalse((output / "unlisted.md").exists())
            self.assertNotIn("sentinel", (output / "edition-manifest.json").read_text())
            self.assertEqual(
                (output / "feeds/rss.xml").read_bytes(),
                preview_edition_feed(packaged, output, "rss"),
            )


            article.write_text("Changed content")
            with self.assertRaisesRegex(ValueError, "revision changed"):
                preview_edition_feed(manifest, root, "json")

            article.unlink()
            article.symlink_to(workspace / "map.md")
            with self.assertRaisesRegex(ValueError, "outside its declared path"):
                preview_edition_feed(manifest, root, "json")
