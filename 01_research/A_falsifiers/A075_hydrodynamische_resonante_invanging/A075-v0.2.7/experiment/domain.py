"""Adversarial finite periodic-box sensitivity, NOT an open-boundary/free-space Euler solver.

A matched physical dx and Gaussian core are imposed. Distinct box sizes change
periodic-image interactions. A converged box sequence can bound sensitivity,
not prove zero image error or post-exit capture.
"""
from __future__ import annotations
import dataclasses
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from .euler3d import Config,run_paired,Euler3D

VALID_GRIDS=tuple(range(16,513,8))

def parse_domains(spec,base_n,base_box=10.0):
    if spec:
        arr=[]
        for token in spec.split(','):
            parts=token.strip().split(':')
            if len(parts)!=2:raise ValueError('DOMAIN_FORMAT: use L:N,L:N,L:N, e.g. 10:80,15:120,20:160')
            L=float(parts[0]);n=int(parts[1]);arr.append({'box':L,'grid':n})
    else:
        arr=[{'box':float(base_box)*m,'grid':int(base_n*m)} for m in (1,1.5,2)]
    if len(arr)<3:raise ValueError('DOMAIN_THREE_LEVELS_REQUIRED')
    if any(not np.isfinite(z['box']) or z['box']<=0 or z['grid'] not in VALID_GRIDS for z in arr):
        raise ValueError('DOMAIN_INVALID_POSITIVE_BOX_OR_GRID; multiples of 8, 16..512 required')
    if any(arr[i]['box']>=arr[i+1]['box'] for i in range(len(arr)-1)):
        raise ValueError('DOMAIN_BOX_SIZES_MUST_INCREASE')
    dx=arr[0]['box']/arr[0]['grid']
    if any(abs(z['box']/z['grid']-dx)>1.e-11*max(1,dx) for z in arr):
        raise ValueError('DOMAIN_FIXED_DX_VIOLATION: keep physical cell width L/N invariant across boxes')
    return [{**z,'dx':dx} for z in arr]


def domain_budget(boxes,p):
    # An auditable conservative work proxy: for each knot, 2 Euler fields,
    # paired 4-stage RK plus diagnostics; max RAM based on largest box.
    nmax=max(z['grid'] for z in boxes)
    peak_gib=30*3*16*nmax**3/(2**30)
    work=int(sum(z['grid']**3 for z in boxes)*len(p['knots'])*max(1,int(np.ceil(p['T']/p['dt'])))*8)
    reasons=[]
    if peak_gib>p['max_ram_gb']: reasons.append('DOMAIN_MEMORY_BUDGET_EXCEEDED')
    if work>1_500_000_000 and not p.get('allow_expensive'):reasons.append('DOMAIN_EXPENSIVE_REQUIRE_ALLOW_EXPENSIVE')
    return {'peak_memory_GiB_proxy':round(peak_gib,3),'work_proxy':work,
            'approved':not reasons,'block_reasons':reasons,
            'warning':'RSS is solver dependent; the estimate is a conservative rough upper proxy, not measured RAM.'}


def _face_fraction(solver,uh):
    """Enstrophy fraction within one sigma of any periodic face. Diagnostic only."""
    om=solver.ifft(solver.curl_hat(uh))
    q=np.sum(om*om,axis=-1)
    slab=max(solver.c.core,2*solver.dx)
    coords=solver.X
    near=np.zeros_like(q,dtype=bool)
    for coord in coords:
        near |= np.abs(coord)>=solver.c.box/2-slab
    denom=max(float(q.sum()),1e-30)
    return {'boundary_enstrophy_fraction':float(q[near].sum()/denom),
            'boundary_enstrophy_max':float(q[near].max()) if np.any(near) else 0.,
            'shell_width':slab,'meaning':'Periodic-face proximity proxy; not a proof donor did or did not return'}


