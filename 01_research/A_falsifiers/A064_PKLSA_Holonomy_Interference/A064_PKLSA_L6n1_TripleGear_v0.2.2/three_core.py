"""A064 three-core Borromean-SKELETON, locally knotted component research model.

Not a Brunnian link once local knots are tied; not E011-qualified dynamics.
Reference Borromean ellipses: https://www.paulbourke.org/geometry/borromean/
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
from scipy.ndimage import map_coordinates
from skimage.measure import marching_cubes
from a064.analysis import closed_components, field_data, rk4, transport_audit, sample_scalar
from a064.flow import SnapshotFlow, file_hash
from euler_extension.spectral import SpectralEuler3D,evolve

ROOT=Path(__file__).resolve().parent
CASES={'552_61':('5_2','5_2','6_1'),'661_52':('6_1','6_1','5_2')}
CLASS='geometry_initialized_periodic_3d_euler_model'


class PeriodicEulerFlow(SnapshotFlow):
    """Correct periodic sampling, unlike nonperiodic NPZ interpolation."""
    def velocity(self,points,time=0.):
        p=np.asarray(points,float).reshape(-1,3)
        t=float(time)
        if t<self.times[0]-1e-9 or t>self.times[-1]+1e-9:
            raise ValueError('time outside model trajectory')
        t=float(np.clip(t,self.times[0],self.times[-1]))
        i=int(np.clip(np.searchsorted(self.times,t,side='right')-1,0,len(self.times)-2))
        f=float((t-self.times[i])/(self.times[i+1]-self.times[i]))
        ix=np.stack([(p[:,j]-self.axes[j][0])/float(np.diff(self.axes[j]).mean()) for j in range(3)])
        a=np.stack([map_coordinates(self.v[i,...,j],ix,order=1,mode='grid-wrap',prefilter=False) for j in range(3)],axis=-1)
        b=np.stack([map_coordinates(self.v[i+1,...,j],ix,order=1,mode='grid-wrap',prefilter=False) for j in range(3)],axis=-1)
        return a*(1-f)+b*f
    def frame(self,axes,time):
        pts=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1)
        return self.velocity(pts.reshape(-1,3),time).reshape(*pts.shape)


def canonical_hash(obj):
    s=json.dumps(obj,sort_keys=True,allow_nan=False,separators=(',',':')).encode()
    return hashlib.sha256(s).hexdigest()


def borromean_ellipse(index,t,R=2.,r=1.):
    """Paul Bourke's explicit centered 3-ellipse Borromean embedding (R=2,r=1)."""
    c,s=np.cos(t),np.sin(t)
    if index==0:return np.stack([0*c,R*c,r*s],axis=-1)
    if index==1:return np.stack([r*c,0*c,R*s],axis=-1)
    if index==2:return np.stack([R*c,r*s,0*c],axis=-1)
    raise ValueError(index)


def knot_bead(base_index,source,window=.21,diameter=.72,ellpts=180):
    """Local connected-sum geometry using an exterior-facing cut of a polygonal knot.

    The cut is at original edge 0.  Both leads are routed outside the knotted
    bead so that the 5_2 / 6_1 determinant is preserved (audited separately).
    """
    native=np.loadtxt(source)
    if native.ndim!=2 or native.shape[1]!=3 or len(native)<30:
        raise ValueError('Invalid raw source knot')
    # The omitted cut edge is native[0] -> native[1].
    src=np.vstack([native[1:],native[:1]])
    chord=src[-1]-src[0]
    eps=.002
    tangent=(borromean_ellipse(base_index,np.array([eps]))[0]
              -borromean_ellipse(base_index,np.array([-eps]))[0])
    tangent/=np.linalg.norm(tangent)
    v=chord/np.linalg.norm(chord)
    axis=np.cross(v,tangent);dot=np.clip(v@tangent,-1.,1.)
    rot=(Rotation.from_rotvec(axis/np.linalg.norm(axis)*np.arccos(dot))
           if np.linalg.norm(axis)>1e-8 else Rotation.identity())
    bead=rot.apply(src-src.mean(axis=0))
    bead*=diameter/max(np.ptp(bead,axis=0).max(),1e-9)
    origin=borromean_ellipse(base_index,np.array([0.]))[0]
    # Component 1 points INWARD to avoid approaching component 2 near x=2.
    radial=origin/np.linalg.norm(origin)*(1. if base_index!=1 else -1.)
    seam=(bead[0]+bead[-1])*.5
    seam-=np.dot(seam,tangent)*tangent
    seam/=np.linalg.norm(seam)
    theta=np.arctan2(np.dot(tangent,np.cross(seam,-radial)),np.dot(seam,-radial))
    bead=Rotation.from_rotvec(theta*tangent).apply(bead)
    bead+=origin+.39*radial
    t=np.linspace(window,2*np.pi-window,ellpts)
    parent_arc=borromean_ellipse(base_index,t)
    b=parent_arc[-1];a=parent_arc[0]
    poly=np.concatenate([parent_arc,(b+bead[0])[None,:]*.5,bead,
                         (bead[-1]+a)[None,:]*.5])
    return poly,{'source_file':source.name,'source_sha256':file_hash(source),
                 'native_points':len(native),'knot_bead_extent':diameter,
                 'removed_half_angle_rad':window,'omitted_knot_edge':[0,1],
                 'offset_radial':.39,'bead_orientation':float(1 if base_index!=1 else -1),
                 'construction':'local_connected_sum_exterior_seam',
                 'topology_validation':'KNOT_DETERMINANT_SCREEN_ONLY'}


