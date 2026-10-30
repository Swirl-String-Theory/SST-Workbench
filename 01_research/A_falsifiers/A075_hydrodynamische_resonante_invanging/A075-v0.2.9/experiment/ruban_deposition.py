"""A075-v0.2.9: adversarial initial-field deposition and geometric tracking.

Only an incompressible periodic Euler *screening* model. The tracer polygon
is not a reconstructed vortex centerline; the sampled vorticity ridge is a
local proxy, not a certified material vortex tube or topological invariant.
Ruban's filament delta and xi are NOT the Gaussian Euler sigma.
"""
from __future__ import annotations
import csv, dataclasses, hashlib, json, math, zipfile
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .euler3d import Config, Euler3D, resample_closed, stable_dt
from .ruban import PRIMARY, B0, load_primary_seed, analytic_torus, resolution_gate
from .heartbeat import phase,advance

SCHEMA='A075-RUBAN-DEPOSITION-AND-FIELD-TRACKING-1'


def _write(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf8')


def _curve(root, kind):
    if kind=='ruban':
        return load_primary_seed(Path(root)/'inputs/ruban_t23'/PRIMARY)
    if kind=='analytic_032':
        return analytic_torus(.32,n=2048),{'source':'LEGACY_ANALYTIC_T23','B0':.32,
            'source_file':None,'topology_verification':'ANALYTIC_ONLY'}
    raise ValueError('Unknown curve')


def _config(root, kind, n, box, sigma, threads):
    return Config(n=n,box=box,core=sigma,gamma_receiver=2*math.pi,
        incoming=False,receiver_on=True,initial_condition=(
        'ruban_isolated' if kind=='ruban' else 'legacy_t23_isolated'),
        ruban_seed_path=str(Path(root)/'inputs/ruban_t23'/PRIMARY),
        geometry='ruban_t23_B0_0p154' if kind=='ruban' else 'analytic_t23_B0_0p32',
        backend='cpu-scipy-fft',threads=threads,dt=.01,final_time=.02)


def trilinear(field, positions, box):
    """Cell-centered periodic 3-D interpolation for vector/scalar Euler fields."""
    positions=np.asarray(positions,dtype=float)
    a=np.asarray(field)
    n=a.shape[0]
    if a.shape[:3]!=(n,n,n) or positions.shape[-1]!=3:
        raise ValueError('Invalid interpolation shapes')
    xyz=(positions+box/2)*n/box-.5
    ij=np.floor(xyz).astype(np.int64)
    f=xyz-ij
    out=np.zeros((len(positions),)+a.shape[3:],dtype=float)
    for i in (0,1):
      for j in (0,1):
        for k in (0,1):
          ind=(ij+np.array([i,j,k]))%n
          w=np.prod(np.where(np.array([i,j,k])==1,f,1-f),axis=1)
          q=a[ind[:,0],ind[:,1],ind[:,2]]
          out+=q*w.reshape((-1,)+(1,)*(a.ndim-3))
    return out


def _frames(points):
    d=np.roll(points,-1,axis=0)-np.roll(points,1,axis=0)
    t=d/np.maximum(np.linalg.norm(d,axis=1)[:,None],1e-30)
    ref=np.tile([0.,0.,1.],(len(t),1))
    ref[np.abs(t[:,2])>.85]=[1.,0.,0.]
    n=np.cross(t,ref);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-30)
    b=np.cross(t,n)
    return t,n,b


