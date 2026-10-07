from __future__ import annotations
REQUIRED_DYNAMIC_META=(
  "opaque_id","source_group","boundary","phase_definition_id","perturbation_id",
  "solver_id","provider_version","upstream_geometry_sha256","carrier_sha256"
)

def validate_dynamic_metadata(meta, synthetic=False):
    missing=[k for k in REQUIRED_DYNAMIC_META if not meta.get(k)]
    if synthetic:
        # Synthetic implementation controls have no physical upstream carrier.
        missing=[k for k in missing if k not in {"upstream_geometry_sha256","carrier_sha256"}]
    return {"pass":not missing,"missing":missing}
