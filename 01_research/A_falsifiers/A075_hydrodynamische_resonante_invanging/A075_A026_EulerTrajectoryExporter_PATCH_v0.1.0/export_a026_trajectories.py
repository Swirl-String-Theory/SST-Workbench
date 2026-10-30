#!/usr/bin/env python3
"""Create independently-seeded 3-D periodic Euler material-tracer trajectories.

Additive adapter: imports existing A075 v0.2.9 euler3d rather than modifying it.
No claim of converged Euler physics, material vortex-core tracking or Swirl Clock.
"""
from __future__ import annotations
import argparse
import dataclasses
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone
import numpy as np

# Source bytes from the inspected connected A075-v0.2.9 tree, not from a guessed version.
PINNED = {
    'experiment/euler3d.py': 'e66cb8430d70e2738f6ddb2505d446c47b2a11cb71d9f6310ebbb2321748a063',
    'experiment/ruban.py': '6c402e8f9928556f3593447ef85f7874d23f472f21d689261a30bafa623642f6',
}
VERSION = 'v0.1.0'
CANON_RC_M = 1.40897017e-15
CANON_V_M_S = 1.09384563e6


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checksum_manifest(root):
    entries = {}
    for rel, expected in PINNED.items():
        f = root / rel
        if not f.is_file():
            raise FileNotFoundError(f'MISSING_A075_SOURCE: {f}')
        actual = sha(f)
        if actual != expected:
            raise RuntimeError(f'A075_SOURCE_DRIFT: {rel}\nexpected {expected}\nactual   {actual}\nUse exactly A075-v0.2.9 or prepare a reviewed NEW exporter version.')
        entries[rel] = actual
    return entries


def source_contract_sha(d):
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_solver(root):
    # Avoid accidental import from a different ambient A075 install.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    for m in ('experiment.euler3d', 'experiment.ruban'):
        if m in sys.modules:
            path = Path(getattr(sys.modules[m], '__file__', '')).resolve()
            if root not in path.parents:
                raise RuntimeError(f'WRONG_IMPORTED_MODULE: {m} at {path}')
    e = importlib.import_module('experiment.euler3d')
    rb = importlib.import_module('experiment.ruban')
    if root not in Path(e.__file__).resolve().parents or root not in Path(rb.__file__).resolve().parents:
        raise RuntimeError('IMPORT_PROVENANCE_MISMATCH')
    return e, rb


def seeded_perturbation(solver, uh, rng, fraction, length):
    """Different smooth, divergence-free Fourier velocity initial perturbations.
    This is NOT an explicitly initialized bundle of material vortex filaments.
    """
    if fraction == 0:
        return uh
    noise = rng.normal(size=(solver.c.n, solver.c.n, solver.c.n, 3))
    # Filter unresolved high-wavenumber noise before Leray projection.
    ph = solver.project(solver.fft(noise))
    ph *= np.exp(-0.5 * length**2 * solver.k2)[..., None]
    ph = solver.project(ph)
    # Scale in rms *velocity*, rather than raw Fourier coefficient units.
    norm_p = np.sqrt(np.sum(np.abs(ph)**2))
    norm_base = np.sqrt(np.sum(np.abs(uh)**2))
    if norm_p <= 0 or norm_base <= 0:
        raise RuntimeError('DEGENERATE_PERTURBATION')
    return solver.project(uh + fraction * (norm_base / norm_p) * ph)


def rk4_field_marker(s, uh, x_unwrapped, dt):
    """Shared four Euler RK stages and four tracer velocity stages.

    The marker is a LAGRANGIAN PASSIVE TRACER; its numerical accuracy
    is subject to interpolation/field/time convergence. Not vortex core centroid.
    """
    k1 = s.rhs(uh)
    a1 = s.probe_u(uh, x_unwrapped)
    h2 = s.project(uh + .5 * dt * k1)
    k2 = s.rhs(h2)
    a2 = s.probe_u(h2, x_unwrapped + .5 * dt * a1)
    h3 = s.project(uh + .5 * dt * k2)
    k3 = s.rhs(h3)
    a3 = s.probe_u(h3, x_unwrapped + .5 * dt * a2)
    h4 = s.project(uh + dt * k3)
    k4 = s.rhs(h4)
    a4 = s.probe_u(h4, x_unwrapped + dt * a3)
    new_uh = s.project(uh + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6)
    new_x = x_unwrapped + dt * (a1 + 2 * a2 + 2 * a3 + a4) / 6
    return new_uh, new_x