def run_domain_study(root,profile,out,p):
    """Run the matched-domain paired source/control at three or more periodic boxes.

    Do not reuse the memory-heavy intermediate solutions across boxes; build
    separate operators and enforce identical physical endpoint and source geometry.
    """
    from .science import save,comparison,write_steps
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    boxes=parse_domains(p.get('domains'),p['n'])
    b=domain_budget(boxes,p)
    pre={'schema':'A075-DOMAIN-PREFLIGHT-1','status':'PLANNED','box_geometry':boxes,
         'physical_core_sigma':p['core'],'same_absolute_T':p['T'],
         'same_dt_max':p['dt'],'same_cfl_limits':True,'budget':b,
         'boundary_condition':'TRIPLY_PERIODIC_FOURIER_NOT_FREE_SPACE',
         'source_motion_qualification':'NOT_PROVEN','free_space_euler_provider':False}
    save(out/'DOMAIN_PREFLIGHT.json',pre)
    if not b['approved']:raise RuntimeError('DOMAIN_STUDY_BUDGET_REFUSED: '+','.join(b['block_reasons']))
    if p['backend'] not in ('cpu-scipy-fft','cpu-numpy-reference','cpp-hybrid'):
        raise RuntimeError('DOMAIN_STUDY_BACKEND_NOT_VALIDATED: use Python or hybrid C++; run XPU independently')
    matrix={'schema':'A075-DOMAIN-SENSITIVITY-1','profile':profile,
        'boundary_model':'PERIODIC_IMAGES_PRESENT_AT_ALL_BOX_SIZES',
        'physical_answer':'UNRESOLVED','physical_free_space_pass':False,
        'executed':False,'boxes':boxes,'knots':{},'qualified_donor_exit':False,
        'qualified_receiver_cycles':False,
        'fixed_physical_dx':boxes[0]['dx'],'fixed_core_sigma':p['core'],
        'fixed_absolute_final_time':p['T'],'backend':p['backend'],
        'tolerance_last_two_box_difference':0.03,
        'note':'Box-size sensitivity in a periodic solver is not a non-periodic/open-boundary certification'}
    # Source code and explicit test input provenance, preserved with the science outputs.
    src_paths=[root/'experiment/domain.py',root/'experiment/euler3d.py',root/'experiment/science.py']
    matrix['source_sha256']={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in src_paths}
    for knot_idx,knot in enumerate(p['knots']):
        levels=[];reason=None
        for box_idx,z in enumerate(boxes):
            from .heartbeat import phase
            phase('domain_sensitivity',backend=p['backend'],knot=knot,grid=z['grid'],phase_index=knot_idx*len(boxes)+box_idx+1,phase_total=len(p['knots'])*len(boxes),
                 physical_end_time=p['T'],message=f"Periodic box L={z['box']}, not free space")
            n,L=z['grid'],z['box'];tag=f'{knot}_L{L:g}_N{n}'
            cfg=Config(n=n,box=L,core=p['core'],dt=p['dt'],final_time=p['T'],
                geometry=knot,xyz_root=str(root/'inputs'),threads=p['threads'],backend=p['backend'],
                adaptive=p['adaptive'],cfl_target=p['cfl_target'],max_core_shift=p['max_core_shift'],
                max_vorticity_turn=p['max_vorticity_turn'],dt_min=p['dt_min'],
                steps_per_diagnostic=p['diagnostic_stride'],gpu_precision=p['gpu_precision'])
            try:
                src,ref,steps=run_paired(cfg)
                # The diagnostic does NOT imply actual free-space propagation.
                initial_donor=Euler3D(dataclasses.replace(cfg,receiver_on=False,backend='cpu-scipy-fft'))
                dh,_=initial_donor.initial_velocity()
                donor_energy=initial_donor.global_energy_hat(dh)
                capture=comparison(src,ref,donor_energy)
                # Final periodic-boundary proximity is measured on source field
                # with a separate exactly matched T, not a heuristic ring track.
                # Avoid replay by calculating approximate face metric on first/last
                # diagnostic source fields: dynamic field unavailable here; record
                # the independently reproducible initial full-source indicator.
                full_start=Euler3D(dataclasses.replace(cfg,backend='cpu-scipy-fft'))
                sh,_=full_start.initial_velocity()
                faces=_face_fraction(full_start,sh)
                item={'box':L,'grid':n,'dx':z['dx'],'core_sigma_cells':p['core']/z['dx'],
                    'fixed_T':p['T'],'dt_max':p['dt'],'backend':p['backend'],
                    'global_energy_relative_drift':max(src['global_relative_energy_drift'],ref['global_relative_energy_drift']),
                    'max_flux_residual_over_initial_E':max(src['max_window_budget_residual_over_E0'],ref['max_window_budget_residual_over_E0']),
                    'window_excess_final_J':capture['window_excess_final_J'],
                    'late_min_excess_over_donor_E':capture['tail_min_excess_over_donor_E'],
                    'window_excess_final_over_donor_E':capture['window_excess_final_J']/max(donor_energy,1e-18),
                    'donor_initial_energy_J':donor_energy,'steps':len(steps),
                    'periodic_faces_at_initial_state':faces,
                    'donor_exit_confirmed':False,'receiver_clock_qualified':False,
                    'physical_status':'DIAGNOSTIC_ONLY_PERIODIC'}
                save(out/(tag+'.json'),item)
                write_steps(out/(tag+'_step_energy.csv'),steps)
                levels.append(item)
            except FileNotFoundError as exc:
                reason='MISSING_GENUINE_XYZ: '+str(exc);break
            except Exception as exc:
                reason=f'{type(exc).__name__}: {exc}';break
        if reason:
            matrix['knots'][knot]={'execution':'BLOCKED_OR_FAILED','reason':reason,'completed_levels':levels}
            continue
        norm=[v['window_excess_final_over_donor_E'] for v in levels]
        diffs=[abs(norm[i+1]-norm[i]) for i in range(len(norm)-1)]
        # Diagnostic screen: not box convergence certificate, not a material boundary.
        matrix['knots'][knot]={'execution':'EXECUTED','completed_levels':levels,
            'normalized_observables':norm,'adjacent_box_abs_differences':diffs,
            'last_pair_difference':diffs[-1],
            'periodic_box_sensitivity_screen':bool(diffs[-1]<matrix['tolerance_last_two_box_difference']),
            'status':'PERIODIC_BOX_DIAGNOSTIC_NO_FREE_SPACE_PASS'}
        save(out/'DOMAIN_MATRIX.json',matrix)
    matrix['executed']=all(z['execution']=='EXECUTED' for z in matrix['knots'].values())
    save(out/'DOMAIN_MATRIX.json',matrix)
    return matrix
