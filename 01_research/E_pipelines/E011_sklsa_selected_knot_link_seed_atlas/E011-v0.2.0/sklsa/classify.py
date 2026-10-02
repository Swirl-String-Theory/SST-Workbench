from __future__ import annotations

MIRROR_TOKEN = "MIRROR"
GENERATED_FAMILIES = {
    "ptsa", "ptsa_control", "siaf", "katlas_source_derived", "katlas_braid_derived",
    "knotplot_qhp", "knot_library_derived",
}
DERIVED_FAMILIES = {"ridgerunner", "knot_library_derived"}


def evidence_class(entry: dict) -> str:
    raw = str(entry.get("evidence_independence_class") or "").upper()
    family = str(entry.get("source_family") or "")
    role = str(entry.get("source_role") or "").lower()
    if MIRROR_TOKEN in raw or "mirror" in role or entry.get("raw_duplicate_of") or entry.get("geometry_duplicate_of"):
        return "MIRROR"
    if family in GENERATED_FAMILIES or role.startswith("generated"):
        return "GENERATED_OR_CONTROL"
    if family in DERIVED_FAMILIES or "derived" in role:
        return "DERIVED_NUMERICAL"
    if raw == "UPSTREAM_REFERENCE" or entry.get("contributes_new_upstream_provider") is True:
        return "UPSTREAM_INDEPENDENT"
    if entry.get("provider_group"):
        return "QUALIFIED_NONMIRROR"
    return "UNCLASSIFIED"


def contributes_to_scope(cls: str, scope: str) -> bool:
    if scope == "strict_upstream":
        return cls == "UPSTREAM_INDEPENDENT"
    if scope == "extended_qualified":
        return cls in {"UPSTREAM_INDEPENDENT", "QUALIFIED_NONMIRROR", "DERIVED_NUMERICAL", "GENERATED_OR_CONTROL"}
    raise ValueError(scope)
