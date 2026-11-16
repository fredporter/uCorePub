import unittest

from udos_publishing.src.feed_codec import Feed, FeedItem, parse_feed, render_feed


class FeedCodecTest(unittest.TestCase):
    def test_same_collection_round_trips_in_all_formats(self):
        item = FeedItem(
            "urn:udos:map-1", "Map & compass", "https://example.org/map?a=1&b=2",
            "", "2026-11-12T00:00:00+00:00", "2026-11-14T00:00:00+00:00",
            ("navigation", "offline"), "<p>A reviewed article</p>",
        )
        feed = Feed("Global Knowledge", "https://example.org/", (item,), "Reference edition")
        for wire in ("rss", "atom", "json"):
            with self.subTest(wire=wire):
                payload = render_feed(
                    feed, wire, feed_url=f"https://example.org/{wire}",
                    updated=item.updated, author="uDOS",
                )
                self.assertEqual(parse_feed(payload), feed)

    def test_external_rss_without_guid_uses_item_link(self):
        feed = parse_feed(b"""<rss version="2.0"><channel>
          <title>Fieldwork</title><link>https://example.org/</link><description>News</description>
          <item><link>https://example.org/first</link>
            <description>&lt;p&gt;First entry&lt;/p&gt;</description>
            <pubDate>Sat, 14 Nov 2026 08:00:00 +0800</pubDate>
          </item></channel></rss>""")
        self.assertEqual(feed.items[0].uid, "https://example.org/first")
        self.assertEqual(feed.items[0].published, "2026-11-14T00:00:00+00:00")
        self.assertEqual(feed.items[0].html, "<p>First entry</p>")

    def test_unsafe_xml_and_oversized_payload_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "entities are disabled"):
            parse_feed(b'<!DOCTYPE rss [<!ENTITY probe "value">]><rss>&probe;</rss>')
        with self.assertRaisesRegex(ValueError, "byte limit"):
            parse_feed(b" " * 2_000_001)
