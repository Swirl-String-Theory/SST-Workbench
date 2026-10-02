from __future__ import annotations

KNOWN_LINK_CATALOG: dict[str, dict] = {
    "L6a4": {
        "common_name": "Borromean rings",
        "identity_status": "[CATALOG] Standard link-table identity supplied by the project owner.",
        "higher_invariant_family": "Milnor triple-linking / mu-bar_123",
        "higher_invariant_computed": False,
    },
}


def known_link_metadata(link_id: str) -> dict:
    row = KNOWN_LINK_CATALOG.get(str(link_id), {})
    return {
        "common_name": row.get("common_name"),
        "identity_status": row.get("identity_status", "No common-name catalog entry in this release."),
        "higher_invariant_family": row.get("higher_invariant_family"),
        "higher_invariant_computed": bool(row.get("higher_invariant_computed", False)),
    }
