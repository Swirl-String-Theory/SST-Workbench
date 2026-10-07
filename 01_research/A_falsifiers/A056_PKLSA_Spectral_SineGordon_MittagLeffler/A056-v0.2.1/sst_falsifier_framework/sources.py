from __future__ import annotations

EVIDENCE_CLASSES=("synthetic_control","simulation","independent_source","experimental")
REQUIRED_DYNAMIC_META=(
  "opaque_id","source_group","boundary","phase_definition_id","perturbation_id",
  "solver_id","provider_version","upstream_geometry_sha256","carrier_sha256","evidence_class"
)


def validate_dynamic_metadata(meta, synthetic=False):
    missing=[k for k in REQUIRED_DYNAMIC_META if not meta.get(k)]
    if synthetic:
        missing=[k for k in missing if k not in {"upstream_geometry_sha256","carrier_sha256"}]
    ec=meta.get("evidence_class")
    invalid=[] if ec in EVIDENCE_CLASSES else (["evidence_class"] if ec is not None else [])
    if synthetic and ec not in {None,"synthetic_control"}:
        invalid.append("synthetic_evidence_class")
    return {"pass":not missing and not invalid,"missing":missing,"invalid":invalid,"evidence_class":ec}
