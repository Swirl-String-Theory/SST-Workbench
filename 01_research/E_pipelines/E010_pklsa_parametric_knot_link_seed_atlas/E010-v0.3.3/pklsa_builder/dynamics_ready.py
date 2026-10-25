"""E010 v0.3.2 finite-core filament dynamics qualification (additive).

This module extends the EXISTING pklsa_builder; it imports the established
Gilbert/XYZ/VECT loaders. It does not rewrite E010 or E011 identity data.

Model: desingularized, free-space, polygon midpoint Biot-Savart vortex filament;
NOT a 3-D incompressible Euler solver, GP solver or SST clock model.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import zipfile
import numpy as np

MODEL_ID = 'BS_FILAMENT_MIDPOINT_ROSENHEAD_V1'
SCHEMA = 'E010-PKLSA-DYNAMICS-READY-1'
E011_SCHEMA = 'E011-STATIC-SEED-CONTRACT-1'
REQUIRED_CAPS = ('curvature_rms_ready', 'reach_ready')

class AdmissionError(RuntimeError):
    pass

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1<<20), b''): h.update(block)
    return h.hexdigest()

def canonical_json_file(path:Path, value:dict)->None:
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f: json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')

class E011SeedContract:
    """Read E011's unmodified output as a strict dependency, ZIP or directory."""
    def __init__(self, path, expected_sha256=None):
        self.path=Path(path)
        if not self.path.exists():raise AdmissionError(f'E011 output not found: {self.path}')
        self.parent_zip_sha256=sha256_file(self.path) if self.path.is_file() else None
        if expected_sha256:
            if self.parent_zip_sha256 is None: raise AdmissionError('PINNED E011 hash requires a ZIP, not an unverified directory')
            if self.parent_zip_sha256!=expected_sha256: raise AdmissionError('E011 archive SHA256 mismatch')
        if self.path.is_file():
            self.z=zipfile.ZipFile(self.path)
            self.root=next((x.split('/')[0]+'/' for x in self.z.namelist() if x.endswith('/SEED_CONTRACT_SCHEMA.json')),None)
            if self.root is None: raise AdmissionError('E011 SEED_CONTRACT_SCHEMA.json missing')
        else:
            self.z=None
            self.root=self.path
        schema=self.read('SEED_CONTRACT_SCHEMA.json')
        if schema.get('schema')!=E011_SCHEMA or schema.get('atlas_version')!='0.3.0':
            raise AdmissionError('Unsupported E011 source contract/version')
        if schema.get('dynamics_ready') is not False:raise AdmissionError('E011 STATIC_READY dynamics flag unexpectedly changed')
        self.schema=schema

    def read(self,rel):
        if self.z:
            name=self.root+rel
            try:b=self.z.read(name)
            except KeyError:raise AdmissionError(f'E011 missing {rel}')
            return json.loads(b)
        f=self.root/rel
        if not f.is_file():raise AdmissionError(f'E011 missing {rel}')
        return json.loads(f.read_text(encoding='utf-8'))

    def anchors(self,topology):
        if self.z:
            rows=(self.z.read(self.root+'STATIC_READY_PROVIDER_ANCHORS.jsonl')).decode('utf-8').splitlines()
        else:
            rows=(self.root/'STATIC_READY_PROVIDER_ANCHORS.jsonl').read_text(encoding='utf-8').splitlines()
        out=[]
        for line in rows:
            if not line.strip():continue
            a=json.loads(line)
            if a.get('topology_id')==topology:out.append(a)
        return out

    def select(self,topology,provider):
        anchors=[r for r in self.anchors(topology) if r.get('provider_group')==provider]
        if len(anchors)!=1:raise AdmissionError(f'expected exactly one E011 provider anchor for {topology}/{provider}; got {len(anchors)}')
        s=anchors[0]
        if not s.get('static_ready') or s.get('seed_role')!='PRIMARY_REFERENCE':raise AdmissionError('E011 seed is not an admitted primary STATIC_READY source')
        if s.get('evidence_class')!='UPSTREAM_INDEPENDENT':raise AdmissionError('source is derived/control/mirror, not an independent upstream seed')
        if not s.get('static_seed_id') or not s.get('carrier_id'):raise AdmissionError('E011 identity missing')
        for gate in ('G1_isotopy_safe_sampling','G2_writhe_quadratic_convergence','G3_signed_frenet_chirality_completeness'):
            if s.get('literature_gate_status',{}).get(gate)!='PASS':raise AdmissionError(f'E010 source literature gate {gate} not PASS')
        if s.get('literature_gate_status',{}).get('B1_ideal_trefoil_ropelength')=='FAIL':
            # Upstream documented unresolved estimator bias, never rewrite/ignore.
            pass
        for key in REQUIRED_CAPS:
            if not s.get('capabilities',{}).get(key,False):raise AdmissionError(f'required static capability {key} unavailable')
        return s