def initial_marker(e, rb, args, root):
    if args.mode == 'ruban':
        seed = root / 'inputs' / 'ruban_t23' / rb.PRIMARY
        coords, provenance = rb.load_primary_seed(seed)
        return np.asarray(coords[args.marker_index % len(coords)], dtype=float), provenance, sha(seed), sha(seed.parent / 'SEED_MANIFEST.json')
    if args.mode == 'legacy_t23':
        pts = rb.analytic_torus(.32, n=2048)
        x = np.asarray(pts[args.marker_index % len(pts)], dtype=float)
        desc = {'kind':'3_1','analytic_B0':'.32','seed_formula':'A075 experiment/ruban.py analytic_torus', 'marker_index':args.marker_index}
        return x, desc, source_contract_sha(desc), sha(root / 'experiment' / 'ruban.py')
    if args.mode == 'coupled_ring_trefoil':
        pts, prov = e.curve('3_1', 0.82, 0.65, xyz_root=str(root/'inputs'))
        desc = {'kind':'legacy_coupled_ring_plus_trefoil', 'curve_provenance':prov,'marker_index':args.marker_index}
        return np.asarray(pts[args.marker_index % len(pts)],dtype=float), desc, source_contract_sha(desc), sha(root/'experiment'/'euler3d.py')
    raise ValueError('unknown mode')


def one_trajectory(e, rb, args, root, seq, times, axis):
    cfg=e.Config(n=args.grid,box=args.box,core=args.sigma,rho=1.,gamma_receiver=2*np.pi,
                 gamma_donor=0.,dt=args.dt,final_time=float(times[-1]),geometry='3_1',
                 incoming=False,receiver_on=True,threads=args.threads,backend='cpu-scipy-fft',
                 adaptive=args.adaptive,cfl_target=args.cfl_target,
                 max_core_shift=args.max_core_shift,max_vorticity_turn=args.max_vorticity_turn,
                 max_steps=args.max_steps,dt_min=1.e-10,
                 initial_condition={'ruban':'ruban_isolated','legacy_t23':'legacy_t23_isolated',
                                    'coupled_ring_trefoil':'legacy_coupled'}[args.mode],
                 ruban_seed_path=str(root/'inputs'/'ruban_t23'/rb.PRIMARY))
    s=e.Euler3D(cfg)
    uh, initial_prov = s.initial_velocity()
    rng=np.random.default_rng(seq)
    uh=seeded_perturbation(s,uh,rng,args.perturbation,args.perturb_length)
    x0, marker_prov, geometry_hash, geom_manifest_hash=initial_marker(e,rb,args,root)
    x=x0.copy(); q=[]; v=[]; energies=[]; steps=0; rejections=0
    energy0=s.global_energy_hat(uh)
    t=0.0
    for end_t in times:
        tol=max(1e-13, 1e-11*max(float(end_t),1e-9))
        while end_t-t>tol:
            if steps >= args.max_steps:
                raise RuntimeError('MAX_STEPS_EXCEEDED')
            umax,omax=s.adapt_metrics(uh)
            dt=e.stable_dt(cfg,s.dx,umax,omax,end_t-t) if args.adaptive else min(cfg.dt,end_t-t)
            if dt <= 0 or not np.isfinite(dt):
                raise RuntimeError('INVALID_DT')
            attempts=0
            while True:
                new_uh, new_x=rk4_field_marker(s,uh,x,dt)
                up,op=s.adapt_metrics(new_uh)
                ucheck=max(umax,up);ocheck=max(omax,op)
                if (not args.adaptive or
                    (ucheck*dt/s.dx <= cfg.cfl_target*(1+1e-12) and
                     ucheck*dt/cfg.core <= cfg.max_core_shift*(1+1e-12) and
                     ocheck*dt <= cfg.max_vorticity_turn*(1+1e-12))):
                    break
                dt/=2;attempts+=1
                if attempts>12 or dt<cfg.dt_min:
                    raise RuntimeError('ADAPTIVE_STEP_REJECT_LIMIT')
            x=new_x;uh=new_uh;t+=dt;steps+=1;rejections+=attempts
        if abs(t-end_t)>tol:
            raise RuntimeError('SAMPLE_TIME_MISMATCH')
        t=float(end_t)
        q.append(float(x[axis]))
        v.append(float(s.probe_u(uh,x)[axis]))
        energies.append(s.global_energy_hat(uh))
    if not np.isfinite(q).all() or not np.isfinite(v).all():
        raise RuntimeError('NONFINITE_TRAJECTORY')
    drift=float(np.max(np.abs(np.asarray(energies)-energy0))/max(abs(energy0),1e-30))
    return np.asarray(q),np.asarray(v),dict(energy_initial=energy0,energy_drift_max=drift,
                                             steps=steps,rejected_attempts=rejections,
                                             geometry_hash=geometry_hash,geometry_manifest_hash=geom_manifest_hash,
                                             geometry_provenance=marker_prov,field_initialization=initial_prov)


