"""Frozen provider contract for real PKLSA/Euler/finite-core dynamics.

A056 does not infer phase from a static XYZ curve. A producer must supply a
predeclared phase observable on a time/arclength grid plus immutable provenance,
including an evidence class for Gate-5 replication accounting.
"""
SCHEMA="A056-DYNAMIC-PROVIDER-3"
ALLOWED_PHASE_DEFINITIONS={
  "material_frame_torsion_phase_v1",
  "kelvin_mode_phase_v1",
  "provider_declared_phase_v1",
}
ALLOWED_EVIDENCE_CLASSES={"synthetic_control","simulation","independent_source","experimental"}