def source_path(seed,workbench,override=None):
    """Map canonical E011 Windows source into local Workbench; no arbitrary path scan."""
    wb=Path(workbench).resolve()
    loc=seed.get('source_locator',{})
    if override:
        p=Path(override).resolve()
    else:
        original=loc.get('source_path','')
        pw=PureWindowsPath(original)
        parts=list(pw.parts)
        try:i=next(i for i,x in enumerate(parts) if x.lower()=='sst-workbench')
        except StopIteration:raise AdmissionError('Cannot map canonical E011 path to Workbench; provide explicit --source-override')
        relative=parts[i+1:]
        if not relative or relative[0].lower()!='03_data':raise AdmissionError('Non-canonical source path outside 03_data')
        p=wb.joinpath(*relative).resolve()
        if not p.is_relative_to(wb):raise AdmissionError('Resolved source escapes Workbench root')
    if not p.is_file():raise AdmissionError(f'Original source bytes unavailable: {p}')
    expected=loc.get('raw_sha256')
    if not isinstance(expected,str) or len(expected)!=64:raise AdmissionError('E011 raw_sha256 is missing/invalid')
    observed=sha256_file(p)
    if observed != expected:raise AdmissionError(f'Source hash mismatch: expected {expected}, got {observed}')
    return p,observed


def native_geometry(seed,workbench,override=None,n_original=1024):
    """Delegates native parsing to v0.3.1 pklsa_builder, preserving conventions."""
    from pklsa_builder.gilbert import find_gilbert_record,sample_gilbert_components
    from pklsa_builder.io_geometry import load_geometry
    from pklsa_builder.geometry import clean_closed,normalize
    p,h=source_path(seed,workbench,override)
    loc=seed['source_locator'];rep=loc.get('representation')
    if rep=='gilbert_ab_record':
        rec=find_gilbert_record(p,seed['topology_id'])
        if rec.get('attrs',{}).get('Id')!=loc.get('reference_id'):
            raise AdmissionError('Gilbert record id differs from the E011 source locator')
        pts=sample_gilbert_components(rec,n=n_original)
    elif rep in {'xyz','vect','fremlin_fseries','fseries'}:
        pts=load_geometry(p,representation=rep,fseries_n=n_original)
    else:raise AdmissionError(f'Unknown/unadmitted representation {rep}')
    if len(pts)!=1:raise AdmissionError('v0.3.2 pilot only supports one closed filament (not links)')
    original=clean_closed(pts[0])
    if len(original)<8:raise AdmissionError('too few geometry points')
    length=float(np.linalg.norm(np.roll(original,-1,axis=0)-original,axis=1).sum())
    if not (np.isfinite(length) and length>0):raise AdmissionError('invalid length')
    return normalize(original,target_length=1.0), {'path':str(p),'raw_sha256':h,
           'reference_id':loc.get('reference_id'),'representation':rep,
           'original_length':length,'normalized_length':1.0,
           'geometry_source':'pklsa_builder.gilbert/io_geometry/geometry',
           'upstream_B1_status':seed.get('literature_gate_status',{}).get('B1_ideal_trefoil_ropelength','NOT_APPLICABLE')}


def arclength_n(points,n):
    from pklsa_builder.geometry import arclength_linear
    return arclength_linear(points,n)

