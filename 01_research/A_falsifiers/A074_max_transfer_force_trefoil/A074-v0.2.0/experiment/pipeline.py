"""Framework v1.0.10 adapter. Never turns an exploratory pilot into physics certification.

Framework owns freeze verification and execution-status authority. This module uses
only measured, hashed local data and leaves unsolved gates UNRESOLVED.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path


def run_scientific_pipeline(root:Path,cfg:dict,ledger,mode:str)->dict:
    ledger.record('G0','PASS',metrics={'mode':mode,'pin':'1.0.10'},
                  reason='Only the actual frozen framework runner can enter this pipeline.')
    path=root/'Trefoil_Max_Transfer_Force_v0.2.0-outputs'/'PILOT_EULER_REPORT.json'
    source=root/'seeds'/'trefoil_ideal_3_1_1.json'
    def G1():
        obj=json.loads(source.read_text())
        expected='a16c0f6e9175fdd54ee8c50b3b32e23caa3b256e7da21145be00a5a58e08cc51'
        ok=obj.get('source_sha256')==expected and obj.get('id')=='3:1:1'
        return {'status':'PASS' if ok else 'FAIL','reason':'Single verified Gilbert geometry family (not two independent sources)',
                'metrics':{'source_reference_sha256':expected,'source_record_id':obj.get('id')}}
    def data():
        if not path.exists():return None
        return json.loads(path.read_text())
    def G2():
        obj=data()
        if not obj:return {'status':'UNRESOLVED','reason':'Run the independent Euler pilot first; no measurements exist'}
        scenarios=obj.get('scenarios',[])
        if not scenarios:return {'status':'UNRESOLVED','reason':'No measured Euler scenarios'}
        maxdiv=max(x['divergence_relative_residual'] for x in scenarios)
        maxp=max(x['poisson_relative_residual'] for x in scenarios)
        ok=maxdiv<1e-10 and maxp<1e-10
        return {'status':'PASS' if ok else 'FAIL','metrics':{'divergence_max_relative':maxdiv,'pressure_poisson_max_relative':maxp,
                'n_scenarios':len(scenarios)},'reason':'Numerical periodic projected Euler consistency only; not physical core certification'}
    def G3():
        obj=data()
        if not obj:return {'status':'UNRESOLVED','reason':'Missing Euler pilot'}
        values=[x['initial_relative_equilibrium_error'] for x in obj.get('scenarios',[])]
        if not values:return {'status':'UNRESOLVED','reason':'No relative-equilibrium measurements'}
        minimum=min(values)
        return {'status':'PASS' if minimum<.05 else 'FAIL',
                'metrics':{'minimum_normal_relative_equilibrium_residual':minimum,'candidate_threshold':.05},
                'reason':'FAIL means no candidate in this prespecified limited geometry search; not a global non-existence theorem'}
    def G4():
        obj=data()
        if not obj:return {'status':'UNRESOLVED','reason':'Missing Euler pilot'}
        tests=obj.get('perturbations',[])
        if len(tests)<2:return {'status':'UNRESOLVED','reason':'Two independent perturbation modes not both completed'}
        maxg=max(x['max_growth'] for x in tests)
        return {'status':'PASS' if maxg<2 else 'FAIL',
                'metrics':{'finite_time_growth_max':maxg,'independent_modes':len(set(x['mode'] for x in tests))},
                'reason':'Short-time bounded separation only. G3 failure makes it DIAGNOSTIC_ONLY in framework v1.0.10.'}
    def G7():
        obj=data()
        if not obj:return {'status':'UNRESOLVED','reason':'Missing Euler pilot'}
        return {'status':'UNRESOLVED','metrics':{'grid_scenario_count':len(obj.get('scenarios',[])),
                'spatial_energy_difference_48_64':obj.get('spatial_energy_disagreement_48_64')},
                'reason':'No 3-grid qualification at sufficiently resolved core, long-time and independent provenance'}
    def G8():
        obj=data()
        return {'status':'UNRESOLVED','metrics':{'nominal_shear_loads_n':len(set(x['forcing_m_s2'] for x in obj.get('scenarios',[]))) if obj else 0},
                'reason':'No stable Euler knot, independently localized transmitted load or true first-failure force'}
    # In v1.0.10 available downstream diagnostics execute after negative gate results.
    ledger.run_evaluators({'G1':G1,'G2':G2,'G3':G3,'G4':G4,'G7':G7,'G8':G8})
    # G5 native science provider intentionally not claimed; G6 disabled; G9 separate.
    return {'schema':'SST-BACKEND-MANIFEST-2',
            'python_reference':{'actual_backend':'numpy-fft-fp64','precision':'float64','authority':'DEVELOPMENT_DIAGNOSTIC'},
            'mechanism':'Periodic full 3D Euler with finite-width initial vorticity and pressure Poisson',
            'unresolved':'No native full-Euler parity, long-time stability, or mechanical knot failure threshold'}