def ridge_proxy(omega, markers, box, sigma, rminor, *, stencil=7):
    """Local field-based cross-section weighted centroid near advected markers.

    This can fail when two branches overlap or sigma > minor radius; no automatic
    topological or physical tube certification is possible.
    """
    markers=np.asarray(markers)
    tang,normal,binormal=_frames(markers)
    dx=box/omega.shape[0]
    radius=min(1.5*sigma,max(.75*rminor,2*dx))
    offs=np.linspace(-radius,radius,stencil)
    aa,bb=np.meshgrid(offs,offs,indexing='ij')
    samples=(markers[:,None,None,:]+aa[None,:,:,None]*normal[:,None,None,:]
             +bb[None,:,:,None]*binormal[:,None,None,:])
    v=trilinear(omega,samples.reshape(-1,3),box).reshape(len(markers),stencil,stencil,3)
    parallel=np.sum(v*tang[:,None,None,:],axis=-1)
    weight=np.maximum(parallel,0.)**2
    mass=weight.sum(axis=(1,2))
    ok=mass>1e-25
    u=np.divide((weight*aa[None,:,:]).sum(axis=(1,2)),mass,out=np.zeros(len(markers)),where=ok)
    w=np.divide((weight*bb[None,:,:]).sum(axis=(1,2)),mass,out=np.zeros(len(markers)),where=ok)
    ridge=markers+u[:,None]*normal+w[:,None]*binormal
    centers=trilinear(omega,markers,box)
    align=np.abs(np.sum(centers*tang,axis=1))/np.maximum(np.linalg.norm(centers,axis=1),1e-30)
    offset=np.sqrt(u*u+w*w)
    return {'ridge':ridge,'offset':offset,'alignment':align,'valid':ok,
        'radius':float(radius),'stencil':stencil,
        'valid_fraction':float(np.mean(ok)),
        'ridge_offset_rms':float(np.sqrt(np.mean(offset[ok]**2))) if np.any(ok) else None,
        'ridge_offset_max':float(np.max(offset[ok])) if np.any(ok) else None,
        'center_vorticity_alignment_median':float(np.median(align)),
        'cross_section_overlap_risk':bool(sigma>=rminor),
        'interpretation':'LOCAL_VORTICITY_RIDGE_PROXY_NOT_TOPOLOGY'}


def _localization(omega, points, box):
    """Enstrophy-weighted distance-to-input-curve histogram on a documented voxel subsample."""
    n=omega.shape[0]
    stride=max(1,math.ceil(n/96))
    samples=np.arange(0,n,stride)
    x=(samples+.5)*box/n-box/2
    tree=cKDTree((np.asarray(points)+box/2)%box,boxsize=box)
    total=0.;near=0.;dist_sq=0.;count=0
    for a in x:
        y,z=np.meshgrid(x,x,indexing='ij')
        coords=np.column_stack([np.full(y.size,a),y.ravel(),z.ravel()])
        d=tree.query((coords+box/2)%box,k=1,workers=1)[0]
        idx=int(round((a+box/2)*n/box-.5))
        # Indices are the actual sampled voxel locations, not nearest interpolations.
        ix=np.searchsorted((np.arange(n)+.5)*box/n-box/2,x)
        weights=np.sum(omega[idx][np.ix_(ix,ix)]**2,axis=-1).ravel()
        total+=float(np.sum(weights))
        near+=float(np.sum(weights[d<=2*box/n]))  # explicitly grid-relative, not a core-scale claim
        dist_sq+=float(np.sum(weights*d*d))
        count+=len(d)
    return {'sample_stride_voxels':stride,'sample_count':count,
        'enstrophy_weighted_rms_distance_to_seed':math.sqrt(dist_sq/max(total,1e-30)),
        'fraction_enstrophy_within_2_dx_of_seed':near/max(total,1e-30),
        'nearest_curve_reference':'initial_2048_point_curve_periodic_KDTree',
        'spatial_sampling_qualified':False}


