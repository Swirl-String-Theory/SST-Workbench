"""Build A064 velocity snapshots from bundled raw knot centerlines.

NO dynamics are inferred: every output is a stationary regularized-Biot-Savart
model, and repeating frames never constitutes an Euler-time integration.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from .flow import FilamentFlow, file_hash

ALLOWED=('3_1','5_2','6_1')
EVIDENCE='geometry_derived_regularized_biot_savart_simulation'

def preset_paths(root,knot='all'):
    names=ALLOWED if knot=='all' else (knot,)
    return [(name,Path(root)/'data'/'MODEL_NPZ'/f'PKLSA_{name}_stationary_BS_DEMO.npz') for name in names]

def validate_existing(path,xyz,params):
    sidecar=path.with_suffix('.source.json')
    if not path.exists() or not sidecar.exists(): return False
    try:
        md=json.loads(sidecar.read_text(encoding='utf-8'))
        if md.get('source_type')!=EVIDENCE or md.get('npz_sha256')!=file_hash(path): return False
        if md.get('source_xyz_sha256')!=file_hash(xyz): return False
        if any(md.get(k)!=v for k,v in params.items()):return False
        with np.load(path,allow_pickle=False) as z:
            for k in ('x','y','z','t','v','source_type'): assert k in z
            assert str(z['source_type'])==EVIDENCE
            assert z['v'].shape==(params['time_frames'],params['grid'],params['grid'],params['grid'],3)
        return True
    except (OSError,ValueError,KeyError,AssertionError,TypeError):return False

def build_one(xyz,path,scale,core,gamma,grid,duration,nt,calibration,force=False):
    xyz=Path(xyz);path=Path(path)
    if grid<21 or nt<2 or duration<=0:raise ValueError('require grid>=21, time-frames>=2, duration-s>0')
    if not np.isfinite([scale,core,gamma,duration]).all() or scale<=0 or core<=0 or gamma==0:
        raise ValueError('invalid scale/core/circulation/duration')
    params=dict(scale_m_per_unit=float(scale),core_m=float(core),gamma_m2_s=float(gamma),
                grid=int(grid),duration_s=float(duration),time_frames=int(nt),calibration=calibration)
    path.parent.mkdir(parents=True,exist_ok=True)
    if not force and validate_existing(path,xyz,params):
        return {'file':str(path),'status':'VERIFIED_EXISTING','sha256':file_hash(path), 'evidence_class':EVIDENCE}
    p=np.loadtxt(xyz,dtype=np.float64)
    if p.ndim!=2 or p.shape[1]!=3 or len(p)<16 or not np.isfinite(p).all():
        raise ValueError('source has no finite 3D centerline')
    p*=scale
    model=FilamentFlow(p,core_m=core,gamma_m2_s=gamma)
    pad=max(3.5*core,.15*float(np.ptp(p,axis=0).max()))
    axes=tuple(np.linspace(float(p[:,k].min()-pad),float(p[:,k].max()+pad),grid,dtype=np.float64) for k in range(3))
    velocity=model.frame(axes,0.)
    if not np.isfinite(velocity).all():raise ValueError('nonfinite velocity reconstruction')
    times=np.linspace(0.,duration,nt,dtype=np.float64)
    v=np.repeat(velocity[np.newaxis,...],nt,axis=0)
    # Round-trip reproducible inference given source, grid, unit assumptions and implementation.
    tmp=path.with_name(path.stem+'.partial.npz')
    np.savez_compressed(tmp,x=axes[0],y=axes[1],z=axes[2],t=times,v=v,
                        source_type=np.array(EVIDENCE),time_model=np.array('frozen_velocity_not_Euler_evolution'))
    tmp.replace(path)
    md={'schema':'A064_snapshot_v1','source_type':EVIDENCE,'time_model':'frozen_velocity_not_Euler_evolution',
        'source_xyz':xyz.name,'source_xyz_sha256':file_hash(xyz),'npz_sha256':file_hash(path),
        'units':{'x':'m','y':'m','z':'m','t':'s','v':'m/s'},'is_physical_euler_evolution':False,
        'scientific_status':'MODEL_ONLY_UNRESOLVED','builder':'A064-v0.1.1 regularized midpoint segment Biot-Savart',
        **params}
    path.with_suffix('.source.json').write_text(json.dumps(md,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return {'file':str(path),'status':'BUILT','sha256':md['npz_sha256'],
            'evidence_class':EVIDENCE,'shape':list(v.shape)}

def build_all(root,args):
    root=Path(root)
    if args.source is not None:
        if not args.source.is_file():raise ValueError('custom --source must exist')
        if args.output_npz is None:raise ValueError('custom --source requires --output-npz')
        selection=[('CUSTOM',Path(args.output_npz),Path(args.source))]
    else:
        selection=[(name,path,root/'data'/'PKLSA_RAW_NATIVE_UNQUALIFIED'/f'knot_{name.replace("_",".")}.txt')
                   for name,path in preset_paths(root,args.knot)]
        if args.output_npz is not None:
            if len(selection)!=1:raise ValueError('--output-npz requires --knot 3_1, 5_2 or 6_1')
            name,_,xyz=selection[0];selection=[(name,Path(args.output_npz),xyz)]
    supplied=[args.scale_m_per_unit,args.core_m,args.gamma_m2_s]
    if any(x is not None for x in supplied) and not all(x is not None for x in supplied):
        raise ValueError('for a calibrated build provide ALL --scale-m-per-unit, --core-m and --gamma-m2-s')
    if all(x is not None for x in supplied):
        scale,core,gamma=supplied
        calibration='EXPLICIT_USER_SUPPLIED_NOT_INDEPENDENTLY_VALIDATED'
    else:
        scale,core,gamma=1.,.8,10.
        calibration='ARBITRARY_DEMO_COORDINATE_UNIT_AS_1_METER_NOT_PHYSICAL_SST'
    return [build_one(xyz,path,scale,core,gamma,args.grid,args.duration_s,args.time_frames,calibration,args.force)
            for name,path,xyz in selection]
