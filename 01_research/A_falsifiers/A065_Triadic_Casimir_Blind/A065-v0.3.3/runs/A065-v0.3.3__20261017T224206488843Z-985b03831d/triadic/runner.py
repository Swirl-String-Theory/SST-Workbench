"""Self-contained non-certifying reference runner; independent seals for D01/D02/D03."""
from __future__ import annotations
import argparse, json, math, pathlib, hashlib, sys
from .security import readjson,writejson,sha,canon,verify_all
from . import physics as f
from .pklsa import bridge as run_pklsa

ROOT=pathlib.Path(__file__).resolve().parent.parent


def gate(name,ok,metric,limit=None,claim='synthetic_control'):
    return {'gate':name,'status':'PASS' if ok else 'FAIL','metric':metric,'limit':limit,'claim_class':claim}


def run_d01(root):
    d=readjson(root/'data'/'D01_EULER'/'cases.json')
    rows=[];gates=[];errs=[];zero_pot=[];different_clocks=[]
    for case in d['cases']:
        z=f.euler_snapshot(case)
        error=abs(z['pressure_poisson_rhs']-z['pressure_laplacian'])
        errs.append(error)
        rows.append({'case':case['name'],'point':case['point'],'divergence':z['divergence'],'omega2':z['omega2'],'strain2':z['strain2'],'poisson_error':error,'clock_N':z['clock_N']})
        if case['name']=='potential_stagnation':zero_pot.append(z['omega2'])
        if case['name']=='rigid_rotation':different_clocks.append(z['clock_N'])
    gates.append(gate('D01_G01_EULER_DIV',max(abs(r['divergence']) for r in rows)<1e-12,max(abs(r['divergence']) for r in rows),1e-12))
    gates.append(gate('D01_G02_POISSON',max(errs)<1e-12,max(errs),1e-12))
    gates.append(gate('D01_G03_POTENTIAL_NULL',max(zero_pot)<1e-12 and min(r['strain2'] for r in rows if r['case']=='potential_stagnation')>0,max(zero_pot),1e-12))
    # Irrotational need not imply uniform proposed clock factor: this analytic flow explicitly varies.
    cvals=[r['clock_N'] for r in rows if r['case']=='potential_stagnation']
    variation=max(cvals)-min(cvals)
    gates.append(gate('D01_G04_IRROTATIONAL_CLOCK_VARIATION',variation>1e-5,variation,1e-5))
    pklsa=run_pklsa(root)
    from .dynamics import run as run_dynamics
    from .providers import check as check_provider
    dynamics=run_dynamics(root)
    provider=check_provider(root)
    gates.append(gate('D01_G07_FILAMENT_RK4_DT_HALVING',dynamics['numerical_gate']=='PASS',
                      dynamics['relative_discretization_error'],0.001))
    gates.append(gate('D01_G08_FILAMENT_SPATIAL_REFINEMENT',
                      dynamics['spatial_75_150_relative_displacement']<0.05,
                      dynamics['spatial_75_150_relative_displacement'],0.05))
    gates.append(gate('D01_G09_FILAMENT_SPATIAL_150_300',
                      dynamics['spatial_150_300_relative_displacement']<0.05,
                      dynamics['spatial_150_300_relative_displacement'],0.05))
    gates.append(gate('D01_G10_FILAMENT_SPATIAL_75_300',
                      dynamics['spatial_75_300_relative_displacement']<0.05,
                      dynamics['spatial_75_300_relative_displacement'],0.05))
    pklsa_ok=pklsa['stats']['points']==300 and pklsa['source_provider_count']==1
    gates.append(gate('D01_G05_PKLSA_SOURCE_INTEGRITY',pklsa_ok,pklsa['stats']['points'],300))
    gates.append(gate('D01_G06_PKLSA_FINITE_BIOTSAVART',all(math.isfinite(t) for row in pklsa['fields'] for t in row['velocity_300']),pklsa['max_refinement_error'],'finite'))
    # Provider readiness is deliberately a separate OPEN gate, never counted as a false PASS.
    return {'dataset_id':'D01_EULER','rows':rows,'pklsa':pklsa,'filament_dynamics':dynamics,
            'second_provider_readiness':provider,'gates':gates,
            'open_qualifications':['FULL_EULER_TIME_DEPENDENT_VALIDATION','SECOND_PROVIDER_DYNAMICS_REQUIRED','PKLSA_KELVIN_FLOQUET_MODES','ATOM_LINK_COUPLING','WALL_BOUNDARY_PRESSURE'],
            'scope':'analytic controls + authentic N300 trefoil + simulated regularized filament ODE; NOT 3D Euler certification'}


