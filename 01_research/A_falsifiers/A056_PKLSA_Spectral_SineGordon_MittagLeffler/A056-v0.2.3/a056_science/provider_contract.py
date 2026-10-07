from __future__ import annotations
from typing import Any

SCHEMA="A056-DYNAMIC-PROVIDER-4"
ALLOWED_PHASE_DEFINITIONS={
    "material_frame_torsion_phase_v1",
    "kelvin_mode_phase_v1",
    "provider_declared_phase_v1",
}
ALLOWED_EVIDENCE_CLASSES={"synthetic_control","simulation","independent_source","experimental"}
BASE_REQUIRED={
    "opaque_id","source_group","boundary","phase_definition_id","perturbation_id",
    "solver_id","provider_version","evidence_class",
}
PHYSICAL_REQUIRED={"independence_unit","provenance_family","upstream_geometry_sha256","carrier_sha256"}


def validate_dynamic_metadata(meta: dict[str,Any], synthetic: bool=False) -> dict[str,Any]:
    missing=sorted(k for k in BASE_REQUIRED if not meta.get(k))
    if not synthetic:
        missing += sorted(k for k in PHYSICAL_REQUIRED if not meta.get(k))
    errors=[]
    if meta.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    if meta.get("boundary") not in {"periodic","open"}:
        errors.append("boundary must be periodic or open")
    if meta.get("phase_definition_id") not in ALLOWED_PHASE_DEFINITIONS:
        errors.append("phase_definition_id is not preregistered")
    if meta.get("evidence_class") not in ALLOWED_EVIDENCE_CLASSES:
        errors.append("invalid evidence_class")
    if synthetic and meta.get("evidence_class") != "synthetic_control":
        errors.append("synthetic=true requires evidence_class=synthetic_control")
    return {"schema":"A056-PROVIDER-CONTRACT-CHECK-4","pass":not missing and not errors,
            "missing":missing,"errors":errors}
