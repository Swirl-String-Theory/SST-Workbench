"""One authenticated trefoil, independent Euler probe, fail-closed science admission."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,subprocess,sys
import numpy as np
from sst_torsion import pipeline
from sst_torsion.run_contract import load_config,write_json,read_json,seal_run,package_run,sha256_file
from sst_torsion.ptsa_adapter import load_ptsa_archive
from sst_torsion.euler_producer import run_euler_smoke
from sst_torsion.observations import spectrum,branch_admission

ROOT=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser()
    p.add_argument('archive',type=Path)
    p.add_argument('--suite',default='authenticated-trefoil-euler-smoke')
    a=p.parse_args()
    population,provenance=load_ptsa_archive(a.archive)
    run=pipeline.prepare(ROOT,a.suite)
    config=load_config(run)
    audit=run/'AUDIT';audit.mkdir()
    def progress(message):
        with (audit/(run.name+'_heartbeat.log')).open('a',encoding='utf-8') as f:
            f.write(datetime.now(timezone.utc).isoformat()+' '+message+'\n')
        print(message,flush=True)
    print('RUN_DIR='+str(run),flush=True)
    progress('START tests and instrument qualification')
    result=subprocess.run([sys.executable,'-m','pytest','-q','tests'],cwd=ROOT,capture_output=True,text=True)
    write_json(run/'BLIND'/'test_execution.json',{'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    if result.returncode:
        raise RuntimeError('tests failed; unsealed partial run retained')
    pipeline.record_environment(run);pipeline.record_native(run)
    pipeline.analyze(run,'python');pipeline.analyze(run,'native');pipeline.parity(run)
    import a048_seed_native
    write_json(run/'BLIND'/'runtime_euler_seed_native.json',{'module':Path(a048_seed_native.__file__).name,'sha256':sha256_file(a048_seed_native.__file__)})
    write_json(run/'BLIND'/'authenticated_geometry.json',provenance)
    np.savez_compressed(run/'BLIND'/'authenticated_population.npz',centerlines=population)
    selected=population[0]
    outputs={};reports={}
    cfg=config['euler_probe']
    for label,factor in [('baseline_dt',1),('half_dt',2),('quarter_dt',4)]:
        probe=dict(cfg,dt=cfg['dt']/factor,steps=cfg['steps']*factor)
        progress('START '+label)
        arrays,report=run_euler_smoke(selected,probe)
        outputs[label]=arrays;reports[label]=report
        np.savez_compressed(run/'BLIND'/f'{run.name}_{label}_fields.npz',**arrays)
        write_json(run/'BLIND'/f'{run.name}_{label}_report.json',report)
        progress('DONE '+label)
    # Only time-integration convergence at fixed grid/initial state is assessed here.
    # Spatial, core-radius and remesh branches cannot be qualified on this unresolved core.
    ref=outputs['quarter_dt']['perturbed_velocity_hat_final']
    norm=max(float(np.linalg.norm(ref)),1e-30)
    e1=float(np.linalg.norm(outputs['baseline_dt']['perturbed_velocity_hat_final']-outputs['half_dt']['perturbed_velocity_hat_final'])/norm)
    e2=float(np.linalg.norm(outputs['half_dt']['perturbed_velocity_hat_final']-ref)/norm)
    time_pass=e2<1e-7 and (e2<e1 or e2<1e-12)
    temporal={'status':'PASS' if time_pass else 'FAIL','scope':'fixed_grid_short_window_integrator_only',
              'coarse_medium_relative_difference':e1,'medium_fine_relative_difference':e2,
              'fixed_end_time':cfg['dt']*cfg['steps'],'physical_branch_convergence':'INDETERMINATE'}
    base=reports['baseline_dt']
    spectral=spectrum(outputs['quarter_dt']['time'],outputs['quarter_dt']['delta_velocity_rms'])
    write_json(run/'BLIND'/'velocity_response_spectrum.json',spectral)
    qualification={'independent_core_state':'PASS',
        'temporal_convergence':'INDETERMINATE',
        'core_resolution':base['gates']['localized_core_chart']['status'],
        'material_observable':'NOT-IMPLEMENTED','centerline_observable':'NOT-IMPLEMENTED'}
    admission=branch_admission({'evidence_kind':'INDEPENDENT_DYNAMICS',
        'candidate_equation_drives_data':False,'qualification':qualification})
    dynamic={'run_id':run.name,'selected_candidate_id':provenance['candidate_ids'][0],
        'geometry_population_ingested':48,'geometries_evolved':1,'perturbations':['baseline','transverse'],
        'material_phase_run_executed':False,'producer_report':base,'temporal_integrator_check':temporal,
        'branch_admission':admission,'physics_status':'INDETERMINATE_UNQUALIFIED_CORE_AND_MISSING_MATERIAL_OBSERVABLE',
        'stop_reason':'No qualified localized core chart or independently perturbed material-phase observation. Increasing campaign size cannot repair these missing prerequisites.',
        'next_step':'Qualify an embedded resolved finite-core seed, then define objective active core perturbation plus material-phase extraction and conventional core-mode null.'}
    write_json(run/'BLIND'/'euler_probe_summary.json',dynamic)
    progress('SEAL complete BLIND inventory before reveal')
    seal_run(run)
    report=pipeline.reveal(run)
    # reveal already writes the full gate matrix including the producer summary.
    progress('DONE qualified instrument; physical branch remains INDETERMINATE')
    archives=package_run(run)
    print(json.dumps({'run_id':run.name,'archives':archives,'physics_status':dynamic['physics_status'],
        'core_screen':base['gates']['localized_core_chart'],'temporal_check':temporal,
        'energy_drift':base['gates']['energy_drift'],'divergence':base['gates']['incompressibility'],
        'native_seed_parity':base['initializer_native_parity']},indent=2))


if __name__=='__main__':
    main()
