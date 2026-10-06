from __future__ import annotations

# v0.1.1 feature-domain registry.  Pair-space and reveal permissions are
# preregistered here and mirrored in PREREGISTRATION.md.
FEATURE_REGISTRY = {
    "bend_energy": {
        "label": "discrete bending-energy proxy",
        "pair_spaces": ["common_all", "knots", "links"],
        "ratio_pools": ["knots", "links", "all"],
        "requires_positive_for_ratio": True,
    },
    "abs_neumann_energy": {
        "label": "absolute regularized Neumann line-integral proxy",
        "pair_spaces": ["common_all", "knots", "links"],
        "ratio_pools": ["knots", "links", "all"],
        "requires_positive_for_ratio": True,
    },
    "min_distance": {
        "label": "minimum non-local distance after common length normalization",
        "pair_spaces": ["common_all", "knots", "links"],
        "ratio_pools": ["knots", "links", "all"],
        "requires_positive_for_ratio": True,
    },
    "abs_writhe": {
        "label": "absolute component-self-writhe proxy",
        "pair_spaces": ["knots", "links"],
        "ratio_pools": ["knots", "links"],
        "requires_positive_for_ratio": True,
        "mixed_pool_forbidden_reason": "self-writhe aggregate is not the same observable for one- and multi-component objects",
    },
    "linking_strength": {
        "label": "sum of absolute pairwise Gauss-linking proxies",
        "pair_spaces": ["links"],
        "ratio_pools": ["links"],
        "requires_positive_for_ratio": True,
        "knot_forbidden_reason": "single-component knots have no pairwise linking observable",
        "mixed_pool_forbidden_reason": "zero-by-definition knot values would create an artificial dynamic range",
    },
    "contact_ratio": {
        "label": "minimum-distance / mean-segment diagnostic",
        "pair_spaces": [],
        "ratio_pools": [],
        "diagnostic_only": True,
        "excluded_reason": "explicitly resolution dependent because mean segment length changes with N",
    },
}

PAIR_SPACES = {
    "common_all": {
        "pool": "all",
        "features": ["bend_energy", "abs_neumann_energy", "min_distance"],
        "description": "cross-type distance using only observables with common knot/link semantics",
    },
    "knots": {
        "pool": "knots",
        "features": ["bend_energy", "abs_neumann_energy", "min_distance", "abs_writhe"],
        "description": "knot-only distance",
    },
    "links": {
        "pool": "links",
        "features": ["bend_energy", "abs_neumann_energy", "min_distance", "abs_writhe", "linking_strength"],
        "description": "link-only distance including pairwise linking information",
    },
}

PRIMARY_FEATURES = [
    "bend_energy",
    "abs_neumann_energy",
    "min_distance",
    "abs_writhe",
    "linking_strength",
]

DIAGNOSTIC_FEATURES = ["contact_ratio"]


def applicable_to_kind(feature: str, kind: str) -> bool:
    if feature == "linking_strength" and kind == "knot":
        return False
    return feature in FEATURE_REGISTRY


def pool_rows(rows, pool: str):
    if pool == "all":
        return list(rows)
    if pool == "knots":
        return [r for r in rows if r["kind"] == "knot"]
    if pool == "links":
        return [r for r in rows if r["kind"] == "link"]
    raise ValueError(f"unknown pool: {pool}")