def atomic_write_npz(path, **values):
    tmp = path.with_name(path.stem+'.partial.npz')
    try:
        np.savez_compressed(tmp,**values)
        os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()


def export(args):
    root=Path(args.a075_root).expanduser().resolve()
    hashes=checksum_manifest(root)
    e,rb=load_solver(root)
    if args.samples < 12:
        raise ValueError('samples must be >= 12')
    if args.trials < 1:
        raise ValueError('trials must be >= 1')
    if args.grid < 16 or args.grid%2 or args.box<=0 or args.sigma<=0:
        raise ValueError('invalid box/grid/core')
    if args.trials>=80 and args.perturbation<=0:
        raise ValueError('Production-sized ensemble requires independent nonzero perturbations')
    if not 0 <= args.perturbation < 0.5 or args.perturb_length<=0:
        raise ValueError('invalid perturbation')
    if args.length_unit_m<=0 or args.speed_unit_m_s<=0:
        raise ValueError('physical scale must be positive')
    if args.final_time<=0 or args.dt<=0:
        raise ValueError('time steps must be positive')
    axis={'x':0,'y':1,'z':2}[args.axis]
    times=np.linspace(0,args.final_time,args.samples,dtype=np.float64)
    if args.mode=='ruban':
        # Verify provenance *before* the costly ensemble starts.
        seed=root/'inputs'/'ruban_t23'/rb.PRIMARY
        if not rb.verify_geometry(seed)['geometric_fidelity_pass']:
            raise RuntimeError('RUBAN_SEED_VERIFICATION_FAILED')
    out_root=(Path(args.output_parent).expanduser().resolve() if args.output_parent else Path(__file__).resolve().parent.parent/'A075_A026_EulerTrajectories_v0.1.0-outputs')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+hashlib.sha256(str(args.master_seed).encode()).hexdigest()[:8]
    out=out_root/run_id
    out.mkdir(parents=True, exist_ok=False)
    seqs=np.random.SeedSequence(args.master_seed).spawn(args.trials)
    Q=np.empty((args.trials,args.samples));V=np.empty_like(Q)
    ledger=[]
    for k,seedseq in enumerate(seqs):
        start=time.monotonic()
        q,v,diagnostics=one_trajectory(e,rb,args,root,seedseq,times,axis)
        Q[k]=q;V[k]=v
        ledger.append({'id':f'trial_{k:04d}','seed_spawn_key':list(seedseq.spawn_key),
                       'runtime_s':round(time.monotonic()-start,3), **diagnostics})
        print(f'[{k+1}/{args.trials}] Euler trajectory, steps={diagnostics["steps"]}, energy drift={diagnostics["energy_drift_max"]:.3e}',flush=True)
    length=args.length_unit_m;speed=args.speed_unit_m_s
    tscale=length/speed
    import_meta={
        'solver_name':'A075_periodic_Fourier_Galerkin_Euler_3D',
        'solver_revision':'A075-v0.2.9-pinned-sources',
        'source_manifest_sha256':source_contract_sha(hashes),
        'geometry_manifest_sha256':ledger[0]['geometry_manifest_hash'],
        'observable_definition':f'unwrapped {args.axis} coordinate and {args.axis}-velocity of material passive tracer seeded at knot-reference point; NOT knot centroid or phase clock',
        'core_model':f'Gaussian-spectral-vorticity-filter sigma={args.sigma} (in solver length units), not Ruban delta',
        'boundary_conditions':'3D periodic box, Fourier-Galerkin de-aliased 2/3',
        'generation_method':'independent_seeds_solenoidal_background_perturbation',
        'perturbation_velocity_rms_ratio':args.perturbation,
        'perturbation_filter_length_solver_units':args.perturb_length,
        'initial_condition':args.mode,
        'length_unit_m':length,'speed_unit_m_s':speed,'time_unit_s':tscale,
        'scale_origin':'DECLARED_EULER_SIMILITUDE_UNITS_NOT_CALIBRATED_SST_TIME_OR_LENGTH',
        'n_grid':args.grid,'box_solver_units':args.box,'sigma_solver_units':args.sigma,
        'sigma_cells':args.sigma*args.grid/args.box,
        'ruban_minor_radius_cells_if_applicable':(77/500)*args.grid/args.box if args.mode=='ruban' else None,
        'n_trials':args.trials,'master_seed':args.master_seed,
        'source_hashes':hashes,
        'geometry_input_sha256':ledger[0]['geometry_hash'],
        'provenance':'SOURCE_PINNED_DIRECT_EULER3D',
        'physics_status':'UNQUALIFIED: no resolution/core/domain convergence, no topology or clock evidence',
        'model_scope':'Full 3D periodic incompressible Euler FIELD; background perturbation is smooth divergence-free modes; parallel vortex array NOT implemented',
    }
    file=out/'independent_trajectories.npz'
    atomic_write_npz(file,times_s=times*tscale, q_m=Q*length, qdot_m_s=V*speed,
                     trial_ids=np.asarray([f'trial_{k:04d}' for k in range(args.trials)],dtype='<U20'),
                     metadata_json=np.asarray(json.dumps(import_meta,sort_keys=True)))
    diagnostics={'schema':'A075-A026-EULER-TRAJECTORY-EXPORT-1',
                 'source_pinned':True,'number_of_runs':args.trials,
                 'max_energy_drift':max(x['energy_drift_max'] for x in ledger),
                 'independence':'Distinct independently seeded initial solenoidal field perturbations, NOT temporally split trajectories',
                 'field_executions':ledger,
                 'scientific_gates':{'source_pin':'PASS', 'format': 'PASS' if args.trials>=80 else 'DEVELOPMENT_ONLY',
                                     'spatial_convergence':'NOT_RUN','temporal_convergence':'NOT_RUN',
                                     'core_convergence':'NOT_RUN','domain_convergence':'NOT_RUN',
                                     'tracer_convergence':'NOT_RUN',
                                     'physical_background_filament_reaction':'NOT_IMPLEMENTED',
                                     'intrinsic_phase_clock':'UNRESOLVED'}}
    (out/'RUN_DIAGNOSTICS.json').write_text(json.dumps(diagnostics,indent=2,sort_keys=True)+'\n')
    (out/'TRAJECTORY_CONTRACT.json').write_text(json.dumps(import_meta,indent=2,sort_keys=True)+'\n')
    checks={f.name:sha(f) for f in out.iterdir() if f.is_file()}
    (out/'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\n' for k,v in sorted(checks.items())))
    print(f'CREATED {file}',flush=True)
    print(f'SCIENTIFIC_STATUS DEVELOPMENT_ONLY; max rel. energy drift={diagnostics["max_energy_drift"]:.3e}')
    if args.mode=='ruban' and (77/500)*args.grid/args.box < 4:
        print('WARNING: Ruban minor-radius embedding under-resolved (<4 cells across r_minor); no geometric physics qualification')
    print(f'A026: run_all.cmd EULER "{file}" (expected exit 3: NOT CERTIFIED)')
    return file