def bs_velocity(points,core,gamma=1.0,block=128):
    """Midpoint Rosenhead desingularization of the free-space filament integral.

    v(X_i) = Gamma/(4 pi) sum_j Delta X_j cross (X_i - M_j)
             / (|X_i - M_j|^2 + a^2)^(3/2).
    Self and adjacent interactions included with finite core. No LIA correction.
    """
    x=np.asarray(points,dtype=np.float64);n=len(x)
    if x.shape!=(n,3) or n<8 or not np.isfinite(x).all():raise ValueError('bad points')
    if not(np.isfinite(core) and core>0 and np.isfinite(gamma) and gamma!=0):raise ValueError('bad core or circulation')
    dx=np.roll(x,-1,axis=0)-x
    mid=x+dx/2
    out=np.zeros_like(x)
    for i0 in range(0,n,block):
        r=x[i0:i0+block,None,:]-mid[None,:,:]
        r2=np.einsum('ijk,ijk->ij',r,r)+core**2
        out[i0:i0+block]=np.sum(np.cross(dx[None,:,:],r,axis=-1)/(r2[:,:,None]**1.5),axis=1)
    return out*(gamma/(4*math.pi))

def bs_energy_proxy(points,core,gamma=1.0,block=128):
    """Static regularized current-current double integral (diagnostic only)."""
    x=np.asarray(points,np.float64);dr=np.roll(x,-1,axis=0)-x;mid=x+0.5*dr
    sumv=0.0
    for i0 in range(0,len(x),block):
        d=mid[i0:i0+block,None,:]-mid[None,:,:]
        r=np.sqrt(np.einsum('ijk,ijk->ij',d,d)+core**2)
        sumv+=float(np.sum((dr[i0:i0+block]@dr.T)/r))
    return sumv*(gamma**2/(8*math.pi))

def rk4(x,dt,core,gamma=1.0):
    f=lambda y:bs_velocity(y,core,gamma)
    k1=f(x);k2=f(x+0.5*dt*k1);k3=f(x+0.5*dt*k2);k4=f(x+dt*k3)
    return x+dt*(k1+2*k2+2*k3+k4)/6

def evolve(x,tfinal,steps,core,gamma=1.0,diagnostics=False):
    if not (steps>=1 and tfinal>0):raise ValueError('positive final T and steps needed')
    y=np.array(x,dtype=np.float64,copy=True);dt=tfinal/steps
    for _ in range(int(steps)):
        y=rk4(y,dt,core,gamma)
        if not np.isfinite(y).all():raise FloatingPointError('nonfinite evolved filament')
    return y

def poly_length(p):return float(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).sum())

def nonlocal_midpoint_gap(points,exclusion_fraction=0.06,block=128):
    """Coarse nonlocal midpoint clearance *proxy*, not certified 3-D reach."""
    x=np.asarray(points);n=len(x);mid=0.5*(x+np.roll(x,-1,axis=0));idx=np.arange(n);dmin=np.inf
    exclude=max(2,math.ceil(n*exclusion_fraction))
    for i0 in range(0,n,block):
        r=mid[i0:i0+block,None,:]-mid[None,:,:]
        d2=np.einsum('ijk,ijk->ij',r,r)
        di=np.abs(idx[i0:i0+block,None]-idx[None,:]);di=np.minimum(di,n-di)
        d2[di<=exclude]=np.inf
        dmin=min(dmin,float(d2.min()))
    return float(math.sqrt(dmin))

def rel_l2(x,y):
    return float(np.linalg.norm((np.asarray(x)-np.asarray(y)).ravel())/max(np.linalg.norm(np.asarray(y).ravel()),1e-15))

def pre_registered_policy():
    return {'model':MODEL_ID,'normalized_length':1.0,'gamma':1.0,'core_radius':0.017,
            't_final':0.004,'steps':8,'fine_n':256,'coarse_n':128,
            'min_core_cells_fine':4.0,'spatial_velocity_rel_l2_max':0.05,
            'temporal_rel_l2_max':0.002,'energy_proxy_relative_drift_max':0.03,
            'min_clearance_over_2core':1.1, 'max_length_relative_drift':0.03,
            'require_cpu_fp64':True,'require_independent_provider_for_cross_provider_claim':True,
            'qualifies_only':'free-space regularized BS filament numerical dynamics (short horizon)'}