def run_d02(root):
    d=readjson(root/'data'/'D02_CLOCK_LINK'/'single_surface.json');graph=d['graph']
    path1=[0,1,2];path2=[0,2]
    theta=f.phase_path(graph,path1);theta2=f.phase_path(graph,path2)
    rate=f.phase_path_rate(graph,path1);rate2=f.direct_phase_rate(graph,path1)
    transformed=f.gauge_transform(graph,[.6,-.3,.2])
    err=abs(theta-f.phase_path(transformed,path1))
    # Closed-loop holonomy must equal difference of two open-path comparisons.
    loop=theta-theta2
    expected=-(graph['edges'][0]['vartheta']+graph['edges'][1]['vartheta']-graph['edges'][2]['vartheta'])
    errs=[];rows=[];gates=[]
    for name,s in d['surfaces'].items():
        for xi in d['imaginary_frequencies']:
            chi=f.susceptibility(s,xi)
            lam=f.effective_stiffness(s,xi)
            rows.append({'surface':name,'xi':xi,'chi':chi,'lambda_eff':lam})
            if s['kind']!='decoupled':errs.append(chi)
    gates.append(gate('D02_G01_GAUGE',err<1e-12,err,1e-12))
    gates.append(gate('D02_G02_PHASE_RATE',abs(rate-rate2)<1e-12,abs(rate-rate2),1e-12))
    gates.append(gate('D02_G03_HOLONOMY',abs(loop-expected)<1e-12,abs(loop-expected),1e-12))
    gates.append(gate('D02_G04_RESPONSE_POSITIVE',all(r['chi']>=-1e-14 for r in rows),min(r['chi'] for r in rows),0.0))
    gates.append(gate('D02_G05_SHEET_STABLE',all(r['lambda_eff']>0 for r in rows if r['surface']!='C'),min(r['lambda_eff'] for r in rows if r['surface']!='C'),0.0))
    gates.append(gate('D02_G06_NO_RESPONSE_CONTROL',abs(f.reflection(d['surfaces']['C'],1.0))<1e-14, f.reflection(d['surfaces']['C'],1.0),1e-14))
    return {'dataset_id':'D02_CLOCK_LINK','gauge_phase':theta,'path_holonomy':loop,'phase_rate':rate,'rows':rows,'gates':gates,'scope':'gauge/oscillator/sheet toy, not derived matter-link coupling'}


def run_d03(root):
    conditions=readjson(root/'data'/'D03_TWO_SURFACE'/'conditions.json')
    surfaces=readjson(root/'data'/'D02_CLOCK_LINK'/'single_surface.json')['surfaces']
    rows=[];gates=[];max_mismatch=0.;negative_nonnull=0;total_nonnull=0
    for case in conditions['cases']:
        a=case['distance'];T=case['temperature_dimensionless'];s1=surfaces[case['surface_1']];s2=surfaces[case['surface_2']]
        e=f.free_energy_area(a,T,s1,s2)
        p=f.pressure_traction(a,T,s1,s2)
        fd=f.pressure_finite_diff(a,T,s1,s2)
        rel=abs(p-fd)/max(1e-11,abs(p))
        max_mismatch=max(max_mismatch,rel)
        row={**case,'free_energy_area':e,'stress_pressure':p,'pressure_from_energy':fd,'force_energy_relative_residual':rel}
        rows.append(row)
        if case['surface_1']!='C' and case['surface_2']!='C':
            total_nonnull+=1
            if p<0:negative_nonnull+=1
    nullmax=max(abs(r['stress_pressure'])+abs(r['free_energy_area']) for r in rows if 'C' in [r['surface_1'],r['surface_2']])
    gates.append(gate('D03_G01_ENERGY_STRESS',max_mismatch<=0.015,max_mismatch,0.015))
    gates.append(gate('D03_G02_DECOUPLED_NULL',nullmax<1e-13,nullmax,1e-13))
    # Nonzero stress is a toy-model diagnostic, not a target force sign/scale certification.
    gates.append(gate('D03_G03_FINITE_TOY_RESPONSE',total_nonnull>0 and negative_nonnull==total_nonnull, {'negative':negative_nonnull,'total':total_nonnull},'all toy coupled configurations'))
    diagnostics=[]
    for pair in [('A','B'),('B','B')]:
        for T in [.8,1.6]:
            sub=[r for r in rows if (r['surface_1'],r['surface_2'])==pair and r['temperature_dimensionless']==T]
            diagnostics.append({'pair':list(pair),'temperature':T,'free_fitted_exponent':f.slope_powerlaw(sub)})
    return {'dataset_id':'D03_TWO_SURFACE','rows':rows,'gates':gates,'free_exponents_not_targets':diagnostics,'scope':'classical thermal scalar toy interaction, independent force method checks; NOT physical EM Casimir'}


