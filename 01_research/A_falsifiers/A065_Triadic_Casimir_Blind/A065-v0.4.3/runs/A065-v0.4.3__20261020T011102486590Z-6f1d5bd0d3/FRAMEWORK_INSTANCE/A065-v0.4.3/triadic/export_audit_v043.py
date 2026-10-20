"""A065 v0.4.3 independent on-disk FP32/FP64 vortex-field auditing.

Does NOT trust saved in-run residuals, or infer Euler PKLSA source physics.
Spectral differentiation is recomputed from the file's *rounded* voxel arrays.
"""
from __future__ import annotations
import hashlib, io, json, re, zipfile
from pathlib import Path
import numpy as np

class EvidenceError(RuntimeError):pass

def source_hash(data:bytes):return hashlib.sha256(data).hexdigest()

def load_protocol(root):
    root=Path(root)
    raw=(root/'preregistration/POST_EXPORT_V043.json').read_bytes()
    pin=(root/'preregistration/POST_EXPORT_V043.sha256').read_text().strip()
    if source_hash(raw)!=pin:raise EvidenceError('V043_PROTOCOL_HASH_MISMATCH')
    c=json.loads(raw)
    for file,key in [('ARC_GPU_V041.json','prior_v041_protocol_sha256'),('VOLUME_EULER_V040.json','prior_v040_protocol_sha256')]:
        if source_hash((root/'preregistration'/file).read_bytes())!=c[key]:raise EvidenceError('UPSTREAM_PROTOCOL_HASH_MISMATCH')
    return c,pin

def rms(a):return float(np.sqrt(np.mean(np.asarray(a,dtype=np.float64)**2)))

def relative(a,b):return float(np.linalg.norm((np.asarray(a,dtype=np.float64)-b).ravel())/max(np.linalg.norm(b.ravel()),1e-30))

def rederive(u,omega,p,L,rho=1.):
    """Fresh independent double-precision spectral differentiation on exported voxels.

    Pressure identity: q=p/rho+|u|^2/2; ∆q=∇·(u×ω), with
    ω obtained INDEPENDENTLY from curl(u). Gauge (zero-frequency) removed.
    """
    u=np.asarray(u,dtype=np.float64);omega=np.asarray(omega,dtype=np.float64)
    p=np.asarray(p,dtype=np.float64)
    if u.ndim!=4 or u.shape[0]!=3 or omega.shape!=u.shape or p.shape!=u.shape[1:]:
        raise EvidenceError('INVALID_VOLUME_SHAPES')
    n=u.shape[1]
    if u.shape[1:]!=(n,n,n) or n<8 or not np.isfinite(u).all() or not np.isfinite(omega).all() or not np.isfinite(p).all():
        raise EvidenceError('INVALID_VOLUME_CONTENT')
    if not np.isfinite(L) or L<=0 or not np.isfinite(rho) or rho<=0:raise EvidenceError('INVALID_PHYSICAL_GRID')
    k=2*np.pi*np.fft.fftfreq(n,d=L/n)
    # v0.4.2 Euler source uses these exact unmodified Fourier frequency conventions.
    kx,ky,kz=k[:,None,None],k[None,:,None],k[None,None,:]
    U=np.fft.fftn(u,axes=(-3,-2,-1))
    curl_fft=np.array([1j*(ky*U[2]-kz*U[1]),1j*(kz*U[0]-kx*U[2]),1j*(kx*U[1]-ky*U[0])])
    curl=np.fft.ifftn(curl_fft,axes=(-3,-2,-1)).real
    div=np.fft.ifftn(1j*(kx*U[0]+ky*U[1]+kz*U[2])).real
    cross=np.cross(u,curl,axis=0)
    C=np.fft.fftn(cross,axes=(-3,-2,-1))
    poisson_src=np.fft.ifftn(1j*(kx*C[0]+ky*C[1]+kz*C[2])).real
    q=p/rho+.5*np.sum(u*u,axis=0)
    Q=np.fft.fftn(q)
    lap_q=np.fft.ifftn(-(kx*kx+ky*ky+kz*kz)*Q).real
    # The solver uses mean-gauge p=0; the constant q mode drops automatically.
    E=float(.5*rho*np.sum(u*u)*((L/n)**3))
    Z=float(.5*np.sum(omega*omega)*((L/n)**3))
    H=float(np.sum(u*omega)*((L/n)**3))
    return {'n':n,'L':float(L),'divergence_rms':rms(div),
        'divergence_max_abs':float(np.max(np.abs(div))),
        'curl_l2':relative(curl,omega),
        'pressure_poisson_l2':relative(lap_q,poisson_src),
        'kinetic_energy':E,'enstrophy':Z,'helicity':H,
        'pressure_mean':float(np.mean(p))}

