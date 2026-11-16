"""Bounded local feed parsing and export of a caller-selected collection."""

import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

ATOM = "http://www.w3.org/2005/Atom"
JSON_FEED = "https://jsonfeed.org/version/1.1"
MAX_BYTES = 2_000_000
MAX_ITEMS = 500


@dataclass(frozen=True)
class FeedItem:
    uid: str
    title: str
    url: str
    text: str
    published: str = ""
    updated: str = ""
    tags: tuple = ()
    html: str = ""


@dataclass(frozen=True)
class Feed:
    title: str
    home_url: str
    items: tuple
    description: str = ""


def _date(value, rss=False):
    if not value:
        return ""
    if not isinstance(value, str):
        raise ValueError("Feed dates must be strings")
    stamp = parsedate_to_datetime(value) if rss else datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )
    if stamp.tzinfo is None:
        raise ValueError("Feed dates require a timezone")
    return stamp.astimezone(timezone.utc).isoformat(timespec="seconds")


def _json_item(item):
    return FeedItem(
        item.get("id", ""), item.get("title", ""), item.get("url", ""),
        item.get("content_text", item.get("summary", "")),
        _date(item.get("date_published")), _date(item.get("date_modified")),
        tuple(item.get("tags", [])), item.get("content_html", ""),
    )


def _atom_link(node):
    return next(
        (link.get("href", "") for link in node.findall(f"{{{ATOM}}}link")
         if link.get("rel", "alternate") == "alternate"),
        "",
    )


def _atom_item(node):
    def read(name):
        return node.findtext(f"{{{ATOM}}}{name}", "")

    content = node.find(f"{{{ATOM}}}content")
    is_html = content is not None and content.get("type") == "html"
    return FeedItem(
        read("id"), read("title"), _atom_link(node),
        read("summary") if is_html else read("content") or read("summary"),
        _date(read("published")), _date(read("updated")),
        tuple(tag.get("term", "") for tag in node.findall(f"{{{ATOM}}}category")),
        read("content") if is_html else "",
    )


def _rss_item(node):
    url = node.findtext("link", "")
    return FeedItem(
        node.findtext("guid") or url, node.findtext("title", ""), url, "",
        _date(node.findtext("pubDate"), rss=True),
        _date(node.findtext(f"{{{ATOM}}}updated")),
        tuple(tag.text or "" for tag in node.findall("category")),
        node.findtext("description", ""),
    )


def _validate(feed):
    if not isinstance(feed.title, str) or not feed.title.strip():
        raise ValueError("Feed title is required")
    if not isinstance(feed.home_url, str) or not isinstance(feed.description, str):
        raise ValueError("Feed URL and description must be strings")
    if len(feed.items) > MAX_ITEMS:
        raise ValueError("Too many feed items")
    seen = set()
    for item in feed.items:
        fields = (item.uid, item.title, item.url, item.text, item.html, *item.tags)
        if not all(isinstance(field, str) for field in fields):
            raise ValueError("Feed fields must be strings")
        if not item.uid.strip() or item.uid in seen:
            raise ValueError("Feed items require unique source identities")
        seen.add(item.uid)
    return feed


