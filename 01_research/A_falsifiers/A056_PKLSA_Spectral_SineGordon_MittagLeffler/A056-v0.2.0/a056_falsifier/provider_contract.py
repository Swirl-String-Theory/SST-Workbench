"""Frozen provider contract for real PKLSA/Euler/finite-core dynamics.

A056 does not infer phase from a static XYZ curve.  A producer must supply a
predeclared phase observable on a time/arclength grid plus immutable provenance.
"""
SCHEMA="A056-DYNAMIC-PROVIDER-2"
ALLOWED_PHASE_DEFINITIONS={
  "material_frame_torsion_phase_v1",
  "kelvin_mode_phase_v1",
  "provider_declared_phase_v1",
}
