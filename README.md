# udos-publishing

Publishing contract and related utilities for the uCore ecosystem.

This repository implements the publishing functionality including:
- Story creation with privacy and expiry semantics
- API endpoints for managing publishing content
- Publishing-specific store implementations
- Test coverage for contract compliance

## Repository Structure

```
/
├── src/
│   ├── __init__.py
│   ├── publishing.py      # Core publishing service
│   ├── stores.py          # Story storage with privacy controls
│   └── routes.py          # API route definitions
├── tests/
│   └── test_publishing.py # Initial test suite
├── pyproject.toml
├── package.json
└── README.md
```

## Getting Started

```bash
# Install dependencies
npm install

# Run tests
npm test
```

## License

MIT