# udos-publishing

Publishing contract and related utilities for the uCore ecosystem.

This repository owns the publishing cloud mirror boundary for `udo.guide` and `udo.place`.

It implements the publishing functionality including:

- Story creation with privacy and expiry semantics
- API endpoints for managing publishing content
- Publishing-specific store implementations
- Guide/place mirror contract and health surface
- Test coverage for contract compliance

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