def knot_determinant(points,angles=(21,37,17)):
    """Alexander/Wirtinger matrix evaluated at t=-1; determinant knot invariant.

    Does NOT uniquely identify the knot; checks that a local knot was not untied.
    """
    p=np.asarray(points,float);n=len(p)
    basis=Rotation.from_euler('xyz',angles,degrees=True).as_matrix()
    pr=p@basis
    a=pr[:,:2];h=pr[:,2]
    d=np.roll(a,-1,axis=0)-a;dh=np.roll(h,-1)-h
    delta=a[None,:,:]-a[:,None,:]
    den=d[:,None,0]*d[None,:,1]-d[:,None,1]*d[None,:,0]
    cross=lambda x,y:x[...,0]*y[...,1]-x[...,1]*y[...,0]
    with np.errstate(divide='ignore',invalid='ignore'):
        u=cross(delta,d[None,:,:])/den
        v=cross(delta,d[:,None,:])/den
    ii,jj=np.indices((n,n))
    mask=((ii<jj)&((jj-ii)!=1)&((jj-ii)!=(n-1))
           &(np.abs(den)>1e-10)&(u>1e-7)&(u<1-1e-7)&(v>1e-7)&(v<1-1e-7))
    seq=[]
    for i,j in np.argwhere(mask):
        ha=h[i]+u[i,j]*dh[i];hb=h[j]+v[i,j]*dh[j]
        if abs(ha-hb)<1e-6:continue
        under=i+u[i,j] if ha<hb else j+v[i,j]
        over=j+v[i,j] if ha<hb else i+u[i,j]
        seq.append((under,over))
    seq.sort();k=len(seq)
    if not k:return 1
    starts=np.array([x[0] for x in seq]);mat=np.zeros((k,k),dtype=float)
    for j,(_,over) in enumerate(seq):
        oi=(np.searchsorted(starts,over,side='right')-1)%k
        mat[j,oi]+=2;mat[j,(j-1)%k]-=1;mat[j,j]-=1
    return int(abs(round(np.linalg.det(mat[:-1,:-1]))))


def determinant_multiview(points):
    return [knot_determinant(points,angs) for angs in ((21,37,17),(32,51,14),(60,25,40))]


def create_link(case,diameter=.82,ellpts=180):
    if case not in CASES:raise ValueError('unknown case')
    curves=[];meta=[]
    for i,knot in enumerate(CASES[case]):
        src=ROOT/'data'/'PKLSA_RAW_NATIVE_UNQUALIFIED'/('knot_'+knot.replace('_','.')+'.txt')
        pts,details=knot_bead(i,src,diameter=diameter,ellpts=ellpts)
        curves.append(pts);meta.append({'component':i,'knot_label':knot,**details})
    return curves,meta


def gauss_lk(p,q):
    a=np.asarray(p);b=np.asarray(q)
    da=np.roll(a,-1,axis=0)-a;db=np.roll(b,-1,axis=0)-b
    ma=(a+np.roll(a,-1,axis=0))*.5
    mb=(b+np.roll(b,-1,axis=0))*.5
    r=ma[:,None,:]-mb[None,:,:]
    den=np.maximum(np.einsum('ijk,ijk->ij',r,r),1e-20)**1.5
    return float(np.sum(np.einsum('ijk,ijk->ij',np.cross(da[:,None,:],db[None,:,:]),r)/den)/(4*np.pi))


