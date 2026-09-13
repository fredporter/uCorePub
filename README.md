# uCore-Publish

Publishing contract, clean edition compilation, and related utilities for the uCore/uDOS ecosystem.

This repository owns clean edition static compilation, offline vault export, and the publishing cloud mirror boundary for `udo.guide` and `udo.place`.

## Capabilities

`uCore-Publish` provides the outbound edition compilation and multi-target publishing pipeline:

- **Clean Edition Compiler:** Compiles vaults and notebook binders into sanitized, publication-ready editions. Strips internal tags, local filesystem paths, and private author frontmatter while preserving citations and evidence chains.
- **Static Export Engines:** Exports clean editions to Quartz, Jekyll, and portable Markdown libraries for offline distribution.
- **Headless WordPress Commercial Cloud Arm:** Outbound publishing adapter pushing clean editions to hosted WordPress / WordPress Multisite environments via the WordPress REST API (creating posts, pages, categories, tags, and media attachments).
- **Sovereign Mirror Contracts:** Guide and place mirror boundaries for `udo.guide` and `udo.place`.
- **Privacy & Expiry Semantics:** Enforces public vs shared vs private access controls and expiration dates before any document leaves the local environment.

## Repository Structure

```text
/
|- udos_publishing/
|  |- __init__.py
|  `- src/
|     |- contracts.py  # Guide/place mirror contract
|     |- publishing.py # Core publishing service
|     |- routes.py     # API route definitions
|     `- stores.py     # Story storage with privacy controls
|- tests/
|  |- __init__.py
|  `- test_publishing.py # Initial test suite
|- ucore-extension.json  # Plugin manifest scaffold for uCore discovery
|- pyproject.toml
|- package.json
`- README.md
```

## Getting Started

```bash
python3 -m unittest discover
```

## Notes

- This repo is intentionally scaffold-first for the current phase; deeper production behavior is tracked in the next execution plan.

## License

MIT
