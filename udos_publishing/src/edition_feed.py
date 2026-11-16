"""Render a feed preview from a reviewed public edition manifest."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

from .feed_codec import Feed, FeedItem, render_feed


def _public_url(value):
    if not isinstance(value, str):
        raise ValueError("Expected an absolute HTTPS publication URL")
    url = urlsplit(value)
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError("Expected an absolute HTTPS publication URL")
    return value


def reviewed_articles(manifest, edition_root):
    """Read the exact approved public revisions named by the manifest."""
    return _reviewed_files(manifest, edition_root, "items", ".md", "article")


def reviewed_datasets(manifest, edition_root):
    """Read approved JSON objects packaged as reference data."""
    datasets = _reviewed_files(manifest, edition_root, "datasets", ".json", "dataset")
    for _, path, payload in datasets:
        try:
            content = json.loads(payload.decode("utf-8"), parse_constant=_reject_constant)
        except ValueError as exc:
            raise ValueError(f"Invalid edition dataset: {path}") from exc
        if not isinstance(content, dict):
            raise ValueError(f"Edition dataset must be a JSON object: {path}")
    return datasets


def _reject_constant(value):
    raise ValueError(f"Invalid JSON constant: {value}")


def _reviewed_files(manifest, edition_root, collection, suffix, kind):
    if manifest.get("schema_version") != 1 or manifest.get("visibility") != "public":
        raise ValueError("Expected a version 1 public edition manifest")
    root = Path(edition_root).resolve(strict=True)
    files = []
    paths = set()
    records = manifest["items"] if collection == "items" else manifest.get(collection, [])
    for record in records:
        if record.get("visibility") != "public" or record.get("review_status") != "approved":
            continue
        relative = Path(record["path"])
        if relative.is_absolute() or ".." in relative.parts or relative.suffix != suffix:
            raise ValueError(f"Edition {kind} requires a relative {suffix} path")
        source = root / relative
        resolved = source.resolve(strict=True)
        if resolved != source or not resolved.is_file():
            raise ValueError(f"Edition {kind} is outside its declared path: {relative}")
        if resolved in paths:
            raise ValueError(f"Duplicate edition {kind}: {relative}")
        paths.add(resolved)
        payload = resolved.read_bytes()
        if hashlib.sha256(payload).hexdigest() != record["sha256"]:
            raise ValueError(f"Edition {kind} revision changed: {relative}")

        files.append((record, relative, payload))
    return files


def preview_edition_feed(manifest, edition_root, wire_format):
    """Use reviewed excerpts and verify each included article's pinned bytes."""
    articles = reviewed_articles(manifest, edition_root)
    return render_reviewed_feed(manifest, articles, wire_format)


def render_reviewed_feed(manifest, articles, wire_format):
    items = []
    for record, relative, _ in articles:
        excerpt = record["excerpt"]
        tags = record.get("tags", [])
        if not isinstance(excerpt, str) or not excerpt.strip() or not isinstance(tags, list):
            raise ValueError(f"Expected a reviewed text excerpt and tag list: {relative}")
        items.append(FeedItem(
            uid=record["uid"], title=record["title"], url=_public_url(record["url"]),
            text=excerpt, published=record.get("published", ""),
            updated=record.get("updated", ""), tags=tuple(tags),
        ))

    feed = Feed(manifest["title"], _public_url(manifest["home_url"]), tuple(items),
                manifest.get("description", ""))
    return render_feed(
        feed, wire_format, feed_url=_public_url(manifest["feed_urls"][wire_format]),
        updated=manifest["updated"], author=manifest["author"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--edition-root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--format", choices=("rss", "atom", "json"))
    mode.add_argument("--package", type=Path, help="Build a new offline library directory")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_bytes())
        if args.package:
            from .compiler import compile_reviewed_library

            compile_reviewed_library(manifest, args.edition_root, args.package)
            return
        payload = preview_edition_feed(manifest, args.edition_root, args.format)
    except (AttributeError, KeyError, OSError, TypeError, ValueError) as exc:
        parser.exit(1, f"Edition feed preview failed: {exc}\n")
    sys.stdout.buffer.write(payload)


if __name__ == "__main__":
    main()