def parse_feed(payload):
    """Parse an RSS 2.0, Atom or JSON Feed 1.1 fixture without fetching links."""
    if len(payload) > MAX_BYTES:
        raise ValueError("Feed exceeds byte limit")
    text = payload.decode("utf-8-sig")
    if text.lstrip().startswith("{"):
        data = json.loads(text)
        if data.get("version") != JSON_FEED:
            raise ValueError("Expected JSON Feed 1.1")
        items = data.get("items")
        if not isinstance(items, list) or len(items) > MAX_ITEMS:
            raise ValueError("Invalid feed items")
        if any(not isinstance(item, dict) or not isinstance(item.get("tags", []), list) for item in items):
            raise ValueError("Invalid JSON Feed item")
        return _validate(Feed(
            data.get("title"), data.get("home_page_url", ""),
            tuple(_json_item(item) for item in items), data.get("description", ""),
        ))

    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.IGNORECASE):
        raise ValueError("Feed XML declarations for DTDs and entities are disabled")
    root = ET.fromstring(text)
    if root.tag == f"{{{ATOM}}}feed":
        nodes = root.findall(f"{{{ATOM}}}entry")
        title = root.findtext(f"{{{ATOM}}}title", "")
        home = _atom_link(root)
        description = root.findtext(f"{{{ATOM}}}subtitle", "")
        convert = _atom_item
    elif root.tag == "rss" and root.get("version") == "2.0":
        channel = root.find("channel")
        if channel is None:
            raise ValueError("Missing RSS channel")
        nodes = channel.findall("item")
        title = channel.findtext("title", "")
        home = channel.findtext("link", "")
        description = channel.findtext("description", "")
        convert = _rss_item
    else:
        raise ValueError("Unsupported feed format")
    if len(nodes) > MAX_ITEMS:
        raise ValueError("Too many feed items")
    return _validate(Feed(title, home, tuple(map(convert, nodes)), description))


def render_feed(feed, wire_format, *, feed_url, updated, author):
    """Render a selected public projection. The caller controls eligibility."""
    _validate(feed)
    if wire_format == "json":
        items = []
        for item in feed.items:
            entry = {"id": item.uid, "title": item.title, "content_text": item.text,
                     "tags": list(item.tags)}
            for key, value in (("url", item.url), ("content_html", item.html),
                               ("date_published", item.published), ("date_modified", item.updated)):
                if value:
                    entry[key] = value
            items.append(entry)
        return json.dumps({
            "version": JSON_FEED, "title": feed.title, "home_page_url": feed.home_url,
            "feed_url": feed_url, "description": feed.description, "items": items,
        }, ensure_ascii=False).encode("utf-8")

    def add(parent, name, value, **attributes):
        child = ET.SubElement(parent, name, attributes)
        child.text = value
        return child

    if wire_format == "rss":
        root = ET.Element("rss", version="2.0")
        channel = ET.SubElement(root, "channel")
        add(channel, "title", feed.title)
        add(channel, "link", feed.home_url)
        add(channel, "description", feed.description)
        for item in feed.items:
            node = ET.SubElement(channel, "item")
            add(node, "guid", item.uid, isPermaLink="false")
            add(node, "title", item.title)
            if item.url:
                add(node, "link", item.url)
            add(node, "description", item.html or html.escape(item.text))
            if item.published:
                add(node, "pubDate", format_datetime(datetime.fromisoformat(item.published)))
            if item.updated:
                add(node, f"{{{ATOM}}}updated", item.updated)
            for tag in item.tags:
                add(node, "category", tag)
    elif wire_format == "atom":
        root = ET.Element("feed", xmlns=ATOM)
        add(root, "id", feed_url)
        add(root, "title", feed.title)
        if not updated or not author or not urlsplit(feed_url).scheme:
            raise ValueError("Atom export needs a feed URI, update date and author")
        add(root, "updated", _date(updated))
        if feed.description:
            add(root, "subtitle", feed.description)
        add(ET.SubElement(root, "author"), "name", author)
        ET.SubElement(root, "link", href=feed_url, rel="self")
        ET.SubElement(root, "link", href=feed.home_url, rel="alternate")
        for item in feed.items:
            node = ET.SubElement(root, "entry")
            if not urlsplit(item.uid).scheme:
                raise ValueError("Atom item IDs must be absolute URIs")
            add(node, "id", item.uid)
            add(node, "title", item.title)
            if item.url:
                ET.SubElement(node, "link", href=item.url)
            if item.published:
                add(node, "published", item.published)
            add(node, "updated", item.updated or item.published or _date(updated))
            add(node, "content", item.html or item.text, type="html" if item.html else "text")
            if item.html and item.text:
                add(node, "summary", item.text)
            for tag in item.tags:
                ET.SubElement(node, "category", term=tag)
    else:
        raise ValueError("Unsupported feed format")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
