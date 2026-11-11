# uCore-Publish

Publishing contract, clean edition compilation, and related utilities for the uCore/uDOS ecosystem.

This repository owns clean edition static compilation, offline vault export, and the publishing cloud mirror boundary for `udo.guide` and `udo.place`.

## Capabilities

`uCore-Publish` provides the outbound edition compilation and multi-target publishing pipeline:

- **Clean Edition Compiler:** Compiles vaults and notebook binders into sanitized, publication-ready editions. Strips internal tags, local filesystem paths, and private author frontmatter while preserving citations and evidence chains.
- **Static Export Engines:** Exports clean editions to Quartz, Jekyll, and portable Markdown libraries for offline distribution.
- **Headless WordPress Commercial Cloud Arm:** Opt-in Python adapter that sends reviewed posts to a selected HTTPS WordPress site and checks the returned post ID and status. Callers select existing categories and tags by ID.
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

- Pass `enabled=True` to `WordPressCloudAdapter` with a selected HTTPS site URL and an application password obtained through the caller's credential store. Multisite callers use the target site's full URL. The default post status is draft.
- The adapter is a library entry point. uCore role checks, destination review, and live staging qualification are needed before exposing it in a runtime publishing surface. If delivery is unconfirmed, check the destination before retrying.

## License

MIT