def verify_predictions_against_commit(root):
    verifies=verify_all(root)
    for ds in verifies:
        fp=root/'outputs'/'BLIND'/f'{ds}.json'
        if not fp.is_file():raise RuntimeError('missing blind output '+ds)
    summary_path=root/'outputs'/'BLIND'/'RUN_SUMMARY.json';summary=readjson(summary_path)
    rootcommit=readjson(root/'seals'/'GLOBAL_COMMITMENT.json')
    if summary['seals']!=rootcommit['seals']:raise RuntimeError('blind outputs not bound to precommitted datasets')
    digestmap={d:sha((root/'outputs'/'BLIND'/f'{d}.json').read_bytes()) for d in verifies}
    if summary['result_sha256']!=digestmap:raise RuntimeError('blind outputs altered after run')
    return summary


def run_blind(root):
    import os
    if os.environ.get('SST_A065_ISOLATED_RUN') != '1':
        raise RuntimeError('Blind campaign cannot write into source tree; use run_all.cmd or run_all.sh')
    seals=verify_all(root)
    # This function MUST NOT open private_reveal/targets.json: verify_all checks its hash only.
    import shutil
    # Invalidate and remove stale reveal results before a fresh blind campaign.
    shutil.rmtree(root/'outputs'/'REVEALED',ignore_errors=True)
    results=[run_d01(root),run_d02(root),run_d03(root)]
    out=root/'outputs'/'BLIND';out.mkdir(parents=True,exist_ok=True)
    for r in results:writejson(out/f'{r["dataset_id"]}.json',r)
    hashes={r['dataset_id']:sha((out/f'{r["dataset_id"]}.json').read_bytes()) for r in results}
    gs=[g for r in results for g in r['gates']]
    summary={'campaign':'TRIADIC_CASIMIR_v0.3.2','status':'ANALYTIC_AND_FILAMENT_NUMERICS_QUALIFIED' if all(g['status']=='PASS' for g in gs) else 'SYNTHETIC_GATES_FAILED','science_status':'FILAMENT_ODE_SIMULATION_ONLY; PHYSICAL_EULER_AND_CASIMIR_UNVALIDATED','source_status':'SYNTHETIC_PLUS_ONE_SOURCED_KNOTPLOT_GEOMETRY_AND_RK4_SIMULATION','seals':seals,'provider_manifest_sha256':results[0]['second_provider_readiness'].get('manifest_sha256'),
             'result_sha256':hashes,'gates':gs,'framework':'frozen_v1.0.7 adapter supported; native qualification is separate; see FRAMEWORK_STATUS.json','quantum_zero_point_claim':'NONE'}
    writejson(out/'RUN_SUMMARY.json',summary)
    # Run audit; no private comparator data ever read in this step.
    verify_predictions_against_commit(root)
    return summary