def topology_audit(curves):
    det=[determinant_multiview(c) for c in curves]
    pair=[]
    for i,j in ((0,1),(0,2),(1,2)):
        lk=gauss_lk(curves[i],curves[j]); p=cKDTree(curves[i]).query(curves[j])[0]
        pair.append({'pair':[i,j],'gauss_linking_midpoint':lk,'nearest_sample_distance':float(p.min())})
    return {'n_components':3,'component_knot_determinant_multiview':det,'pairwise':pair,'pairwise_lk_zero_screen':all(abs(x['gauss_linking_midpoint'])<.03 for x in pair),
            'pairwise_min_separation_screen':all(x['nearest_sample_distance']>.12 for x in pair),
            'milnor_mu123_gate':'UNRESOLVED_NOT_COMPUTED',
            'component_knot_identity_gate':'DETERMINANT_COMPATIBLE_NOT_UNIQUE_IDENTIFICATION',
            'borromean_parent_embedding':'REFERENCE_PARAMETRIC_ELLIPSES',
            'strict_brunnian':'NO_LOCALLY_KNOTTED_COMPONENTS'}


def init_three_core(solver,curves,core=.39,target_rms=1.):
    n=solver.n
    ax=(np.arange(n)-n//2)*solver.dx
    coords=np.stack(np.meshgrid(ax,ax,ax,indexing='ij'),-1)
    w=np.zeros((n,n,n,3),float)
    for curve in curves:
        ds=np.roll(curve,-1,axis=0)-curve
        mids=(curve+np.roll(curve,-1,axis=0))*.5
        # Keep all components in the same Cartesian frame: DO NOT renormalize individually.
        for start in range(0,len(mids),8):
            delta=coords[...,None,:]-mids[start:start+8]
            delta=(delta+solver.box/2)%solver.box-solver.box/2
            dd=np.einsum('...i,...i->...',delta,delta)
            weight=np.exp(-.5*dd/core**2)/(2*np.pi*core**2)**1.5
            w+=np.einsum('...s,si->...i',weight,ds[start:start+8])
    u=solver.velocity_from_vorticity(w)
    rms=np.sqrt(np.mean(np.sum(u*u,axis=-1)))
    if rms<1e-12:raise ValueError('degenerate flow')
    return u*target_rms/rms


def iso_scan(v,axes,percentiles=(65,75,85,92,96,98,99,99.5)):
    from a064.analysis import curl_div
    curl,div=curl_div(v,axes)
    scalar=np.sum(curl*curl,axis=-1)
    high=scalar[scalar>scalar.max()*1e-9]
    out=[]
    for pct in percentiles:
        level=float(np.percentile(high,pct))
        try:
            vts,fs,_,_=marching_cubes(scalar.astype('float32'),level=level,spacing=tuple(np.diff(a).mean() for a in axes))
            vts+=np.array([a[0] for a in axes])
            comps=closed_components(vts,fs)
            topology=[]
            for c in comps[:8]:
                chi=int(c.euler_number)
                topology.append({'genus':int((2-chi)//2) if chi<=2 and (2-chi)%2==0 else None,
                                 'euler_characteristic':chi,'faces':len(c.faces),'volume':float(abs(c.volume)),
                                 'area':float(c.area),'centroid':np.asarray(c.centroid).tolist()})
            out.append({'percentile':pct,'level':level,'active_fraction':float(np.mean(scalar>=level)),
                        'watertight_components':len(comps),'component_topology':topology})
        except (RuntimeError,ValueError):out.append({'percentile':pct,'level':level,'error':'NO_MARCHING_CUBES'})
    return out


def first_genus_one_feature(scalar,axes,curves,percentiles=(65,75,85,92,96,98,99,99.5)):
    """First CLOSED genus-one isosurface.  May be a global envelope, NOT a vortex tube."""
    high=scalar[scalar>scalar.max()*1e-9]
    for pct in percentiles:
        level=float(np.percentile(high,pct))
        try:
            verts,faces,_,_=marching_cubes(scalar.astype('float32'),level=level,
                        spacing=tuple(np.diff(a).mean() for a in axes))
            verts+=np.array([a[0] for a in axes])
            comps=closed_components(verts,faces)
        except (ValueError,RuntimeError):continue
        for c in comps:
            if int(c.euler_number)!=0:continue
            mesh_verts=np.asarray(c.vertices,float)
            d=np.stack([cKDTree(k).query(mesh_verts)[0] for k in curves],axis=1)
            ownership=[float(np.mean(d.argmin(axis=1)==i)) for i in range(3)]
            info={'level':level,'percentile':pct,'faces':len(c.faces),
                  'area':float(c.area),'volume':float(abs(c.volume)),
                  'surface_nearest_core_vertex_fraction':ownership,
                  'single_core_proximity_gate':bool(max(ownership)>=.90),
                  'three_separate_toroidal_components_gate':'UNRESOLVED_NOT_ESTABLISHED'}
            return {'vertices':mesh_verts,'faces':np.asarray(c.faces,int),**info}
    return None


def neighbor_label(points,curves,margin=.14,box=2*np.pi):
    p=np.asarray(points)
    wrap=lambda a:np.mod(np.asarray(a)+box/2,box)
    ds=np.stack([cKDTree(wrap(c),boxsize=box).query(wrap(p))[0] for c in curves],axis=1)
    ids=ds.argmin(axis=1)
    ambiguity=np.sort(ds,axis=1)[:,1]-np.sort(ds,axis=1)[:,0]
    return ids,ambiguity>margin,ds.min(axis=1)


def exchange_probe(flow,curves,t0,t1,offset=.27,seeds_per_component=64):
    """Moving-centerline nearest-core assignment control; NOT a material-separatrix proof."""
    samples=[];labels=[]
    for i,c in enumerate(curves):
        idx=np.linspace(0,len(c)-1,seeds_per_component,endpoint=False,dtype=int)
        p=c[idx]
        tang=np.roll(c,-2,axis=0)[idx]-np.roll(c,2,axis=0)[idx]
        tnorm=tang/np.maximum(np.linalg.norm(tang,axis=1)[:,None],1e-9)
        basis=np.tile([0.,0.,1.],(len(idx),1))
        parallel=np.abs(np.sum(basis*tnorm,axis=1))>.8
        basis[parallel]=[0,1,0]
        norm=np.cross(tnorm,basis)
        norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-9)
        samples.append(p+offset*norm); labels.extend([i]*len(idx))
    start=np.concatenate(samples);labels=np.array(labels)
    # First reject seeds not actually owned by intended component.
    initial,good_initial,_=neighbor_label(start,curves)
    valid=(initial==labels)&good_initial
    end=rk4(flow,start,t0,t1,48)
    end_curves=[rk4(flow,c,t0,t1,48) for c in curves]
    last,good_end,_=neighbor_label(end,end_curves)
    valid &=good_end & np.isfinite(end).all(axis=1)
    exchange=int(np.sum((last!=labels)&valid))
    return {'method':'nearest_advected_kinematic_centerline_neighborhood_screen',
            'seeds_total':len(labels),'seeds_valid':int(valid.sum()),'changed_ownership':exchange,
            'fraction_changed':float(exchange/valid.sum()) if valid.any() else None,
            'classification':'PROVISIONAL_FEATURE_NEIGHBORHOOD_NOT_MATERIAL_SEPARATRIX'}


def create_reference_baseline(ellpts=180):
    # Positive linked-arrangement control, but each component is unknotted.
    return [borromean_ellipse(j,np.linspace(0,2*np.pi,ellpts,endpoint=False)) for j in range(3)]


def input_hashes(curves):
    return [hashlib.sha256(np.ascontiguousarray(c,dtype='<f8').tobytes()).hexdigest() for c in curves]


def run_case(case,n=24,duration=.32,frames=13,core=.42,force=False,out=None):
    """Build model NPZ from either decorated Borromean ellipses or unknotted baseline."""
    assert case in (*CASES,'base_L6a4')
    out=Path(out) if out is not None else ROOT/'outputs'/f'{case}_N{n}'
    out.mkdir(parents=True,exist_ok=True)
    geometry_dir=out/'geometry';geometry_dir.mkdir(exist_ok=True)
    if case=='base_L6a4':
        curves=create_reference_baseline();provenance=[{'component':j,'knot_label':'0_1','construction':'parametric_Borromean_ellipse'} for j in range(3)]
    else:curves,provenance=create_link(case)
    topology=topology_audit(curves)
    for i,c in enumerate(curves):
        np.savetxt(geometry_dir/f'component_{i}_{provenance[i]["knot_label"]}.xyz',c,fmt='%.14g')
    expected=[{'5_2':7,'6_1':9,'0_1':1}[m['knot_label']] for m in provenance]
    actual=topology['component_knot_determinant_multiview']
    topology['strict_brunnian']=('REFERENCE_BRUNNIAN_BASELINE_UNCERTIFIED_TRIPLE_INVARIANT' if case=='base_L6a4' else 'IMPOSSIBLE_LOCALLY_KNOTTED_COMPONENTS')
    topology['component_determinant_expected']=expected
    topology['component_determinant_screen_pass']=all(all(v==e for v in triple) for triple,e in zip(actual,expected))
    topology.update({'component_sources':provenance,'geometry_sha256':input_hashes(curves),'case':case,
                     'e011_l6a4_status':'STATIC_NOT_READY_E010_EXCLUDED',
                     'e011_component_provider_status':'RAW_NATIVE_NOT_MAPPED_TO_ANCHORS'})
    (out/'GEOMETRY_TOPOLOGY_AUDIT.json').write_text(json.dumps(topology,indent=2,allow_nan=False)+'\n')
    if not topology['component_determinant_screen_pass'] or not topology['pairwise_lk_zero_screen'] or not topology['pairwise_min_separation_screen']:
        raise RuntimeError('Three-core topology SCREEN failed: geometry unsafe')
    cfg={'grid':n,'duration':duration,'frames':frames,'core':core,'case':case,'source_geometry_sha256':topology['geometry_sha256']}
    src=out/'THREE_CORE_EULER_MODEL.npz';side=out/'THREE_CORE_EULER_MODEL.source.json'
    if src.exists() and side.exists() and not force:
        meta=json.loads(side.read_text())
        if meta.get('npz_sha256')!=file_hash(src) or meta.get('build_cfg')!=cfg:
            raise RuntimeError('NPZ provenance mismatch. Use --force to explicitly rebuild.')
        diag=meta['euler_diagnostics']
    else:
        solver=SpectralEuler3D(n)
        u=init_three_core(solver,curves,core=core)
        t,v,diag=evolve(solver,u,duration=duration,frame_count=frames,cfl_limit=.14)
        ax=(np.arange(n)-n//2)*solver.dx
        np.savez_compressed(src,x=ax,y=ax,z=ax,t=t,v=v,source_type=np.array(CLASS),
          construction_class=np.array('locally_knotted_Borromean_skeleton'),
          coordinate_calibration=np.array('ARBITRARY_REFERENCE_1M_1S_NOT_PHYSICAL_SST'))
        meta={'schema':'A064-THREECORE-EULER-v1','source_type':CLASS,'science_tier':'SIMULATED_INITIAL_VALUE_PROTOTYPE',
              'npz_sha256':file_hash(src),'build_cfg':cfg,'euler_diagnostics':diag,
              'physical_claim':'NONE','geometry':'BORROMEAN_SKELETON_KNOT_DECORATED',
              'static_provider':'RAW_NATIVE_UNQUALIFIED','true_invariant_manifold_gate':'UNRESOLVED',
              'framework_v1_0_7_freeze':'NOT_EXECUTED',
              'warning':'Three local knots tied into parameterized Borromean ellipses; not strict Brunnian; SI units are arbitrary numeric aliases.'}
        side.write_text(json.dumps(meta,indent=2,allow_nan=False)+'\n')
    if side.is_file() and file_hash(src)!=json.loads(side.read_text())['npz_sha256']:
        raise RuntimeError('NPZ corrupted after creation')
    if diag['max_divergence']>=1e-8:raise RuntimeError('incompressibility screen failed')
    flow=PeriodicEulerFlow(src)
    # STAGE D: discover from t=0 ONLY. Do not compute transport before D seal is saved.
    v0,s0,d0=field_data(flow,flow.axes,float(flow.times[0]))
    scan=iso_scan(v0,flow.axes)
    screened=[]
    for c in scan:
        for s in c.get('component_topology',[]):
            if s['genus']==1:
                screened.append({'percentile':c['percentile'],'level':c['level'],'area':s['area'],'volume':s['volume']})
    genus1=first_genus_one_feature(s0,flow.axes,curves)
    genus1_info={k:v for k,v in genus1.items() if k not in ('vertices','faces')} if genus1 is not None else None
    mesh_path=out/'DISCOVERED_GENUS1_ISOSURFACE.npz'
    if genus1 is not None:
        np.savez_compressed(mesh_path,vertices=genus1['vertices'],faces=genus1['faces'],level=genus1['level'])
    elif mesh_path.exists():mesh_path.unlink()
    stage_d={'case':case,'geometry_hash':topology['geometry_sha256'],'input_npz_hash':file_hash(src),
             'discovery_time_index':0,'threshold_percentiles':[65,75,85,92,96,98,99,99.5],
             'candidate_classes':['global_enstrophy_envelopes','toroidal_genus_one_candidates'],
             'isolevel_scan':scan,'genus_one_candidates':screened,
             'selected_genus_one_feature':genus1_info,
             'candidate_assignment':'EXPLORATORY_ALL_PREREGISTERED_THRESHOLDS_NO_TRANSPORT_FEEDBACK',
             'invariant_manifold_gate':'UNRESOLVED_NOT_EXTRACTED'}
    (out/'DISCOVERY_ONLY.json').write_text(json.dumps(stage_d,indent=2,allow_nan=False)+'\n')
    seal={'canonical_discovery_json_sha256':canonical_hash(stage_d),'npz_sha256':file_hash(src),
          'selected_genus_one_mesh_sha256':file_hash(mesh_path) if mesh_path.exists() else None,
          'transport_audit_not_yet_computed_at_seal_write':True,'formal_blind_certification':'NOT_EXECUTED'}
    (out/'DISCOVERY_SEAL.json').write_text(json.dumps(seal,indent=2,allow_nan=False)+'\n')
    # STAGE T AFTER SEAL - independent flow trajectory integration.
    from a064.analysis import run as original_a064_run
    results=original_a064_run(flow,flow.axes,float(flow.times[0]),float(flow.times[-1]),
                out/'original_A064_envelope_control','THREE_CORE_SIMULATION_MODEL',meta,skip_stagnation=True)
    # Completely independent examination of a D-selected genus-one feature.
    torus_transport={'status':'NO_GENUS_ONE_FEATURE_DISCOVERED'}
    if genus1 is not None:
        _,s1,_=field_data(flow,flow.axes,float(flow.times[-1]))
        _,s_next,_=field_data(flow,flow.axes,float(flow.times[1]))
        torus_transport=transport_audit(flow,flow.axes,genus1,s0,s1,float(flow.times[0]),
                    float(flow.times[-1]),scalar_derivative=s_next,derivative_dt=float(flow.times[1]))
    exchange=exchange_probe(flow,curves,float(flow.times[0]),float(flow.times[-1]))
    status={
       'case':case,'source_npz_sha256':file_hash(src),
       'overall_science_gate':'UNRESOLVED_NOT_E011_PROVIDER_CERTIFIED',
       'genuine_separatrix_gate':'UNRESOLVED_NO_INVARIANT_MANIFOLD',
       'resolution_gate':'UNRESOLVED_NOT_CONVERGED','frame_count':int(frames),
       'temporal_evolution':'EVOLVED_PERIODIC_3D_EULER_MODEL','euler_diagnostics':diag,
       'geometry_topology':topology,
       'enstrophy_isosurface_screen':{'watertight_genus_one_n':len(screened),
          'genus_one_thresholds':sorted(set(i['percentile'] for i in screened)),
          'genus_one_selected':genus1_info,
          'three_individual_genus_one_components_observed':bool(any(sum(1 for c in line.get('component_topology',[]) if c['genus']==1)>=3 for line in scan)),
          'genus_one_material_transport':torus_transport,
          'outer_envelope_selected_by_prior_A064':results['candidate_detected'],
          'outer_envelope_transport':results['transport'],
          'scientific_interpretation':'FEATURE_SCREENING_ONLY_NO_PHYSICAL_TUBE_VALIDATION'},
       'three_core_exchange_probe':exchange,
       'note':'Neither an enstrophy-isosurface tracer crossing nor a nearest-core assignment change is proof of physical reconnection.',
       'discovery_sha256':seal['canonical_discovery_json_sha256'],
       'framework_freeze':'NOT_EXECUTED'}
    (out/'GATE_RESULTS.json').write_text(json.dumps(status,indent=2,allow_nan=False)+'\n')
    return status
