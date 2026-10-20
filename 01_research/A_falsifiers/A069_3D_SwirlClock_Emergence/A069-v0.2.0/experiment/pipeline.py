"""Framework v1.0.9 science hook. Evidence classes are never aggregated as a physics support vote."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json,hashlib
from .science import analytical_suite,refuse_legacy_inputs,write_json
from .columnar import columnar_suite

def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    ledger.record('G0','PASS',reason='Official v1.0.9 framework verified frozen byte-exact protocol before science hook.')
    old=root/'sources/A069_v0.1.0/D1_ANALYTIC_CONTROL.json'
    frozen=json.loads((root/'configs/BLIND_ANALYTIC_CONTROL_V020.json').read_text())
    actual=hashlib.sha256(old.read_bytes()).hexdigest() if old.is_file() else None
    inherited=actual==frozen['baseline_sha256']
    old_data=json.loads(old.read_text()) if inherited else {}
    control=analytical_suite();smooth=columnar_suite()
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    write_json(out/'D1_ANALYTIC_CONTROL_V020.json',control)
    write_json(out/'D2A_SMOOTH_COLUMNAR_CONTROL.json',smooth)
    exclusions=refuse_legacy_inputs([str(old)])
    ledger.record('G1','PASS' if exclusions['status']=='PASS' else 'FAIL',metrics={'legacy_data_admitted':False},reason='D1 inherited synthetic analytic control only; old KnotPlot/VortexLab inputs not admitted.')
    ledger.record('G2','PASS' if control['identity_pass'] else 'FAIL',metrics=control['maxima'],reason='D1 exact affine Euler and Kelvin identities.')
    ledger.record('G3','PASS' if control['tracer_pass'] else 'FAIL',metrics={'phase_err':control['maxima']['tracer_phase_abs_error']},reason='D1 Cartesian phase identity; not an SST clock.')
    ledger.record('G12','PASS' if smooth['status']=='PASS' else 'FAIL',metrics=smooth['maxima'],reason='Exact smooth stationary 2D columnar Euler embedded in 3D, finite energy per axial length, not knotted dynamics.')
    ledger.record('G13','PASS' if smooth['rk4_monotone'] else 'FAIL',metrics={'rk4_monotone':smooth['rk4_monotone'],'phase_err':smooth['maxima']['phase_absolute_error']},reason='Independent Cartesian tracer solver, RK4 vs midpoint and step refinements, not a clock eigenmode.')
    old_max=(old_data.get('maxima') or {})
    keys=('tracer_phase_abs_error','frame_reconstruction_error','circulation_relative_error')
    comparable=all(k in old_max and abs(old_max[k]-control['maxima'][k])<=1e-12 for k in keys)
    ledger.record('G14','PASS' if inherited and comparable else 'FAIL',metrics={'sha256_verified':inherited,'recomputed_agreement':comparable},reason='Inherited analytic dataset byte hash compared with frozen SHA and regenerated D1 reference; no new experimental source.')
    why={'G4':'No fully 3D, finite-length, finite-core PKLSA Euler trajectory; D2A is columnar only.',
         'G5':'No independently identified stable knot-internal material phase observable.',
         'G6':'E010/E011 real SHA-verified dynamical provider not supplied; STATIC_READY is not DYNAMICS_READY.',
         'G7':'No preregistered physical clock-rate holdout predictions; analytic azimuth is only a tracer.',
         'G8':'No full 3D pressure-Poisson/energy/helicity/core and long-time convergence qualification.',
         'G9':'No provider-independent PKLSA physics holdout; physical reveal forbidden.',
         'G10':'No independently compiled physical C++ FP64 dynamical kernel (minimal reference profile).',
         'G11':'A061 science handoff prohibited without G4-G10.'}
    for gid,reason in why.items():
        if not ledger.defs[gid].enabled:ledger.record(gid,'NOT_APPLICABLE',reason='Minimal framework profile disables '+gid+'; '+reason)
        else:ledger.record(gid,'UNRESOLVED',reason=reason)
    return {'schema':'SST-BACKEND-MANIFEST-2','framework_target':'1.0.9',
            'actual_backend':'python-numpy-fp64','precision':'float64','authority':'ANALYTIC_CONTROL_ONLY',
            'no_native_backend_claim':True,'D1_status':control['status'],'D2A_status':smooth['status'],
            'physical_pklsa_status':'UNRESOLVED','physical_clock_prediction':False,
            'old_dataset_sha256':actual}
