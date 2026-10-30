"""A077 v0.1.1 scientific diagnostics: reduced ring ring dynamics and optional Euler field.

G5: verified *local* pybind numerical gate, independent of physical-source G4.
G10: framework-post-backend independent numerical 2-of-3 control.
Neither proves electron spin, discrete energy spectra, or full continuum Euler.
"""
from __future__ import annotations
import csv,hashlib,json
from pathlib import Path
import numpy as np
from science.diagnostics import detailed_run,dump_trace,compare_refinements
from science.ring_model import circulation
from sst_falsifier import progress


def _hash(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def _inputs(c,scenario):
    s=c['initial_conditions_dimensionless'][scenario]
    return np.column_stack((s['radii'],s['z'])).ravel(),np.asarray(s['gamma_signs'],float),np.asarray(s['radii'],float)*c['core_ratio']

def _native_ring_trajectory(values, expected_shape):
    """Reshape C++ ring_integrate's flat, time-major vector; reject corrupt data.

    The native ABI returns (steps + 1) * (2 * rings) doubles, flattened in
    chronological time-major order. Python reference returns (steps + 1, 2*rings).
    This is an interface conversion, not a change to the scientific algorithm.
    """
    arr = np.asarray(values, dtype=np.float64)
    expected_size = int(np.prod(expected_shape))
    if arr.ndim != 1 or arr.size != expected_size:
        raise ValueError(
            f"native ring_integrate output shape {arr.shape} is invalid; "
            f"expected flat vector of length {expected_size}"
        )
    if not np.isfinite(arr).all():
        raise ValueError("native ring_integrate returned nonfinite values")
    return arr.reshape(expected_shape)


def run_scientific_pipeline(root,cfg,ledger,mode):
    root=Path(root);c=json.loads((root/'configs'/'pilot.json').read_text(encoding='utf8'))
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"/'science_diagnostics'
    out.mkdir(parents=True,exist_ok=True)
    ledger.record('G0','PASS',metrics={'mode':mode},reason='Framework frozen protocol and embedded runtime verified before science.')
    src=root/'configs'/'pilot.json'
    results={'schema':'A077-REDUCED-RING-DIAGNOSTICS-2','scope':'REGULARIZED_FILAMENT_PROXY_ONLY',
             'mode':mode,'config_sha256':_hash(src),'cases':{},'refinements':{},
             'physical_spin_claim':'UNRESOLVED','full_euler_claim':'UNRESOLVED'}
    Gamma0=circulation(c['reference_scale']['radius_m'],c['reference_scale']['speed_m_s'])
    R0=c['reference_scale']['radius_m'];t0=R0*R0/Gamma0
    for name in ('single','same','opposite','reverse'):
        y,g,a=_inputs(c,name)
        sim,stat,clearance=detailed_run(y,g,a,tf=c['normalized_time_end'],steps=c['pilot_steps'],
                                        ntheta=c['angular_quadrature'],self_constant=c['self_induction_constant'])
        p=dump_trace(out/f'{name}_full_trajectory.csv',sim['t'],sim['y'],sim['a2R'],clearance,t0,R0)
        results['cases'][name]={'stats':stat,'trajectory_sha256':_hash(p),
                               'saved_samples':len(sim['t'])}
    # Scientific plot is a derived result artifact; frozen protocol text remains unchanged.
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from pathlib import Path as _Path
        fig,ax=plt.subplots(figsize=(8.2,3.3))
        curve=np.loadtxt(out/'same_full_trajectory.csv',delimiter=',',skiprows=1)
        tx=curve[:,1]
        # CSV schema: step,t,t_SI,R0,z0,a0,R0_SI,z0_SI,R1,z1,...
        ax.plot(tx,curve[:,9]-curve[:,4],linewidth=1.55,label=r'$\Delta z/R_0$')
        ax.axhline(0,color='black',linewidth=.75)
        for evt in results['cases']['same']['stats']['events']:
            ax.axvline(evt['t'],alpha=.28,linewidth=.9)
        ax.set(xlabel=r'$t/t_0$',ylabel=r'$(z_2-z_1)/R_0$',title='A077-v0.1.1: classical axial ring-order swaps (proxy)')
        ax.grid(alpha=.22);fig.tight_layout()
        report_dir=out.parent/'report';report_dir.mkdir(exist_ok=True)
        fig.savefig(report_dir/'ring_traces.pdf');plt.close(fig)
        results['figure_path']='report/ring_traces.pdf'
    except ImportError:
        results['figure_path']=None
    y,g,a=_inputs(c,'same')
    with progress.refinement('spatial',level=1,total=1,resolution=c['refinement_v011']['angular_quadrature'][-1]):
        spatial_scans=compare_refinements(c,'same',axis_filter='angular')
    with progress.refinement('temporal',level=1,total=1,dt=c['normalized_time_end']/c['refinement_v011']['temporal_steps'][-1],final_time=c['normalized_time_end']):
        temporal_scans=compare_refinements(c,'same',axis_filter='temporal')
    scans=spatial_scans+temporal_scans
    results['refinements']={v['axis']:v for v in scans}
    (out/'refinement.json').write_text(json.dumps(results['refinements'],indent=2)+'\n')
    s=scans[0]['levels'];t=scans[1]['levels']
    ang_err=float(s[-2]['relative_endpoint_delta_to_next']);time_err=float(t[-2]['relative_endpoint_delta_to_next'])
    ang_shift=s[-2]['max_event_shift_to_next'];time_shift=t[-2]['max_event_shift_to_next']
    ngood=all(len(x['events'])==len(s[0]['events']) for x in s+t)
    events_good=ngood and ang_shift is not None and time_shift is not None and ang_shift<=c['refinement_v011']['max_event_time_shift'] and time_shift<=c['refinement_v011']['max_event_time_shift']
    numeric_good=(ang_err<c['spatial_relative_tolerance'] and time_err<c['temporal_relative_tolerance'] and events_good)
    min_clearance=min(x['stats']['minimum_surface_clearance'] for x in results['cases'].values() if x['stats']['minimum_centerline_separation'] is not None)
    coarse_clear=bool(results['cases']['same']['stats']['collision_free_sampled'])
    results['numeric_summary']={'angular_endpoint_l2_relative':ang_err,'temporal_endpoint_l2_relative':time_err,
       'max_angular_event_shift':ang_shift,'max_temporal_event_shift':time_shift,
       'event_counts_match':ngood,'same_case_crossing_count':results['cases']['same']['stats']['event_count'],
       'min_surface_clearance_dimensionless':min_clearance,'same_case_no_contact_sampled':coarse_clear,
       'reference_scale_R0_m':R0,'reference_scale_Gamma_m2_s':Gamma0,'reference_scale_t0_s':t0}
    (out/'scientific_diagnostics.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')

    def G1():
        return {'status':'PASS','reason':'Frozen analytic case definitions and source hashes; not independent empirical observations.',
                'metrics':{'config_sha256':_hash(src),'case_count':4}}
    def G2():
        return {'status':'PASS' if numeric_good else 'FAIL',
                'reason':'Separate angle-quadrature and ODE time-step convergence with event-root tests; no 3D Euler authority.',
                'metrics':results['numeric_summary']}
    def G5():
        try:
            from native_ext import _sst_native
            yy=np.asarray(y,dtype=float);kk=float(c['self_induction_constant']);steps=int(c['pilot_steps'])
            dt=float(c['normalized_time_end'])/steps
            if not Path(_sst_native.__file__).is_file():raise RuntimeError('no compiled pybind binary')
            from science.ring_model import trajectory
            ref=trajectory(yy,g,a,dt=dt,steps=steps,ntheta=c['angular_quadrature'],self_constant=kk)['y']
            alt=_native_ring_trajectory(
                _sst_native.ring_integrate(yy.tolist(),g.tolist(),a.tolist(),dt,steps,c['angular_quadrature'],kk),
                ref.shape,
            )
            rel=float(np.linalg.norm(alt-ref)/max(np.linalg.norm(ref),1e-30))
            return {'status':'PASS' if rel<=c['backend_parity_relative_tolerance'] else 'FAIL',
                    'reason':'Actually executed instance pybind11 C++ ring science kernel; numeric parity only.',
                    'metrics':{'relative_L2':rel,'binary_sha256':_hash(_sst_native.__file__),
                               'actual_backend':'pybind11','authority':'NUMERIC_DIAGNOSTIC'},
                    'actual_backend':'pybind11','authority':'NUMERIC_DIAGNOSTIC'}
        except (ImportError,ModuleNotFoundError,RuntimeError,OSError) as exc:
            return {'status':'UNRESOLVED','reason':f'Native source/backend not executable: {type(exc).__name__}: {exc}'}
    def unres(x):return lambda:{'status':'UNRESOLVED','reason':x}
    evals={'G1':G1,'G2':G2,
         'G3':unres('No held-out eigenvalue spectrum or discrete level detection, geometric rank swaps are classical.'),
         'G4':unres('No independent finite-core continuum Euler confirmation with space/time/core convergence.'),
         'G5':G5,
         'G6':unres('No executed GPU scientific kernel; Intel device probe is not science.'),
         'G7':unres('One analytic model family; time/mesh refinement is not source replication.'),
         'G8':unres('Independent toroidal/poloidal finite-width Euler pilot exists but is not continuum-certified; no spinor/field topology proof or experimental electron evidence.')}
    ledger.run_evaluators(evals)
    return {'schema':'SST-BACKEND-MANIFEST-2','model':'AXISYMMETRIC_REGULARIZED_FILAMENT_PROXY',
        'science_diagnostics':'science_diagnostics/scientific_diagnostics.json',
        'scientific_authority':'DEVELOPMENT_DIAGNOSTIC_ONLY',
        'note':'G5 local pybind check independent of G4. G10 validates multi-backend parity after execution. No physical spin/level pass.'}
