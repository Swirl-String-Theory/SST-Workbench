"""v0.2.0 CLI: independent Euler build / analysis / tests / manifest verification."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from .spectral import SpectralEuler3D,init_knotted_tube,evolve
from a064.flow import SnapshotFlow,file_hash
from a064.analysis import run as analyze

ROOT=Path(__file__).resolve().parents[1]
KNOTS=('3_1','5_2','6_1')
CLASS='geometry_initialized_periodic_3d_euler_model'

def _paths(knot):
    src=ROOT/'data'/'PKLSA_RAW_NATIVE_UNQUALIFIED'/f'knot_{knot.replace("_",".")}.txt'
    out=ROOT/'data'/'EVOLVED_NPZ'/f'PKLSA_{knot}_periodic_EULER_MODEL.npz'
    return src,out

def build_one(knot,n=24,duration=.36,frames=13,core=.58,force=False):
    src,out=_paths(knot)
    out.parent.mkdir(exist_ok=True,parents=True)
    cfg={'n':n,'duration':duration,'frames':frames,'core':core}
    meta_path=out.with_suffix('.source.json')
    if out.exists() and meta_path.exists() and not force:
        meta=json.loads(meta_path.read_text())
        if meta.get('input_geometry_sha256')!=file_hash(src) or meta.get('npz_sha256')!=file_hash(out):
            raise RuntimeError('Existing source or NPZ was altered. Use --force for explicit rebuild.')
        if meta['parameters']!=cfg:raise RuntimeError('Existing NPZ parameter mismatch. Use --force.')
        return {'knot':knot,'status':'VERIFIED_EXISTING','file':str(out),'diagnostics':meta['euler_diagnostics']}
    model=SpectralEuler3D(n)
    u,conditioning=init_knotted_tube(model,np.loadtxt(src),core=core)
    t,v,diag=evolve(model,u,duration=duration,frame_count=frames)
    axes=(np.arange(n)-n//2)*model.dx
    # SI numbers are only bookkeeping in an explicitly arbitrary 1m/1s unit mapping.
    np.savez_compressed(out,x=axes,y=axes,z=axes,t=t,v=v,
        source_type=np.array(CLASS),time_model=np.array('pseudospectral_Euler_RK4_2over3_dealiased'),
        coordinate_calibration=np.array('ARBITRARY_REFERENCE_1M_1S_NOT_SST_CALIBRATION'))
    md={'schema':'A064-v0.2.0-euler-snapshot-v1','source_type':CLASS,
        'input_geometry':src.name,'input_geometry_sha256':file_hash(src),
        'npz_sha256':file_hash(out),'parameters':cfg,'conditioning':conditioning,
        'euler_diagnostics':diag,'time_model':'3D_Euler_RK4_rotational_form_2over3_dealiased',
        'evidence_tier':'NUMERICAL_SIMULATION_ONLY',
        'geometry_provider':'RAW_NATIVE_UNQUALIFIED_not_E011_PROVIDER_ANCHOR',
        'is_numerically_evolved':True,'is_independent_measurement':False,
        'is_dynamics_ready':False,'periodic_cube':True,
        'units':{'x':'arbitrary computational length with L0=1m numeric convention',
                 't':'arbitrary computational time with T0=1s numeric convention',
                 'v':'arbitrary U0=1m/s numeric convention'},
        'warning':'Periodic cubic Euler idealization; not free-space PKLSA dynamics, physical calibration, or true separatrix evidence.'}
    meta_path.write_text(json.dumps(md,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf8')
    return {'knot':knot,'status':'BUILT','file':str(out),'diagnostics':diag}

def validate(knot,n=24,duration=.36,frames=13,core=.58):
    src,out=_paths(knot); meta_path=out.with_suffix('.source.json')
    if not out.is_file() or not meta_path.is_file():raise FileNotFoundError('Missing source NPZ. Run EULER_BUILD.')
    md=json.loads(meta_path.read_text())
    if md['input_geometry_sha256']!=file_hash(src) or md['npz_sha256']!=file_hash(out):
        raise ValueError('SHA-256 provenance mismatch')
    if md['parameters']!={'n':n,'duration':duration,'frames':frames,'core':core}:
        raise ValueError('NPZ build parameters differ from request')
    z=np.load(out,allow_pickle=False)
    if z['v'].shape!=(frames,n,n,n,3) or str(z['source_type'])!=CLASS or not np.max(np.abs(z['v'][0]-z['v'][-1]))>1e-9:
        raise ValueError('Evolved NPZ malformed or frozen')
    if md['euler_diagnostics']['max_divergence']>1e-9:raise ValueError('Euler incompressibility gate failed')
    return md

def run(knot,out_dir,n=24,duration=.36,frames=13,core=.58,force=False,build=True):
    if build:build_one(knot,n,duration,frames,core,force)
    md=validate(knot,n,duration,frames,core)
    _,file=_paths(knot)
    flow=SnapshotFlow(file)
    if flow.evidence_class!=CLASS:raise ValueError('wrong simulation source type')
    res=analyze(flow,flow.axes,float(flow.times[0]),float(flow.times[-1]),
        out_dir/f'pklsa_{knot}_euler','EULER_SIMULATION_MODEL',md,skip_stagnation=True)
    dst=out_dir/f'pklsa_{knot}_euler'/'EULER_SOURCE_AUDIT.json'
    diag=md['euler_diagnostics']; q={
        'model':CLASS,'euler_integrator':'SPECTRAL_RK4_PROJECTION','source_sha256':md['npz_sha256'],
        'real_evolution_detected':True,'time_snapshots':frames,
        'incompressibility_pass':diag['max_divergence']<1e-9,
        'energy_drift_screen_pass':diag['max_energy_rel_drift']<.02,
        'helicity_drift_screen_pass':diag['max_helicity_rel_drift']<.05,
        'cfl_screen_pass':diag['max_cfl']<=.1600001,
        'temporal_euler_model_gate':'NUMERICAL_EULER_MODEL_CONDITIONAL',
        'spatial_convergence_gate':'UNRESOLVED_NOT_TESTED',
        'temporal_convergence_gate':'UNRESOLVED_NOT_TESTED',
        'invariant_manifold_gate':'UNRESOLVED_NOT_TESTED',
        'material_transport_assessment':res['dynamical_feature_status'],
        'scientific_separatrix_gate':'UNRESOLVED',
        'diagnostics':diag}
    dst.write_text(json.dumps(q,indent=2,allow_nan=False)+'\n')
    return {'knot':knot,'euler':q,'analysis':res}

def summarize(results,root):
    result={
      'project':'A064','version':'0.2.0','status':'MODEL_SIMULATION_NOT_V1_0_7_CERTIFIED',
      'n_cases':len(results),'regime':'periodic_incompressible_3D_Euler',
      'scientific_gate':'UNRESOLVED','separatrix_manifold_gate':'UNRESOLVED',
      'tests':[{'knot':r['knot'],'max_energy_rel_drift':r['euler']['diagnostics']['max_energy_rel_drift'],
      'max_helicity_rel_drift':r['euler']['diagnostics']['max_helicity_rel_drift'],
      'max_divergence':r['euler']['diagnostics']['max_divergence'],
      'candidate_detected':r['analysis']['candidate_detected'],
      'dynamical_feature_status':r['analysis']['dynamical_feature_status'],
      'transport':r['analysis']['transport'],
      'scientific_gate':r['analysis']['overall_scientific_gate']} for r in results]
    }
    root.mkdir(parents=True,exist_ok=True)
    (root/'RUN_SUMMARY.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description='A064 v0.2.0 periodic 3D Euler expansion')
    p.add_argument('mode',choices=('EULER_BUILD','EULER_RUN','EULER_TEST','EULER_VALIDATE'))
    p.add_argument('--knot',choices=('all',*KNOTS),default='all')
    p.add_argument('--grid',type=int,default=24)
    p.add_argument('--duration',type=float,default=.36)
    p.add_argument('--frames',type=int,default=13)
    p.add_argument('--core',type=float,default=.58)
    p.add_argument('--force',action='store_true')
    p.add_argument('--output',type=Path,default=ROOT/'A064-v0.2.0-outputs')
    args=p.parse_args(argv)
    if args.mode=='EULER_TEST':
        import pytest
        return pytest.main([str(ROOT/'tests'),str(ROOT/'tests_v2'),'-q'])
    knots=KNOTS if args.knot=='all' else (args.knot,)
    rows=[]
    for knot in knots:
        if args.mode=='EULER_BUILD':rows.append(build_one(knot,args.grid,args.duration,args.frames,args.core,args.force))
        elif args.mode=='EULER_VALIDATE':rows.append({'knot':knot,'metadata':validate(knot,args.grid,args.duration,args.frames,args.core)})
        else:rows.append(run(knot,args.output,args.grid,args.duration,args.frames,args.core,args.force))
    if args.mode=='EULER_RUN':summarize(rows,args.output)
    for row in rows:
        if args.mode=='EULER_RUN':
            print(f"[{row['knot']}] status={row['analysis']['dynamical_feature_status']}, "
                  f"candidate={row['analysis']['candidate_detected']}, "
                  f"energy_drift={row['euler']['diagnostics']['max_energy_rel_drift']:.3g}, "
                  f"manifold={row['euler']['invariant_manifold_gate']}")
        else:print(json.dumps(row,sort_keys=True)[:1200])
    return 0
if __name__=='__main__':sys.exit(main())