def qualify(points, *, core=0.017, tfinal=0.004, steps=8, fine_n=256, gamma=1.0,
            thresholds=None, full=True):
    """Independent temporal/spatial refinement, no replacement with extrapolated PASS."""
    policy=pre_registered_policy();limits={k:policy[k] for k in ('min_core_cells_fine','spatial_velocity_rel_l2_max','temporal_rel_l2_max','energy_proxy_relative_drift_max','min_clearance_over_2core','max_length_relative_drift')}
    if thresholds:limits.update(thresholds)
    if fine_n%2 or fine_n<32 or steps%2 or steps<4:raise ValueError('fine_n even >=32 and steps even >=4')
    p_f=arclength_n(points,fine_n);p_c=arclength_n(points,fine_n//2)
    initial_len=poly_length(p_f)
    gap0=nonlocal_midpoint_gap(p_f)
    v_f=bs_velocity(p_f,core,gamma);v_c=bs_velocity(p_c,core,gamma)
    v_ref=v_f[::2];spatial=rel_l2(v_c,v_ref)
    # Independent temporal series on identical fine grid (steps, 2*steps, 4*steps)
    co=evolve(p_f,tfinal,steps,core,gamma)
    mi=evolve(p_f,tfinal,2*steps,core,gamma)
    fi=evolve(p_f,tfinal,4*steps,core,gamma)
    temporal=rel_l2(mi,fi)
    delta_co=rel_l2(co,mi)
    order=math.log(max(delta_co,1e-20)/max(temporal,1e-20),2)
    h0=bs_energy_proxy(p_f,core,gamma);hf=bs_energy_proxy(fi,core,gamma)
    edrift=abs(hf-h0)/max(abs(h0),1e-15)
    len_drift=abs(poly_length(fi)-initial_len)/initial_len
    gapf=nonlocal_midpoint_gap(fi)
    core_cells=core/(initial_len/fine_n)
    checks={
     'core_resolution':core_cells>=limits['min_core_cells_fine'],
     'spatial_velocity_convergence':spatial<=limits['spatial_velocity_rel_l2_max'],
     'temporal_RK4_convergence':temporal<=limits['temporal_rel_l2_max'] and 2.8<=order<=5.2,
     'energy_proxy_diagnostic':edrift<=limits['energy_proxy_relative_drift_max'],
     'filament_length_diagnostic':len_drift<=limits['max_length_relative_drift'],
     'nonlocal_clearance_proxy':min(gap0,gapf)>=2*core*limits['min_clearance_over_2core'],
    }
    # Strict status threshold; when short horizon or substandard grid used, cannot promote.
    registered=(full and fine_n>=policy['fine_n'] and tfinal>=policy['t_final']
                and steps>=policy['steps'] and abs(core-policy['core_radius'])<=1e-15
                and gamma==policy['gamma'])
    ready=registered and all(checks.values())
    return {'schema':SCHEMA,'model':MODEL_ID,'status':'DYNAMICS_READY' if ready else 'DYNAMICS_NOT_READY',
            'scientific_authority':'NUMERICAL_FILAMENT_ONLY' if ready else 'DIAGNOSTIC_ONLY',
            'registered_full_protocol':bool(registered),'checks':checks,'limits':limits,
            'metrics':{'fine_n':fine_n,'coarse_n':fine_n//2,'core_radius':core,'core_cells_fine':core_cells,
                 't_final':tfinal,'steps':steps,'gamma':gamma,'spatial_velocity_rel_l2':spatial,
                 'temporal_RK4_relative_l2':temporal,'temporal_RK4_observed_order':order,
                 'energy_proxy_relative_drift':edrift,'filament_length_relative_drift':len_drift,
                 'minimum_midpoint_gap_initial':gap0,'minimum_midpoint_gap_final':gapf,
                 'length_initial':initial_len,'length_final':poly_length(fi)},
            'claims':{'three_d_Euler':False,'GP':False,'SST_physics':False,'intrinsic_clock':False,'isotopy_certified':False},
            'warnings':['finite-core Rosenhead midpoint model, free space; not full 3D Euler',
                       'energy uses a diagnostic regularized current-current proxy',
                       'clearance proxy is not a proof of temporal ambient isotopy']}
