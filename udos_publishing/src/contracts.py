"""Contracts for the publishing cloud mirror."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class PublishingMirrorContract:
    """Canonical guide origin, place edition mirror, and graphics origin."""

    guide_name: str = "udo.guide"
    place_name: str = "udo.place"
    frontmatter_keys: Tuple[str, ...] = ("title", "summary", "slug", "published_at")
    tag_keys: Tuple[str, ...] = ("tags", "categories")
    location_keys: Tuple[str, ...] = ("location", "region", "site")
    beacon_keys: Tuple[str, ...] = ("beacons", "signals")
    portal_keys: Tuple[str, ...] = ("portals", "targets")

    asset_name: str = "cdn.udo.guide"

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON-friendly representation of the contract."""

        return asdict(self)


def default_mirror_contract() -> PublishingMirrorContract:
    """Return the default contract used by the publishing service."""

    return PublishingMirrorContract()