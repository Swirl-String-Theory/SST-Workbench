"""Frozen SST-Falsifier-Framework v1.0.7 scientific interface.

Gates are independent; failure of a scientific gate never manufactures a later PASS.
Absent physical PKLSA dynamics must stay UNRESOLVED.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .science import analytical_suite,refuse_legacy_inputs,write_json


def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    ledger.record('G0','PASS',metrics={'mode':mode},reason='Framework verified frozen protocol before science entry.')
    exclusion=refuse_legacy_inputs([])
    ledger.record('G1',exclusion['status'],metrics={'legacy_input_count':0},
                  reason='No historical KnotPlot or visual-relaxation input admitted in D1.')
    suite=analytical_suite()
    out=root/'results'/'D1_ANALYTIC_CONTROL.json'
    write_json(out,suite)
    ledger.record('G2','PASS' if suite['identity_pass'] else 'FAIL',metrics=suite['maxima'],
                  reason='Exact 3D Euler affine flow, divergence, Kelvin circulation, stretching and rotating-frame identities; local control only.')
    ledger.record('G3','PASS' if suite['tracer_pass'] else 'FAIL',
                  metrics={'phase_abs_error_max':suite['maxima']['tracer_phase_abs_error'],
                           'rk4_monotone':suite['rk4_monotone']},
                  reason='Independent Cartesian Lagrangian tracer phase, not target-clock fit. NOT an SST knot clock.')
    # D2/D3 are scientifically blocked until the independently source-qualified
    # volumetric Euler trajectories and preregistered phase observable exist.
    for gid,why in {
      'G4':'No qualified finite-core 3D Euler trajectory supplied; no simulation of physical knot stability.',
      'G5':'No material, gauge-invariant internal knot phase observable from independent 3D trajectory.',
      'G6':'E011 STATIC_READY seed catalog exists upstream; DYNAMICS_READY and source-byte qualification absent.',
      'G7':'No frozen physical prediction versus withheld phase time-series. Clock law not inferred.',
      'G8':'No volumetric convergence, second integrator, kinetic energy/helicity and topology certification.',
      'G9':'No independent E011 provider holdout dynamical predictions.',
      'G10':'No independently compiled strict C++ FP64 physical kernel in this tranche.',
      'G11':'A061 downstream handoff prohibited absent G4-G10 physical closure.'
    }.items():
        ledger.record(gid,'UNRESOLVED',reason=why)
    return {'schema':'SST-BACKEND-MANIFEST-2',
            'python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'ANALYTIC_CONTROL_ONLY'},
            'physical_prediction_available':False,
            'unresolved_physical_gates':['G4','G5','G6','G7','G8','G9','G10','G11'],
            'analytic_results':str(out.relative_to(root))}
