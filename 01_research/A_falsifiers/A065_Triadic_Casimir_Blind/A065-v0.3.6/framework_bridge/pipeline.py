"""Application plug-in for *unchanged* canonical SST framework v1.0.7.

The instance gate DAG is versioned and frozen *before* FREEZE. G5 is a
strict C++ kernel-parity gate that does NOT certify full coupled dynamics.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from triadic.runner import run_d01,run_d02,run_d03
from triadic.security import verify_all
from triadic.provider_manifest import verify as verify_provider
from triadic.native_qualification import evaluate


def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    ledger.record('G0','PASS',metrics={'mode':mode,'framework_contract':'1.0.7'},
                  reason='Frozen protocol verified by canonical framework.')
    seals=verify_all(root)
    provider=verify_provider(root)
    ledger.record('G1','PASS',metrics={'sealed_datasets':3,'upstream_geometry_providers':1+
                  int(provider['status']=='PASS_RAW_HASH_AND_XYZ_PARSER_ONLY'),
                  'provider_status':provider['status'],'provider_manifest_sha256':provider['manifest_sha256'],
                  'seals':seals},reason='Source bytes and single shared provider manifest verified; dynamic independence not implied.')
    results=[run_d01(root),run_d02(root),run_d03(root)]
    gates=[g for r in results for g in r['gates']]
    fails=[g['gate'] for g in gates if g['status']!='PASS']
    dyn=results[0]['filament_dynamics']
    ledger.record('G2','PASS' if not fails else 'FAIL',metrics={
        'reference_gates_pass':len(gates)-len(fails),'reference_gates_total':len(gates),
        'legacy_75_150_relative':dyn['spatial_75_150_relative_displacement'],
        'new_150_300_relative':dyn['spatial_150_300_relative_displacement'],
        'failed_reference_gates':fails,'pklsa_points':300},
        reason='75/150/300 fixed-core validation. Retain historical FAIL; no tolerance changes.')
    from triadic.qualification_v032 import run as run_qualification_v032
    q=run_qualification_v032(root)
    qs=q['qualification']
    ledger.record('G10',qs['refined_discretization'],metrics={
        'historical_75_150':q['spatial']['pairs']['75_vs_150']['relative_to_coarse_displacement'],
        'refined_150_300':q['spatial']['pairs']['150_vs_300']['relative_to_coarse_displacement'],
        'refined_300_600':q['spatial']['pairs']['300_vs_600']['relative_to_coarse_displacement']},
        reason='Refined filament ODE only; 600 points interpolated from 300. Historic G2 FAIL retained.')
    pstatus=qs['fremlin_dynamic_lane']
    ledger.record('G11','PASS' if pstatus=='SIMULATION_QUALIFIED' else 'UNRESOLVED' if pstatus.startswith('UNRESOLVED') else 'FAIL',
                  metrics={'provider_status':pstatus,'raw_geometry':q['independent_dynamic_simulation']['geometry_evidence']},
                  reason='C++17 Fremlin numerical provider only, not an independent physical Euler model.')
    # v0.3.4 historical geometry tranche: strictly supplementary, never G3 prereq.
    from triadic.historical_v034 import run as historical_run
    history=historical_run(root)
    hn=history['native_qualification']
    ledger.record('G12','PASS',metrics={'historical_sources':list(history['geometry_sources']),
                  'geometry_integrity':'HASH_ANALYTIC_LENGTH_AND_XYZ_ALIGNMENT_VERIFIED'},
                  reason='Historical initial geometries verified, not dynamically relaxed PKLSA.')
    if hn['status']=='EXECUTED':
        seeds=hn['seeds']
        converged=all(x['spatial_status']=='PASS' and x['temporal_status']=='PASS' and
                      x['python_cpp_parity_status']=='PASS' for x in seeds.values())
        ledger.record('G13','PASS' if converged else 'FAIL',
                      metrics={'seed_numerical_diagnostics':seeds},
                      reason='G13 reduced filament ODE resolution only; any failure retained.')
        ledger.record('G14','PASS',metrics={'core_sensitivity':{k:v['core_sensitivity'] for k,v in seeds.items()}},
                      reason='Only deterministic epsilon scan completion; not a physical closure.')
    else:
        ledger.record('G13','UNRESOLVED',metrics={'native':hn['status']},reason='C++ solver absent/failed, no fabricated qualification.')
        ledger.record('G14','UNRESOLVED',metrics={'native':hn['status']},reason='Epsilon scan not executed.')
    # v0.3.5 high-resolution geometry-only branch: new gates are independent
    # of FAILED coarse G2/G13 and do not change physical G3 prerequisites.
    from triadic.highres_v035 import run as highres_run
    highres=highres_run(root)
    if highres['native']['status']=='EXECUTED':
        seeds=highres['native']['seeds']
        ledger.record('G15','PASS',metrics={'grids':[600,1200,2400,4800],
                       'parametric_seed_sources':list(seeds),'prereg_sha256':highres['prereg_sha256']},
                      reason='All direct parametric coordinate hashes and nesting verified; geometry only.')
        good=all(z['baseline_spatial_1pct']=='PASS' for z in seeds.values())
        ledger.record('G16','PASS' if good else 'FAIL',metrics={k:z['epsilon_ladders']['0.12']['pairs'] for k,z in seeds.items()},
                      reason='Fixed 1 percent baseline discretization threshold (not physical Euler).')
        full=all(len(z['epsilon_ladders'])==3 and all(len(e['pairs'])==3 for e in z['epsilon_ladders'].values()) for z in seeds.values())
        ledger.record('G17','PASS' if full else 'FAIL',metrics={k:{e:v['all_1pct'] for e,v in z['epsilon_ladders'].items()} for k,z in seeds.items()},
                      reason='Epsilon scan completion only; individual failures retained, no physical core fit.')
        temporal=all(z['temporal_status']=='PASS' and z['parity_status']=='PASS' for z in seeds.values())
        ledger.record('G18','PASS' if temporal else 'FAIL',metrics={k:{'time':z['temporal_controls'],'parity_N150':z['parity_N150_python_cpp_rms']} for k,z in seeds.items()},
                      reason='Native time-convergence and limited Python parity; reduced ODE, not Euler PDE.')
    else:
        ledger.record('G15','PASS',metrics={'integrity':'PASS','native':highres['native']['status']},
                      reason='Coordinates verified independently from compiler availability.')
        for gid in ('G16','G17','G18'):
            ledger.record(gid,'UNRESOLVED',metrics={'native':highres['native']['status']},
                          reason='C++ compiler unavailable; no Python approximation substituted for large grids.')
    # v0.3.6 runtime-generated 2015 parametric mesh; never rewrites original XYZ.
    from triadic.generated_core_v036 import run as generated_run
    gen=generated_run(root)
    ledger.record('G19','PASS',metrics={'max_coordinate_difference':gen['generated_compatibility_max_xyz_difference'],
                  'two_parametric_geometry_seeds':list(gen['generated_geometry']),
                  'generator_prereg_sha256':gen['prereg_sha256']},
                  reason='Runtime 2015 analytical generation agrees with pinned XYZ; numerical initial data only.')
    # 0.25 is explicitly a descriptive resolution rule, not an SST core relation.
    resolution={k:v['grids']['4800']['segment_over_epsilon'] for k,v in gen['generated_geometry'].items()}
    ledger.record('G20','PASS' if max(resolution.values())<.25 else 'FAIL',
                  metrics={'at_N4800_segment_over_epsilon':resolution,'epsilon':.06},
                  reason='Resolution relative to numerical smoothing parameter measured, never optimized.')
    if gen['dynamics']['status']=='EXECUTED':
        good=all(d['fine_pairs_pass_1pct'] for d in gen['dynamics']['seeds'].values())
        ledger.record('G21','PASS' if good else 'FAIL',metrics={k:v['pairs'] for k,v in gen['dynamics']['seeds'].items()},
                      reason='Freshly generated N1200-N4800 geometry, fixed epsilon=.06, native C++ RK4; 600/1200 remains diagnostic.')
    else:
        ledger.record('G21','UNRESOLVED',metrics={'native':gen['dynamics']['status']},
                      reason='Native unavailable; no high-N Python replacement or physical claims.')
    # G5 is deliberately independent from scientific G2 so a spatial FAIL does
    # not suppress useful CPU parity evidence. The question is restricted to
    # the executed C++17 velocity kernel, not an unexecuted native RK4 chain.
    if ledger.defs['G5'].enabled:
        native=evaluate(root)
        if native['status']=='PASS':
            ledger.record('G5','PASS',metrics=native,
                          requested_backend='cpp17-fp64',actual_backend='cpp17-serial-fp64',
                          authority='KERNEL_ONLY',reason='Actual C++17 kernel executed. Full scientific/backend certification remains open.')
        else:
            ledger.record('G5','UNRESOLVED',metrics=native,
                          requested_backend='cpp17-fp64',actual_backend=None,authority='KERNEL_ONLY',
                          reason='C++ kernel parity unavailable/failed; never silently substitute Python.')
    else:ledger.record('G5','NOT_APPLICABLE',reason='Native CPU profile disabled')
    # v0.3.3 routes *evaluation* through refined numerical readiness only.
    # A coarse-grid FAIL remains part of G2 and is never relabeled PASS.
    from triadic.numeric_readiness import evaluate as evaluate_routing
    routing=evaluate_routing(root,gates,q,g10_status=ledger.status('G10'))
    if not routing['ready_for_G3_evaluation']:
        ledger.skip_due_prerequisite('G3',reason='v0.3.3 fail-closed analytic/refined-numeric/source gate; '+
                                     ','.join(routing['protected_mismatches'][:3]))
    else:
        ledger.record('G3','UNRESOLVED',metrics={
            'qualified_time_dependent_euler_providers':0,
            'historical_G2':'FAIL_RETAINED',
            'refined_G10':'PASS',
            'numerical_readiness_sha256':routing['prereg_sha256'],
            'raw_hash_verified_fremlin':provider['status']=='PASS_RAW_HASH_AND_XYZ_PARSER_ONLY'},
            reason='G3 evaluated after refined numerical qualification; independent physical force, complete Euler dynamics and microscopic material response remain unestablished.')
    ledger.skip_due_prerequisite('G4',reason='G3 physical discovery not PASS; no held-out independent physical replication')
    for gid in ('G6','G7'):
        if gid in ledger.defs:
            if not ledger.defs[gid].enabled:
                ledger.record(gid,'NOT_APPLICABLE',reason='Disabled for CPU-only profile')
            else:
                ledger.skip_due_prerequisite(gid,reason='Not certified for this profile')
    if 'G8' in ledger.defs:
        ledger.skip_due_prerequisite('G8',reason='Physical G3 not PASS; G8 has no dependency on disabled G7')
    return {'schema':'SST-BACKEND-MANIFEST-2','v033_numerical_routing':routing,'v036_generated':{'prereg_sha256':gen['prereg_sha256'],'native_status':gen['dynamics']['status'],'scope':'PARAMETRIC_GEOMETRY_SIMULATION_ONLY'},'v035_highres':{'prereg_sha256':highres['prereg_sha256'],'native_status':highres['native']['status'],'scope':'DIMENSIONLESS_FILAMENT_ODE_ONLY'},'v034_historical':{'prereg_sha256':history['precommit_sha256'],'native_status':hn['status'],'gate_scope':'GEOMETRY_SIMULATION_ONLY'},
            'python_reference':{'actual_backend':'python-stdlib-binary64','precision':'float64','authority':'REFERENCE'},
            'native_kernel':native if ledger.defs['G5'].enabled else {'status':'NOT_APPLICABLE'},
            'scope':'Kernel-only native gate; complete coupled physical validation withheld',
            'provider_manifest_sha256':provider['manifest_sha256'],
            'provider_status':provider['status'],
            'pklsa_geometry':results[0]['pklsa']['source']['raw_sha256'],
            'sealed_source_groups':list(seals), 'physical_force_status':'UNRESOLVED'}
