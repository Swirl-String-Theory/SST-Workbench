"""A065 v0.4.0 A003-authentic 48^3/64^3/96^3 + separate numerical Euler IVP.

Do not fit Gaussian a, circulation, length L, time T or profiles to the
holdout. The 384-record A003 validation is mandatory. Original A003 geometry
is NOT equivalent to a source-native PKLSA 3-D Euler vorticity trajectory.
"""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path
import numpy as np
from .native_core_v038 import gaussian_vorticity,spectral_helmholtz,cross_sections
from .euler3d_v040 import integrate,taylor_green
from .a003_v039 import adapter_root,atlas_root,_load_original_adapter,_screen_geometry,SourceIntegrityError

PIN='f63242516db654c2ecfeb2d45744d68c7438ca5c7fa48cdf0ec1822a8afa9437'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as f:json.dump(data,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')

def preflight(root):
    root=Path(root);p=root/'preregistration'/'VOLUME_EULER_V040.json'
    if sha(p)!=PIN:raise SourceIntegrityError('V040_PREREGISTRATION_CHANGED')
    c=json.loads(p.read_text(encoding='utf-8'))
    if c['schema']!='A065-VOLUME-EULER-PREREG-1' or c['grids']!=[48,64,96] or c['gaussian_a_assumed']!=0.55:
        raise SourceIntegrityError('V040_UNEXPECTED_CONTRACT')
    return c,sha(p)

def truth_on_grid(a,target):
    """Diagnostic trigonometric bandlimited prolongation, not new data.
    scipy.signal.resample preserves physical amplitude and performs Fourier
    zero padding, including correct real-Nyquist treatment per axis.
    """
    for ax in range(a.ndim-3,a.ndim):
        old=a.shape[ax]
        if old==target:continue
        if target<old:raise ValueError('FOURIER_DOWNSAMPLING_NOT_ALLOWED')
        f=np.fft.rfft(a,axis=ax)
        shape=list(f.shape);shape[ax]=target//2+1
        F=np.zeros(shape,dtype=np.complex128)
        sl=[slice(None)]*F.ndim;sl[ax]=slice(0,old//2+1)
        F[tuple(sl)]=f
        if old%2==0:
            ny=[slice(None)]*F.ndim;ny[ax]=old//2
            # Original even-grid Nyquist splits across ± frequencies.
            F[tuple(ny)]*=.5
        a=np.fft.irfft(F,n=target,axis=ax)*(target/old)
    return np.asarray(a,dtype=np.float64)

def relerr(a,b):
    return float(np.linalg.norm((a-b).ravel())/max(np.linalg.norm(b.ravel()),1e-25))

def selected_sources(root,c):
    path=adapter_root(root)
    if path is None:return None,'A003_ADAPTER_MISSING'
    adapter=_load_original_adapter(path)
    ar=atlas_root(root,path)
    if ar is None:return None,'A003_ATLAS_MISSING'
    registry,report=adapter.validate_atlas(ar,diagram=False)
    if registry['atlas_manifest_sha256']!=c['atlas_manifest_sha256'] or report['status']!='GEOMETRIC_IMPORT_QUALIFIED' or report['source_records']!=384:
        raise SourceIntegrityError('A003_ATLAS_VALIDATION_FAILED')
    rows={(r['id'],r['sampling'],r['points']):r for r in registry['records']}
    results={}
    for sid in c['seeds']:
        key=(sid,c['sampling'],c['source_resolution'])
        if key not in rows:raise SourceIntegrityError('A003_SOURCE_NOT_FOUND:'+sid)
        x=_screen_geometry(adapter,ar,registry,rows[key],{'source_resolution':c['source_resolution']})
        results[sid]={'xyz':x['xyz'][::c['stride']].copy(),'sha256':x['source_sha256'], 'length':x['polyline_length'],'source_file':x['source_file']}
    return results,None

def numerical_control(c):
    # A genuinely independent analytic Euler IVP initialization, unrelated to A003.
    # This is solver-validation-only, not corroborating PKLSA physical origin.
    u0=taylor_green(c['control_grid'])
    main=integrate(u0,2*np.pi,c['euler_T'],c['euler_steps'])
    finer=integrate(u0,2*np.pi,c['euler_T'],2*c['euler_steps'])
    return {'initial_condition':'TAYLOR_GREEN_PERIODIC_ANALYTIC','grid_n':c['control_grid'],
            'audit':main['audit'],'temporal_u_relative':relerr(main['u'],finer['u']),
            'outcome':'PASS' if main['audit']['div_u_rms']<c['div_tol'] and main['audit']['relative_energy_drift']<c['energy_tol'] and relerr(main['u'],finer['u'])<c['temporal_tol'] else 'FAIL',
            'provider_status':'NUMERICAL_EULER_SOLVER_CONTROL_ONLY'}

def run(root,*,persist=True,requested='ALL',synthetic_debug=False):
    root=Path(root);c,ph=preflight(root)
    selected,missing=selected_sources(root,c)
    control=numerical_control(c)
    results={'schema':'A065-VOLUME-EULER-RESULT-1','release':'v0.4.0',
      'prereg_sha256':ph,'status':'EXECUTED' if selected else 'PARTIAL_MISSING_A003_INPUT',
      'geometries':{},'source_missing':missing,'periodic_euler_solver_control':control,
      'physical_euler_provider_qualified':False,'pklsa_time_evolution_qualified':False,
      'independent_physical_holdout':False,'no_fitted_parameters':True,
      'gates':{},'source_class':'GEOMETRY_SEEDED_GAUSSIAN_EULER_IVP_DIAGNOSTIC_ONLY'}
    if missing:
        results['gates']={'G37':'NOT_RUN_PREREQUISITE','G38':'NOT_RUN_PREREQUISITE',
                 'G39':'PASS' if control['outcome']=='PASS' else 'FAIL',
                 'G40':'NOT_RUN_PREREQUISITE','G41':'UNRESOLVED','G42':'NOT_RUN_PREREQUISITE'}
        if persist:write(root/'outputs'/'VOLUME_EULER_V040_RESULT.json',results)
        return results
    section_c=json.loads((root/'preregistration'/'SOURCE_NATIVE_CORE_V038.json').read_text('utf8'))
    save_fields=os.getenv('A065_V040_SAVE_FIELDS','0')=='1'
    for sid,source in selected.items():
        records=[];field_cache={};euler_cache={}
        for n in c['grids']:
            nodes=source['xyz'];L=c['box_length']
            omega=gaussian_vorticity(nodes,n,L,c['gaussian_a_assumed'],c['gamma_assumed'])
            flow=spectral_helmholtz(omega,L,c['density'])
            sections=cross_sections(flow['omega'],flow['u'],flow['grad_p'],nodes,L,section_c)
            accepted=[r for r in sections if r['section_admissible']]
            evo=integrate(flow['u'],L,c['euler_T'],c['euler_steps'],c['density'])
            ed=evo['audit']
            row={'n':n,'dx':L/n,'source_sha256':source['sha256'],'section_admitted_count':len(accepted),
                'section_rejections':len(sections)-len(accepted),
                'section_gamma':[s['Gamma_cross_section'] for s in sections],
                'section_Z':[s['Z_axial'] for s in sections],
                'section_width':[s['a_Gamma_Z_gaussian_assumption'] for s in sections],
                'heldout_velocity_relative':[s['heldout_velocity_rms_relative'] for s in accepted],
                'heldout_pressure_relative':[s['heldout_radial_pressure_gradient_rms_relative'] for s in accepted],
                'source_projection_relative_error':flow['projection_relative_error'],
                'source_steady_euler_residual_relative':flow['steady_euler_residual_relative'],
                'euler':ed}
            if persist and save_fields:
                dst=root/'outputs'/f'V040_{sid}_N{n}_EULER.npz'
                dst.parent.mkdir(parents=True,exist_ok=True)
                np.savez_compressed(dst,u0=flow['u'],omega0=flow['omega'],p0=flow['p'],
                        u=evo['u'],omega=evo['omega'],p=evo['p'],
                        dx=np.float64(L/n),L=np.float64(L),time0=np.float64(0.),
                        time=np.float64(c['euler_T']),source_class=np.array('A003_GEOMETRY_GAUSSIAN_EULER_NUMERICAL_NOT_PKLSA'))
                row['field_path']=str(dst.relative_to(root)).replace('\\','/')
                row['field_sha256']=sha(dst)
            records.append(row)
            # Use bandlimited Fourier prolongation ONLY for comparison, NOT source generation.
            field_cache[n]={'u':flow['u'],'p':flow['p'],'omega':flow['omega']}
            euler_cache[n]={'u':evo['u'],'omega':evo['omega'],'p':evo['p']}
        pairs=[]
        for low,hi in zip(c['grids'],c['grids'][1:]):
            source_errors={key:relerr(truth_on_grid(field_cache[low][key],hi),field_cache[hi][key]) for key in ('u','p','omega')}
            euler_errors={key:relerr(truth_on_grid(euler_cache[low][key],hi),euler_cache[hi][key]) for key in ('u','p','omega')}
            pairs.append({'grids':[low,hi],'source_field_relative':source_errors,'euler_field_relative':euler_errors})
        vgood=all(all(v<c['volume_tol'] for v in p['source_field_relative'].values()) for p in pairs)
        egood=all(r['euler']['div_u_rms']<c['div_tol'] and r['euler']['relative_energy_drift']<c['energy_tol'] for r in records)
        pg=all(all(v<c['pressure_tol'] for v in [p['source_field_relative']['p'],p['euler_field_relative']['p']]) for p in pairs)
        results['geometries'][sid]={'geometry_file':source['source_file'],'geometry_sha256':source['sha256'],
          'polyline_length':source['length'],'source_nodes':len(source['xyz']),
          'assumed_gaussian_a_NOT_INFERRED':c['gaussian_a_assumed'],
          'fixed_gamma':c['gamma_assumed'],'fixed_box_length':c['box_length'],
          'records':records,'grid_pairs':pairs,
          'volume_pass':vgood,'euler_numerics_pass':egood,'pressure_grid_pass':pg}
        del field_cache,euler_cache
    goodv=all(x['volume_pass'] for x in results['geometries'].values())
    goode=all(x['euler_numerics_pass'] for x in results['geometries'].values())
    goodp=all(x['pressure_grid_pass'] for x in results['geometries'].values())
    results['gates']={'G37':'PASS','G38':'PASS' if goodv else 'FAIL',
       'G39':'PASS' if control['outcome']=='PASS' else 'FAIL',
       'G40':'PASS' if goode else 'FAIL',
       'G41':'UNRESOLVED',
       'G42':'PASS' if goodp else 'FAIL'}
    if persist:write(root/'outputs'/'VOLUME_EULER_V040_RESULT.json',results)
    return results
