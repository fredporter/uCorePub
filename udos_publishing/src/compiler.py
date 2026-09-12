"""Clean Edition Compiler for sanitized, static publishing bundles.

Compiles vaults and notebook binders into sanitized, publication-ready editions.
Strips internal tags, local comment directives, and private author frontmatter
while preserving citations, evidence chains, and document structure.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional


def compile_edition_to_static(
    edition_markdown: str,
    title: str,
    edition_num: int = 1,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compile raw edition markdown into a clean static HTML file and markdown export."""
    # 1. Strip internal comment directives (e.g. <!-- section: REQ-001 -->)
    clean_md = re.sub(r"<!--\s*section:\s*[\w\-]+\s*-->\n?", "", edition_markdown).strip()

    # 2. Extract or strip private frontmatter
    if clean_md.startswith("---"):
        parts = clean_md.split("---", 2)
        if len(parts) >= 3:
            clean_md = parts[2].strip()

    sha256_hash = hashlib.sha256(clean_md.encode("utf-8")).hexdigest()

    # 3. Simple standalone HTML template
    # Replace markdown headers and blockquotes
    body_html = (
        clean_md.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    # Simple line-to-p conversion
    body_html = f"<pre style='white-space: pre-wrap; font-family: inherit;'>{clean_md}</pre>"

    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title} — Edition {edition_num}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 2rem auto; padding: 0 1rem; color: #1e293b; background: #f8fafc; }}
    .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 1rem; margin-bottom: 2rem; }}
    .badge {{ display: inline-block; background: #0284c7; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }}
    .meta {{ font-size: 0.85rem; color: #64748b; margin-top: 0.5rem; }}
  </style>
</head>
<body>
  <div class="header">
    <span class="badge">Edition {edition_num}</span>
    <h1>{title}</h1>
    <div class="meta">SHA-256: {sha256_hash}</div>
  </div>
  <main>
    {body_html}
  </main>
</body>
</html>
"""

    receipt: Dict[str, Any] = {
        "title": title,
        "edition": edition_num,
        "sha256": sha256_hash,
        "compiled_at": datetime.now(UTC).isoformat(),
        "sanitized": True,
    }

    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        html_file = out_path / "index.html"
        html_file.write_text(html_page, encoding="utf-8")

        md_file = out_path / f"edition_{edition_num}.clean.md"
        md_file.write_text(clean_md, encoding="utf-8")

        receipt["html_path"] = str(html_file)
        receipt["markdown_path"] = str(md_file)
        receipt_file = out_path / "receipt.json"
        receipt_file.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    return receipt
