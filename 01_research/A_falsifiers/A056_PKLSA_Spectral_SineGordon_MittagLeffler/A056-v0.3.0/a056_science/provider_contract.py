from __future__ import annotations
from typing import Any

SCHEMA="A056-DYNAMIC-PROVIDER-5"
ALLOWED_PHASE_DEFINITIONS={
    "paired_kelvin_residual_phase_v1",
    "material_frame_torsion_phase_v1",
    "kelvin_mode_phase_v1",
    "provider_declared_phase_v1",
}
ALLOWED_RINGDOWN_DEFINITIONS={
    "paired_kelvin_mode_envelope_v1",
    "provider_zero_baseline_observable_v1",
    "derived_pod_energy_v1",
}
ALLOWED_EVIDENCE_CLASSES={"synthetic_control","simulation","independent_source","experimental"}
BASE_REQUIRED={
    "opaque_id","source_group","boundary","phase_definition_id","ringdown_definition_id",
    "perturbation_id","solver_id","provider_version","evidence_class",
}
NON_SYNTH_REQUIRED={"independence_unit","provenance_family","upstream_geometry_sha256","carrier_sha256"}
SIMULATION_REQUIRED={"provider_case_family","resolution_value","resolution_unit","provider_numerically_valid"}


def validate_dynamic_metadata(meta: dict[str,Any], synthetic: bool=False) -> dict[str,Any]:
    missing=sorted(k for k in BASE_REQUIRED if meta.get(k) is None or meta.get(k)=="")
    if not synthetic:
        missing += sorted(k for k in NON_SYNTH_REQUIRED if meta.get(k) is None or meta.get(k)=="")
    if meta.get("evidence_class")=="simulation":
        missing += sorted(k for k in SIMULATION_REQUIRED if meta.get(k) is None or meta.get(k)=="")
    errors=[]
    if meta.get("schema") != SCHEMA: errors.append(f"schema must be {SCHEMA}")
    if meta.get("boundary") not in {"periodic","open"}: errors.append("boundary must be periodic or open")
    if meta.get("phase_definition_id") not in ALLOWED_PHASE_DEFINITIONS: errors.append("phase_definition_id is not preregistered")
    if meta.get("ringdown_definition_id") not in ALLOWED_RINGDOWN_DEFINITIONS: errors.append("ringdown_definition_id is not preregistered")
    if meta.get("evidence_class") not in ALLOWED_EVIDENCE_CLASSES: errors.append("invalid evidence_class")
    if synthetic and meta.get("evidence_class") != "synthetic_control": errors.append("synthetic=true requires evidence_class=synthetic_control")
    if meta.get("evidence_class")=="simulation" and meta.get("provider_numerically_valid") is not True:
        errors.append("simulation provider_numerically_valid must be true")
    return {"schema":"A056-PROVIDER-CONTRACT-CHECK-5","pass":not missing and not errors,"missing":sorted(set(missing)),"errors":errors}
