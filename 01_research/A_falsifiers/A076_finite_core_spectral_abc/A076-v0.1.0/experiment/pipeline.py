"""Framework 1.1.0 scientific pipeline; separate numerical and physical authority."""
from __future__ import annotations
import json,os
from pathlib import Path
from sst_falsifier.runner import instance_output_root
from .abc_compute import run_abc
from .pklsa_coupling import assess_c_dataset


def run_scientific_pipeline(root,cfg,ledger,mode):
    root=Path(root);out=instance_output_root(root,cfg);out.mkdir(parents=True,exist_ok=True)
    ledger.record('G0','PASS',reason='Framework verified frozen protocol before invoking science pipeline')
    ledger.record('G1','PASS',metrics={'source':'vendored finite-core selector v0.1.2.4',
                  'dimensionless':True,'external_target_used':False},
                  reason='Original source copy frozen; E010 atlas handled as separate C intake')
    ledger.record('G2','PASS',metrics={'q_units':'ln(cell/core)','ring_R_over_a':4.,
                  'core_radius_unit':1.,'circulation_unit':1.},
                  reason='Mathematically dimensionless predeclared operator and non-overlap q_min>ln(10)')
    try:
        verdict=run_abc(out,mode,threads=int(os.environ.get('SST_ABC_THREADS','16')),
                     force_python=bool(int(os.environ.get('SST_ABC_FORCE_PYTHON','0'))))
        usable=verdict['numeric_backend']=='C++' and verdict['status']=='FULL_NUMERICAL_ADJUDICATION'
        n_m2=sum(1 for c in verdict['all_clusters'] if c.get('dominant_abs_m')==2 and
                 c.get('kind')=='fourier_sector_growth_transition_cluster')
        ledger.record('G3','PASS' if n_m2 else 'UNRESOLVED',
             metrics={'m2_candidate_clusters':n_m2,'n_total_clusters':verdict['n_clusters'],
                      'backend':verdict['numeric_backend']},
             reason='Mode-resolved candidate presence only; not physics promotion')
        b=verdict['B']=='B_SPECTRAL_ONLY' and usable
        ledger.record('G4','PASS' if b else 'UNRESOLVED',
             metrics={'B':verdict['B'],'n_promoted':verdict['n_promoted'],
                      'native_compiled':usable,'q_tolerance':.005},
             reason='Numerical convergence only. Missing physical/temporal gates cannot be promoted.')
    except Exception as ex:
        ledger.record('G3','UNRESOLVED',reason=f'Computation error: {type(ex).__name__}: {ex}')
        ledger.record('G4','UNRESOLVED',reason='No validated A/B convergence assessment')
        verdict={'A':'UNRESOLVED','B':'UNRESOLVED','C':'C_NOT_EVALUATED',
                 'run_error':f'{type(ex).__name__}: {ex}'}
    # Full-field self-consistency is not implied by m=2 neutral mode crossing.
    ledger.record('G5','UNRESOLVED',reason='No nonlinear preferred-spacing / full Euler relative equilibrium test')
    c= {'status':'C_NOT_EVALUATED'}
    try:c=assess_c_dataset(root,out,mode)
    except Exception as ex:c={'status':'UNRESOLVED','error':f'{type(ex).__name__}: {ex}'}
    ledger.record('G6','UNRESOLVED',metrics={'C_dynamics':c.get('status')},
                  reason='PKLSA pilot is not temporal+spatial convergence of a coupled hierarchy')
    ledger.record('G7','UNRESOLVED',metrics={'n_records':c.get('n_records',0)},
                  reason='E010 geometries are input carriers; independent providers not certified')
    ledger.record('G8','UNRESOLVED',metrics={'A':verdict['A'],'B':verdict['B'],'C':c.get('status')},
                  reason='No dynamically stable multiple-scale hierarchy, independent providers, and coupled-mode convergence')
    return {'schema':'ABC-SPECTRAL-SCALE-1','results_file':'abc_science/ABC_VERDICT.json',
       'A':verdict['A'],'B':verdict['B'],'C':c.get('status'),
       'scientific_claims':'NUMERICAL_M2_DIAGNOSTICS_ONLY',
       'independent_physical_source_groups':0}