def npz_bytes(data:bytes):
    with np.load(io.BytesIO(data),allow_pickle=False) as f:
        names=set(f.files)
        if not {'u','omega','p'}.issubset(names):raise EvidenceError('MISSING_FINAL_FIELDS')
        arrays={x:np.asarray(f[x]) for x in ('u','omega','p')}
        for x in ('u0','omega0','p0','L','dx','time','time0','times','trace_u','trace_omega','trace_p','u_refined','omega_refined','p_refined','source_sha256'):
            if x in names:arrays[x]=np.asarray(f[x])
    return arrays

def inspect_array_bytes(blob:bytes,kind:str,cfg:dict)->dict:
    d=npz_bytes(blob)
    expected=np.dtype('float64' if kind=='cpu' else 'float32')
    types={key:str(d[key].dtype) for key in ('u','omega','p')}
    if any(d[x].dtype!=expected for x in types):raise EvidenceError('BACKEND_DTYPE_INVALID_'+str(types))
    L=float(d.get('L',cfg['L']))
    if abs(L-cfg['L'])>1e-10:raise EvidenceError('BOX_LENGTH_MISMATCH')
    end=rederive(d['u'],d['omega'],d['p'],L,cfg['rho'])
    start=None
    if all(k in d for k in ('u0','omega0','p0')):
        for k in ('u0','omega0','p0'):
            if d[k].dtype!=expected:raise EvidenceError('INITIAL_DTYPE_INVALID')
        start=rederive(d['u0'],d['omega0'],d['p0'],L,cfg['rho'])
    drift=(abs(end['kinetic_energy']-start['kinetic_energy'])/max(abs(start['kinetic_energy']),1e-30)) if start else None
    criteria=cfg['post_export_tolerances'][kind]
    checks={
      'divergence':end['divergence_rms']<=criteria['divergence_rms'],
      'curl':end['curl_l2']<=criteria['curl_l2'],
      'pressure_poisson':end['pressure_poisson_l2']<=criteria['poisson_l2'],
      'energy':None if drift is None else drift<=criteria['energy_relative_drift']}
    refined=None
    if all(x in d for x in ('u_refined','omega_refined','p_refined')):
        for k in ('u_refined','omega_refined','p_refined'):
            if d[k].dtype!=expected:raise EvidenceError('REFINED_DTYPE_INVALID')
        refined={k:relative(d[k],d[k+'_refined']) for k in ('u','omega','p')}
    time_contract=(('time' in d) and abs(float(d['time'])-cfg['T'])<=1e-12 and ('time0' in d) and abs(float(d['time0']))<=1e-12)
    trace=None
    if all(x in d for x in ('times','trace_u','trace_omega','trace_p')):
        times=d['times'].tolist()
        if len(times)!=len(d['trace_u']) or len(times)!=len(d['trace_p']) or any(float(b)<=float(a) for a,b in zip(times,times[1:])):
            raise EvidenceError('INVALID_TRACE_TIMES')
        expected_times=[cfg['T']*j/cfg['coarse_steps'] for j in cfg['field_snapshots_indices']]
        if len(times)!=len(expected_times) or any(abs(float(a)-float(b))>1e-12 for a,b in zip(times,expected_times)):
            raise EvidenceError('TRACE_TIME_CONTRACT_MISMATCH')
        if start is not None and any(not np.array_equal(d['trace_'+k][0],d[k+'0']) for k in ('u','omega','p')):
            raise EvidenceError('TRACE_INITIAL_STATE_MISMATCH')
        if any(not np.array_equal(d['trace_'+k][-1],d[k]) for k in ('u','omega','p')):
            raise EvidenceError('TRACE_FINAL_STATE_MISMATCH')
        trace=[]
        for j,t in enumerate(times):
            trace.append({'t':float(t),**rederive(d['trace_u'][j],d['trace_omega'][j],d['trace_p'][j],L,cfg['rho'])})
    return {'sha256':source_hash(blob),'backend':kind,'dtype':types,'initial':start,'final':end,'energy_relative_drift':drift,
            'checks':checks,'status':'FAIL' if any(v is False for v in checks.values()) else ('PASS' if all(v is True for v in checks.values()) else 'UNRESOLVED'),
            'trace':trace,'has_initial':start is not None,'time_refinement':refined,'time_contract_compliant':time_contract,'source_sha256':str(d['source_sha256'].item()) if 'source_sha256' in d else None}