def initial_field(root, kind, n, box, sigma, *, threads=1, localization=True):
    points,prov=_curve(root,kind)
    cfg=_config(root,kind,n,box,sigma,threads)
    s=Euler3D(cfg)
    uh,fieldprov=s.initial_velocity()
    wh=s.curl_hat(uh)
    om=s.ifft(wh)
    E=s.global_energy_hat(uh)
    Z=float(.5*s.dx**3/n**3*np.sum(np.abs(wh)**2))
    mode=np.meshgrid(*[np.fft.fftfreq(n)*n]*3,indexing='ij')
    kval=np.sqrt(sum(k*k for k in mode))
    poww=np.sum(np.abs(wh)**2,axis=-1)
    # Shell just inside 2/3 de-aliasing boundary, not full Nyquist shell.
    frac=float(np.sum(poww[kval>=.7*n/3])/max(np.sum(poww),1e-30))
    # Raw deposition (before Helmholtz projection, Gaussian smoothing, de-aliasing).
    raw=np.zeros((n,n,n,3),float)
    s.source_curve(raw,points,cfg.gamma_receiver)
    rawhat=s.fft(raw)
    raw_norm=float(np.sum(np.abs(rawhat)**2))
    proj=s.project(rawhat)
    projected_norm=float(np.sum(np.abs(proj)**2))
    filtered=proj*np.exp(-.5*sigma*sigma*s.k2)[...,None]
    smooth_norm=float(np.sum(np.abs(filtered)**2))
    del raw,rawhat,proj,filtered
    b0=.154 if kind=='ruban' else .32
    res=resolution_gate(box,n,sigma,b0)
    loc=_localization(om,points,box) if localization else None
    ridge=ridge_proxy(om,resample_closed(points,96),box,sigma,b0)
    diag={'schema':SCHEMA,'case':kind,'geometry_B0':b0,'input_provenance':prov,
          'actual_euler_geometry_provenance':fieldprov,'n':n,'box':box,'sigma':sigma,
          'resolution':res,'initial_energy_J_normalized':E,
          'initial_enstrophy_m3_per_s2_normalized':Z,
          'spectral_enstrophy_fraction_near_dealias_boundary':frac,
          'deposition_L2_projected_over_raw_squared':projected_norm/max(raw_norm,1e-30),
          'deposition_L2_smoothed_over_projected_squared':smooth_norm/max(projected_norm,1e-30),
          'deposition_L2_raw_to_smoothed_total':smooth_norm/max(raw_norm,1e-30),
          'ridge_initial':{k:v for k,v in ridge.items() if k not in ('ridge','offset','alignment','valid')},
          'localization':loc,'spatial_fidelity_qualified':False,
          'topology_certified':False,'ruban_delta_is_euler_sigma':False,
          'model':'3D_PERIODIC_FOURIER_GALERKIN_EULER_GAUSSIAN_INITIALIZATION',
          'status':'DIAGNOSTIC_ONLY'}
    sl=om[:,n//2,:,:]
    return diag,sl, s,uh,points


def _rigid_rms(a,b):
    """Best rigid registration with cyclic relabeling, not a topology test."""
    a=a-a.mean(axis=0);b=b-b.mean(axis=0)
    best=float('inf')
    for shift in range(len(a)):
        m=np.roll(a,shift,axis=0)
        U,_,V=np.linalg.svd(m.T@b)
        D=np.diag([1.,1.,np.sign(np.linalg.det(U@V))])
        err=np.sqrt(np.mean(np.sum((m@(U@D@V)-b)**2,axis=1)))
        best=min(best,float(err))
    return best


def track_field(s,uh,points,*,T=.02,dt=.01,markers_count=96):
    """Heun advected material markers + independent Euler vorticity cross sections.

    Advected material markers are NOT a certified reconstructed vortex line.
    """
    if T<=0 or dt<=0 or markers_count<24:raise ValueError('Invalid tracking parameters')
    markers=resample_closed(points,markers_count)
    origin=markers.copy()
    initial=ridge_proxy(s.ifft(s.curl_hat(uh)),markers,s.c.box,s.c.core,
        .154 if s.c.initial_condition=='ruban_isolated' else .32)
    series=[];frames=[markers.copy()];ridge_frames=[initial['ridge'].copy()];times=[0.]
    t=0.;steps=0
    while T-t>max(1e-12,T*1e-12):
        umax,omax=s.adapt_metrics(uh)
        h=stable_dt(dataclasses.replace(s.c,dt=dt),s.dx,umax,omax,T-t)
        v0=s.ifft(uh)
        u0=trilinear(v0,markers,s.c.box)
        new=s.rk4(uh,h)
        u1=trilinear(s.ifft(new),markers+h*u0,s.c.box)
        markers=markers+.5*h*(u0+u1)
        uh=new;t+=h;steps+=1
        if steps>10000:raise RuntimeError('TRACK_MAX_STEPS')
        omega=s.ifft(s.curl_hat(uh))
        rminor=.154 if s.c.initial_condition=='ruban_isolated' else .32
        ridge=ridge_proxy(omega,markers,s.c.box,s.c.core,rminor)
        legs=np.linalg.norm(np.roll(markers,-1,axis=0)-markers,axis=1)
        series.append({'t':float(t),'step':steps,
            'marker_rigid_cyclic_rms':_rigid_rms(markers,origin),
            'marker_length':float(np.sum(legs)),
            'marker_segment_ratio':float(legs.max()/legs.min()),
            'ridge_offset_rms':ridge['ridge_offset_rms'],
            'ridge_valid_fraction':ridge['valid_fraction'],
            'ridge_alignment_median':ridge['center_vorticity_alignment_median'],
            'cross_section_overlap_risk':ridge['cross_section_overlap_risk']})
        frames.append(markers.copy());ridge_frames.append(ridge['ridge'].copy());times.append(t)
    return ({'schema':'A075-RUBAN-MATERIAL-MARKERS-AND-FIELD-RIDGE-1',
        'marker_count':markers_count,'time_final':float(t),'steps':steps,
        'integration':'EULER_RK4_FIELD_WITH_HEUN_TRAPEZOIDAL_PASSIVE_MARKERS',
        'initial_ridge_offset_rms':initial['ridge_offset_rms'],
        'history':series,'dynamic_topology_certified':False,
        'material_markers_are_not_vortex_centerlines':True,
        'vorticity_ridge_is_local_proxy':True,'status':'DIAGNOSTIC_ONLY'},
        {'times':np.asarray(times),'markers':np.asarray(frames),'ridge_proxy':np.asarray(ridge_frames)})


def _plot_slice(path, slices, *, n, box, sigma):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return 'MATPLOTLIB_NOT_INSTALLED'
    a,b=slices
    scale=max(float(np.max(np.linalg.norm(a,axis=-1))),float(np.max(np.linalg.norm(b,axis=-1))),1e-30)
    fig,axs=plt.subplots(1,2,figsize=(10,4.2),layout='constrained')
    for ax,kind,arr in zip(axs,['Ruban B0=0.154','Analytic B0=0.32'],slices):
        im=ax.imshow(np.linalg.norm(arr,axis=-1).T,origin='lower',extent=[-box/2,box/2]*2,
             cmap='magma',vmin=0,vmax=scale,interpolation='nearest')
        ax.set_title(kind);ax.set_xlabel('x (model length)');ax.set_ylabel('z (model length)')
        ax.set_xlim(-2,2);ax.set_ylim(-2,2)
    fig.colorbar(im,ax=axs,shrink=.8,label='|vorticity| (model units)')
    fig.suptitle(f'Initial Euler vorticity, y~0 | N={n} | L={box:g} | sigma={sigma:g}')
    fig.savefig(path,dpi=160);plt.close(fig)
    return 'CREATED'


def run_deposition(root, out, *, grids=(24,32), sigmas=(.5,), boxes=(10.,),
                   threads=1, allow_expensive=False, track=False, track_T=.02, track_dt=.01):
    root=Path(root);out=Path(out)
    grids=tuple(sorted(set(int(x) for x in grids)))
    sigmas=tuple(sorted(set(float(x) for x in sigmas)))
    boxes=tuple(sorted(set(float(x) for x in boxes)))
    if not grids or not sigmas or not boxes:raise ValueError('Empty scan')
    if any(n<16 or n>256 or n%8 for n in grids):raise ValueError('Grid must be multiples of 8, 16..256')
    if any(not .005<=s<=2 for s in sigmas):raise ValueError('Sigma outside safe diagnostic range')
    if any(not 3<=L<=30 for L in boxes):raise ValueError('Box outside safe diagnostic range')
    if len(grids)*len(sigmas)*len(boxes)>30 and not allow_expensive:
        raise RuntimeError('SCAN_BUDGET_EXCEEDED: use --allow-expensive')
    if max(grids)>128 and not allow_expensive:
        raise RuntimeError('GRID_BUDGET_EXCEEDED: --allow-expensive required above N128')
    if track and len(grids)*len(sigmas)*len(boxes)!=1:
        raise ValueError('Tracking needs exactly one grid, sigma, box combination')
    out.mkdir(parents=True,exist_ok=False)
    rows=[];all_cases={};plots={}
    stage=0;total_stages=2*len(grids)*len(sigmas)*len(boxes)
    for L in boxes:
      for n in grids:
       for sigma in sigmas:
        tag=f'L{L:g}_N{n}_sigma{sigma:g}'.replace('.','p')
        slices=[]
        for kind in ('ruban','analytic_032'):
            stage+=1
            phase('ruban_initial_field_deposition',backend='cpu-scipy-fft',knot=kind,grid=n,
                  phase_index=stage,phase_total=total_stages,
                  message=f'L={L:g} sigma={sigma:g}; projection, Gaussian smoothing, field ridge')
            d,sl,solver,uh,points=initial_field(root,kind,n,L,sigma,threads=threads)
            name=f'{tag}_{kind}'
            if track:
                d['tracking'],tr=track_field(solver,uh,points,T=track_T,dt=track_dt)
                np.savez_compressed(out/f'{name}_markers.npz',**tr)
                with (out/f'{name}_tracking.csv').open('w',newline='',encoding='utf8') as f:
                    w=csv.DictWriter(f,fieldnames=d['tracking']['history'][0].keys());w.writeheader();w.writerows(d['tracking']['history'])
            _write(out/f'{name}.json',d)
            np.save(out/f'{name}_vorticity_xz_y0.npy',sl)
            slices.append(sl)
            all_cases[name]=d
            rows.append({'case':kind,'grid':n,'box':L,'sigma':sigma,'B0':d['geometry_B0'],
                'dx':d['resolution']['dx'],'rminor_cells':d['resolution']['rminor_cells'],
                'sigma_cells':d['resolution']['sigma_cells'],
                'sigma_over_rminor':d['resolution']['sigma_over_rminor'],
                'energy':d['initial_energy_J_normalized'],
                'enstrophy':d['initial_enstrophy_m3_per_s2_normalized'],
                'near_cutoff_fraction':d['spectral_enstrophy_fraction_near_dealias_boundary'],
                'ridge_offset_rms':d['ridge_initial']['ridge_offset_rms'],
                'field_ridge_valid_fraction':d['ridge_initial']['valid_fraction'],
                'localization_rms':d['localization']['enstrophy_weighted_rms_distance_to_seed'],
                'status':'DIAGNOSTIC_ONLY'})
        plots[tag]=_plot_slice(out/f'{tag}_xz_compare.png',slices,n=n,box=L,sigma=sigma)
    with (out/'INITIAL_FIELD_MATRIX.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    comparisons=[]
    for L in boxes:
      for sigma in sigmas:
       for kind in ('ruban','analytic_032'):
        rs=sorted((r for r in rows if r['box']==L and r['sigma']==sigma and r['case']==kind),key=lambda r:r['grid'])
        for a,b in zip(rs,rs[1:]):
            comparisons.append({'case':kind,'box':L,'sigma':sigma,'grid_low':a['grid'],'grid_high':b['grid'],
              'relative_initial_energy_change':(b['energy']-a['energy'])/max(abs(b['energy']),1e-30),
              'relative_initial_enstrophy_change':(b['enstrophy']-a['enstrophy'])/max(abs(b['enstrophy']),1e-30),
              'initial_energy_below_1pct_DIAGNOSTIC_ONLY':abs(b['energy']-a['energy'])/max(abs(b['energy']),1e-30)<.01,
              'spatial_convergence_certified':False})
    # A geometry resolution target is a *screening proposal*, not physical proof.
    qualification={'schema':SCHEMA,'source_version':'v0.2.9','framework_version':'1.1.0',
       'framework_gates':'NOT_EXECUTED','physical_answer':'UNRESOLVED',
       'cases':len(rows),'parameters':{'grids':grids,'sigmas':sigmas,'boxes':boxes,'track':track},
       'screening_thresholds_PROPOSED_NOT_PHYSICAL_GATES':{
           'rminor_cells_at_least':4,'sigma_cells_at_least':3,
           'sigma_over_rminor_at_most':.5,'initial_energy_grid_change_below':.01},
       'resolution_screening':[{ 'case':r['case'],'grid':r['grid'],'box':r['box'],'sigma':r['sigma'],
           'all_three_geometric_ratios_satisfied':bool(r['rminor_cells']>=4 and r['sigma_cells']>=3 and r['sigma_over_rminor']<=.5),
           'physical_qualification':False} for r in rows],
       'grid_comparisons':comparisons,'plot_status':plots,
       'scientific_notes':['Ruban delta is a filament regularizer, not Euler Gaussian sigma.',
           'Spatial convergence needs at least three resolved levels and domain/core variation.',
           'Passive material markers and local vorticity ridge are not certified knot topology.',
           'The Euler model has periodic images; no free-space limit is demonstrated.'],
       'status':'DEVELOPMENT_ONLY'}
    _write(out/'DEPOSITION_QUALIFICATION.json',qualification)
    from .ruban_report import generate_deposition_report
    qualification['per_run_report_pdf']=str(generate_deposition_report(out,qualification).name)
    _write(out/'DEPOSITION_QUALIFICATION.json',qualification)
    phase('ruban_deposition_completed',phase_index=total_stages,phase_total=total_stages,
          message='Initial-field matrices and optional marker/ridge tracks written')
    return qualification


def package_outputs(root,folder):
    """Versioned diagnostic archive + checksum; no private reveal files."""
    root=Path(root);folder=Path(folder)
    base='A075_Hydrodynamische_Resonante_Invanging_v0.2.9-outputs'
    archive=root.parent/f'{base}.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file():
                if any(token in p.name.upper() for token in ('PRIVATE','REVEAL','SECRET','KEY')):
                    raise RuntimeError('Refusing to package potentially private diagnostic data')
                z.write(p,arcname=str(Path(base)/p.relative_to(folder)))
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name+'.sha256').write_text(digest+'  '+archive.name+'\n')
    return {'archive':str(archive),'sha256':digest}