def reveal(root):
    blind=verify_predictions_against_commit(root)
    targetfile=root/'private_reveal'/'targets.json'
    if not targetfile.is_file():raise RuntimeError('REVEAL_BLOCKED_NO_ESCROW: extract the separate private escrow archive first')
    commit=readjson(root/'seals'/'GLOBAL_COMMITMENT.json')
    if sha(targetfile.read_bytes())!=commit['private_target_sha256']:raise RuntimeError('REVEAL_BLOCKED_ESCROW_SHA256_MISMATCH')
    failed=[g['gate'] for g in blind.get('gates',[]) if g['status']!='PASS']
    if failed:raise RuntimeError('REVEAL_BLOCKED_FAILED_BLIND_GATES: '+', '.join(failed))
    raise RuntimeError('REVEAL_BLOCKED_UNRESOLVED_PHYSICAL_G3: physical Casimir discovery has not been demonstrated')
    targets=readjson(targetfile)
    d3=readjson(root/'outputs'/'BLIND'/'D03_TWO_SURFACE.json')
    comparisons=[]
    for x in d3['free_exponents_not_targets']:
        comparisons.append({'pair':x['pair'],'temperature':x['temperature'], 'toy_exponent':x['free_fitted_exponent'], 'ideal_scalar_highT_comparator_exponent':targets['reference_exponent_ideal_scalar_classical_T_gt_0'],'ideal_em_zeroT_comparator_exponent':targets['reference_exponent_ideal_em_T0'],'claim':'NUMERICAL_TOY_ONLY_NOT_PHYSICAL_MATCH'})
    result={'status':'REVEALED_REFERENCE_COMPARISON','external_measurements_included':False,'reference_coefficients':{'scalar_classical':targets['reference_ideal_scalar_classical_pressure_coefficient_zeta3_over_8pi'],'ideal_em_zeroT':targets['reference_ideal_em_T0_pressure_coefficient_pi_squared_over_240']},'comparison':comparisons,'blind_summary_sha256':sha((root/'outputs'/'BLIND'/'RUN_SUMMARY.json').read_bytes()),'target_commitment':sha((root/'private_reveal'/'targets.json').read_bytes()),'verdict':'ONLY_SYNTHETIC_CONTROL_QUALIFIED; NO_SST_FORCE_CLAIM'}
    out=root/'outputs'/'REVEALED';out.mkdir(parents=True,exist_ok=True)
    writejson(out/'COMPARISON.json',result)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['SELFTEST','VERIFY','BLIND','REVEAL','ALL','CERTIFY','INIT','PARITY','PROVIDER','DYNAMICS'])
    args=parser.parse_args()
    if args.mode=='PARITY':
        from runpy import run_path
        run_path(str(ROOT/'tools'/'backend_parity.py'),run_name='__main__')
        run_path(str(ROOT/'tools'/'filament_parity.py'),run_name='__main__');return
    if args.mode=='INIT':
        raise SystemExit('INIT_BLOCKED: v0.3.0 is preregistered; do not regenerate or reseal blind datasets in-place')
    if args.mode=='VERIFY':
        print(json.dumps(verify_all(ROOT),indent=2));return
    if args.mode=='PROVIDER':
        from .providers import check
        print(json.dumps(check(ROOT),indent=2));return
    if args.mode=='DYNAMICS':
        from .dynamics import run
        print(json.dumps(run(ROOT),indent=2));return
    if args.mode=='CERTIFY':
        print('CERTIFY BLOCKED: no second qualified PKLSA provider, Euler trajectories or calibrated wall coupling.',file=sys.stderr)
        raise SystemExit(2)
    if args.mode=='SELFTEST':
        import unittest
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():raise SystemExit(1)
        return
    if args.mode=='ALL':
        import unittest,shutil
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
        tested=unittest.TextTestRunner(verbosity=1).run(suite)
        if not tested.wasSuccessful():raise SystemExit(1)
        if shutil.which('g++'):
            from runpy import run_path
            run_path(str(ROOT/'tools'/'backend_parity.py'),run_name='__main__')
            run_path(str(ROOT/'tools'/'filament_parity.py'),run_name='__main__')
        else:print('OPTIONAL_CPP_PARITY_UNAVAILABLE (not PASS)')
    if args.mode in ('BLIND','ALL'):
        s=run_blind(ROOT)
        print(json.dumps({'status':s['status'],'gates':len(s['gates']),'pass':sum(x['status']=='PASS' for x in s['gates'])},indent=2))
    if args.mode in ('REVEAL','ALL'):
        r=reveal(ROOT);print(json.dumps({'status':r['status'],'verdict':r['verdict']},indent=2))

if __name__=='__main__':main()