def named_volumes_from_directory(path):
    path=Path(path)
    if not path.exists():raise FileNotFoundError(path)
    if path.is_dir():
        for p in sorted(path.rglob('*.npz')):
            if 'V04' in p.name or 'V043' in p.name:yield p.name,p.read_bytes()
    elif path.suffix.lower()=='.npz':yield path.name,path.read_bytes()
    elif path.suffix.lower()=='.zip':
        with zipfile.ZipFile(path) as z:
            for name in sorted(z.namelist()):
                if name.endswith('.npz') and ('V04' in name or 'V043' in name):
                    yield Path(name).name,z.read(name)
                elif name.endswith('_BLIND_RESULTS.zip'):
                    with zipfile.ZipFile(io.BytesIO(z.read(name))) as inner:
                        for n in sorted(inner.namelist()):
                            if n.endswith('.npz') and ('V04' in n or 'V043' in n):
                                yield Path(n).name,inner.read(n)
    else:raise EvidenceError('INPUT_MUST_BE_DIRECTORY_ZIP_OR_NPZ')

def audit_files(root,paths,*,require_new=False):
    cfg,pin=load_protocol(root)
    items={};unexpected=[]
    for path in paths:
        for name,blob in named_volumes_from_directory(path):
            b='gpu' if 'ARC_FP32' in name or '_GPU_' in name else 'cpu' if 'CPU_FP64' in name or '_CPU_' in name or (name.startswith('V040_') and name.endswith('_EULER.npz')) else None
            mat=re.search(r'(torus_3_1_(?:direct|hoste))_N(48|64|96)',name)
            if mat is None or b is None:
                unexpected.append(name);continue
            sid,n=mat.group(1),int(mat.group(2))
            key=f'{sid}_N{n}_{b}'
            if key in items:
                if items[key]['sha256']==source_hash(blob):continue
                raise EvidenceError('CONFLICTING_EVIDENCE_'+key)
            row=inspect_array_bytes(blob,b,cfg)
            if row['final']['n']!=n:raise EvidenceError('GRID_NAME_SHAPE_MISMATCH:'+key)
            row.update({'name':name,'seed':sid,'n':n})
            items[key]=row
    grids={};pairerrors={};source_consistency={}
    for sid in cfg['seeds']:
        for n in cfg['grids']:
            gkey=f'{sid}_N{n}_gpu';ckey=f'{sid}_N{n}_cpu'
            if gkey not in items or ckey not in items:continue
            cp,gg=items[ckey],items[gkey]
            source_consistency[f'{sid}_N{n}']=(cp['source_sha256']==gg['source_sha256']) if cp['source_sha256'] is not None and gg['source_sha256'] is not None else None
            grids[f'{sid}_N{n}']={'cpu':cp['status'],'gpu':gg['status']}
    count={b:sum(1 for k in items if k.endswith('_'+b)) for b in ('cpu','gpu')}
    cstates=[v['status'] for v in items.values() if v['backend']=='cpu']
    gstates=[v['status'] for v in items.values() if v['backend']=='gpu']
    def category(states):
        if not states:return 'NOT_RUN_PREREQUISITE'
        if 'FAIL' in states:return 'FAIL'
        if 'UNRESOLVED' in states:return 'UNRESOLVED'
        if len(states)!=6:return 'NOT_RUN_PREREQUISITE'
        return 'PASS'
    refinements=[v['time_refinement'] for v in items.values()]
    goodref=(len(refinements)==12 and all(x is not None for x in refinements))
    refinestatus=('PASS' if goodref and all(all(x[k]<=cfg['time_refinement_tolerance'][k] for k in ('u','omega','p')) for x in refinements) else
                   'FAIL' if goodref else 'NOT_RUN_PREREQUISITE')
    gates={
      'G53':{'status':refinestatus,'reason':'Independently compared serialized coarse/fine field pairs at common T, 16 vs 32 RK4 steps'},
      'G50':{'status':category(cstates),'reason':'Independent Fourier checks using actually exported CPU FP64 voxels; requires all six'},
      'G51':{'status':category(gstates),'reason':'Independent Fourier checks using actually exported Arc FP32 voxels; requires all six'},
      'G52':{'status':('PASS' if len(items)==12 and len(source_consistency)==6 and all(source_consistency.values()) and
                      all(v['time_contract_compliant'] and v['has_initial'] and v['trace'] is not None and len(v['trace'])==3 for v in items.values())
                    else 'FAIL' if any(v is False for v in source_consistency.values()) else 'NOT_RUN_PREREQUISITE'),
            'reason':'Initial and multitime fields required for all twelve volumes; old v0.4.2 end-only fields cannot PASS'},
      'G54':{'status':'UNRESOLVED','reason':'Numerical pressure reconstruction is not independent physical PKLSA pressure evidence.'}}
    return {'schema':'A065-V043-INDEPENDENT-EXPORT-AUDIT-1','v043_prereg_sha256':pin,'files':items,'volume_pairs':grids,'source_consistency':source_consistency,
            'count':count,'unexpected':unexpected,'gates':gates,'physical_PKLSA':'UNRESOLVED'}