def parser():
    p=argparse.ArgumentParser(description='A075-v0.2.9 -> A026 external Euler NPZ, source-pinned additive exporter')
    p.add_argument('--a075-root',required=True,help='Existing A075-v0.2.9 folder containing experiment/euler3d.py')
    p.add_argument('--mode',choices=('ruban','legacy_t23','coupled_ring_trefoil'),default='ruban')
    p.add_argument('--trials',type=int,default=80)
    p.add_argument('--samples',type=int,default=16)
    p.add_argument('--grid',type=int,default=32)
    p.add_argument('--box',type=float,default=10.)
    p.add_argument('--sigma',type=float,default=.5, help='Euler Gaussian-core sigma IN solver units; != Ruban delta')
    p.add_argument('--dt',type=float,default=.01,help='Max internal Euler step IN solver units')
    p.add_argument('--final-time',type=float,default=.10,help='Fixed solver final time; all trials same physical time')
    p.add_argument('--threads',type=int,default=4)
    p.add_argument('--master-seed',type=int,default=2601029)
    p.add_argument('--perturbation',type=float,default=.02,help='RMS velocity fraction of independent smooth solenoidal perturbation')
    p.add_argument('--perturb-length',type=float,default=.7)
    p.add_argument('--marker-index',type=int,default=0)
    p.add_argument('--axis',choices=('x','y','z'),default='z')
    p.add_argument('--length-unit-m',type=float,default=1.0,help='EXPLICIT Euler SI realization scale. Default 1 m for numerically conditioned A026; not a calibrated SST core.')
    p.add_argument('--speed-unit-m-s',type=float,default=1.0,help='EXPLICIT Euler SI realization speed. Default 1 m/s; not a calibrated SST clock.')
    p.add_argument('--output-parent',default='')
    p.add_argument('--max-steps',type=int,default=100000)
    p.add_argument('--cfl-target',type=float,default=.15)
    p.add_argument('--max-core-shift',type=float,default=.15)
    p.add_argument('--max-vorticity-turn',type=float,default=.12)
    p.add_argument('--no-adaptive',action='store_false',dest='adaptive',default=True)
    return p


if __name__ == '__main__':
    try:
        export(parser().parse_args())
    except Exception as exc:
        print('EXPORT_REFUSED: '+str(exc),file=sys.stderr)
        sys.exit(2)
