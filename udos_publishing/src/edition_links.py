"""Review Vault wiki references against an explicit edition manifest."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import PurePosixPath
from typing import Iterable, Mapping

_WIKI_LINK = re.compile(r"(?P<embed>!)?\[\[(?P<reference>[^\]\n]+)\]\]")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_INLINE_CODE = re.compile(r"(?P<ticks>`+)(?!`).*?(?<!`)(?P=ticks)(?!`)")


def _note_key(path: str) -> str:
    value = path.strip().lstrip("/")
    return (value[:-3] if value.lower().endswith(".md") else value).casefold()


def preview_wiki_links(
    markdown: str,
    *,
    known_paths: Iterable[str],
    edition_manifest: Mapping[str, str],
    source_path: str = "",
) -> list[dict]:
    """Report references for an authorized preview. Only admitted targets get URLs."""
    by_path = defaultdict(set)
    by_name = defaultdict(set)
    for path in set(known_paths) | set(edition_manifest):
        key = _note_key(path)
        by_path[key].add(path)
        by_name[PurePosixPath(key).name].add(path)

    preview = []
    fence = None
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        delimiter = _FENCE.match(line)
        if fence:
            if delimiter and delimiter[1].startswith(fence) and not line[delimiter.end():].strip():
                fence = None
            continue
        if delimiter:
            fence = delimiter[1]
            continue
        for match in _WIKI_LINK.finditer(_INLINE_CODE.sub("", line)):
            reference, _, label = match["reference"].partition("|")
            target, _, anchor = reference.partition("#")
            key = _note_key(target or source_path)
            if "/" in target or not target:
                candidates = by_path.get(key, set())
            else:
                candidates = by_name.get(key, set())
            url = None
            if not candidates:
                status = "missing"
            elif len(candidates) > 1:
                status = "ambiguous"
            else:
                path = next(iter(candidates))
                url = edition_manifest.get(path)
                status = "included" if url else "outside_edition"
            preview.append({
                "line": line_number,
                "target": target.strip(),
                "anchor": anchor.strip(),
                "label": label.strip(),
                "embed": bool(match["embed"]),
                "status": status,
                "url": url,
            })
    return preview
