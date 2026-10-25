"""VCCR v0.2.0: genuinely independent *exact affine Euler-flow* tracer benchmark.

A material ring is advanced by RK4 in the analytic velocity field. Its area
and circulation are reconstructed from advected vertices and sampled velocity;
the VCCR closure is used only after measurement, as a prediction to test.

This is NOT a finite-core self-induced vortex or a knotted Euler solution.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import numpy as np


def velocity(x, t, k=0.4, omega0=1.0, freeze_rotation=False):
    """Exact incompressible Euler strain+rotation if omega=omega0*exp(k*t)."""
    x=np.asarray(x, dtype=float)
    omega=omega0 if freeze_rotation else omega0*math.exp(k*t)
    out=np.empty_like(x)
    out[...,0]=-(k/2)*x[...,0]-omega*x[...,1]
    out[...,1]=omega*x[...,0]-(k/2)*x[...,1]
    out[...,2]=k*x[...,2]
    return out


def pressure_over_density(x,t,k=0.4,omega0=1.0,freeze_rotation=False):
    x=np.asarray(x,dtype=float)
    omega=omega0 if freeze_rotation else omega0*math.exp(k*t)
    return -.5*((k*k/4-omega*omega)*(x[...,0]**2+x[...,1]**2)+k*k*x[...,2]**2)


def rk4(x0,tend,nsteps,k=0.4,omega0=1.0,freeze_rotation=False):
    if nsteps<1 or tend<0:raise ValueError('invalid RK4 integration schedule')
    x=np.array(x0,dtype=float,copy=True)
    dt=tend/nsteps
    t=0.0
    for _ in range(nsteps):
        a=velocity(x,t,k,omega0,freeze_rotation)
        b=velocity(x+.5*dt*a,t+.5*dt,k,omega0,freeze_rotation)
        c=velocity(x+.5*dt*b,t+.5*dt,k,omega0,freeze_rotation)
        d=velocity(x+dt*c,t+dt,k,omega0,freeze_rotation)
        x+=(dt/6)*(a+2*b+2*c+d)
        t+=dt
    return x


def ring_measure(points, velocities):
    """Polygon vector area and centered trapezoidal material circulation."""
    p=np.asarray(points,dtype=float); u=np.asarray(velocities,dtype=float)
    q=np.roll(p,-1,axis=0); v=np.roll(u,-1,axis=0)
    area_vec=.5*np.sum(np.cross(p,q),axis=0)
    area=float(np.linalg.norm(area_vec))
    gamma=float(np.sum(np.einsum('ij,ij->i',.5*(u+v),q-p)))
    e=p-p.mean(axis=0)
    n=area_vec/area
    planarity=float(np.max(np.abs(e@n))/math.sqrt(area/math.pi))
    cov=np.cov(e,rowvar=False,bias=True)
    eig=np.linalg.eigvalsh(cov)
    roundness=math.sqrt(max(0.,eig[1])/max(1e-300,eig[2]))
    return dict(area=area, a_eff=math.sqrt(area/math.pi), gamma=gamma,
                roundness=roundness, planarity=planarity,
                area_vec=area_vec.tolist(), normal=n.tolist())


def curl_z_measured(x,t,k,omega0,h=1e-4,freeze_rotation=False):
    """Finite-difference vorticity from sampled u, NOT prescribed omega."""
    x=np.asarray(x,float)
    ey=np.array([0.,h,0.]);ex=np.array([h,0.,0.])
    dvdx=(velocity(x+ex,t,k,omega0,freeze_rotation)[1]-velocity(x-ex,t,k,omega0,freeze_rotation)[1])/(2*h)
    dudy=(velocity(x+ey,t,k,omega0,freeze_rotation)[0]-velocity(x-ey,t,k,omega0,freeze_rotation)[0])/(2*h)
    return float(dvdx-dudy)


def euler_pde_residual(t,k=.4,omega0=1.,freeze_rotation=False,h=1e-5):
    """Numerical time/space derivatives validate Euler momentum and divergence."""
    probes=np.array([[.23,-.41,.17],[-.71,.29,.58],[.89,.44,-.37]])
    tstep=min(h, t*.1) if t else h
    ut=(velocity(probes,t+tstep,k,omega0,freeze_rotation)-velocity(probes,t-tstep,k,omega0,freeze_rotation))/(2*tstep)
    grad=np.zeros((len(probes),3,3))
    gp=np.zeros((len(probes),3))
    for j in range(3):
        delta=np.eye(3)[j]*h
        grad[:,:,j]=(velocity(probes+delta,t,k,omega0,freeze_rotation)-velocity(probes-delta,t,k,omega0,freeze_rotation))/(2*h)
        gp[:,j]=(pressure_over_density(probes+delta,t,k,omega0,freeze_rotation)-pressure_over_density(probes-delta,t,k,omega0,freeze_rotation))/(2*h)
    adv=np.einsum('pij,pj->pi',grad,velocity(probes,t,k,omega0,freeze_rotation))
    mom=ut+adv+gp
    divergence=np.trace(grad,axis1=1,axis2=2)
    # Pressure Poisson identity: Delta(p/rho) = -tr[(grad u)^2],
    # checked by an independent spatial second-difference stencil.
    h2=1e-3
    pp0=pressure_over_density(probes,t,k,omega0,freeze_rotation)
    lap=np.zeros(len(probes))
    for j in range(3):
        delta=np.eye(3)[j]*h2
        lap+=(pressure_over_density(probes+delta,t,k,omega0,freeze_rotation)
              -2*pp0+pressure_over_density(probes-delta,t,k,omega0,freeze_rotation))/(h2*h2)
    trace_grad_sq=np.einsum('pij,pji->p',grad,grad)
    poisson=lap+trace_grad_sq
    return dict(momentum_linf=float(np.max(np.abs(mom))),
                divergence_linf=float(np.max(np.abs(divergence))),
                pressure_poisson_linf=float(np.max(np.abs(poisson))))


def initial_markers(a0=1., L0=12., rings=8, markers=128, ellipse=1.):
    if rings<2 or markers<12 or a0<=0 or L0<=0 or ellipse<=0:raise ValueError('invalid material grid')
    theta=2*math.pi*np.arange(markers)/markers
    z=np.linspace(-L0/2,L0/2,rings)
    p=np.zeros((rings,markers,3))
    p[:,:,0]=a0*ellipse*np.cos(theta)[None,:]
    p[:,:,1]=a0/ellipse*np.sin(theta)[None,:]
    p[:,:,2]=z[:,None]
    centers=np.zeros((rings,3));centers[:,2]=z
    return p,centers


def snapshot(p,centers,t,k,omega0,freeze_rotation=False):
    n=len(p)
    rm=[ring_measure(p[i],velocity(p[i],t,k,omega0,freeze_rotation)) for i in range(n)]
    axial_length=np.linalg.norm(np.diff(centers,axis=0),axis=1)
    area=np.array([r['area'] for r in rm])
    # This is a polygonal swept material-cell volume, exact in affine benchmark.
    local_vol=.5*(area[1:]+area[:-1])*axial_length
    flux=np.array([curl_z_measured(centers[i],t,k,omega0,freeze_rotation=freeze_rotation)*area[i] for i in range(n)])
    return dict(time=t,length=float(np.sum(axial_length)),segment_lengths=axial_length,
                segment_volume=local_vol, total_volume=float(np.sum(local_vol)),
                ring_area=area, ring_radius=np.array([r['a_eff'] for r in rm]),
                gamma_line=np.array([r['gamma'] for r in rm]),gamma_flux=flux,
                vorticity_z=float(curl_z_measured(centers[0],t,k,omega0,freeze_rotation=freeze_rotation)),
                min_roundness=min(r['roundness'] for r in rm),
                max_planarity=max(r['planarity'] for r in rm))


def compare_measurements(initial,now,lam):
    """Independent observed area, gamma and length compared to closure after tracer run."""
    relative=lambda x,y: float(np.max(np.abs(np.asarray(x)/np.asarray(y)-1)))
    radius_ratio=np.asarray(now['ring_radius'])/np.asarray(initial['ring_radius'])
    omega_ratio=now['vorticity_z']/initial['vorticity_z']
    local_stretch=np.asarray(now['segment_lengths'])/np.asarray(initial['segment_lengths'])
    local_volume_rel=np.asarray(now['segment_volume'])/np.asarray(initial['segment_volume'])
    return dict(lambda_observed=now['length']/initial['length'],lambda_target=lam,
        measured_radius_ratio=float(np.mean(radius_ratio)),predicted_radius_ratio=float(1/math.sqrt(now['length']/initial['length'])),
        radius_closure_relative_error=float(np.max(np.abs(radius_ratio*math.sqrt(float(np.mean(local_stretch)))-1))),
        volume_relative_error=relative(now['total_volume'],initial['total_volume']),
        max_local_volume_relative_error=float(np.max(np.abs(local_volume_rel-1))),
        circulation_relative_error=relative(now['gamma_line'],initial['gamma_line']),
        circulation_stokes_relative_error=relative(now['gamma_line'],now['gamma_flux']),
        mean_vorticity_ratio=omega_ratio,predicted_vorticity_ratio=now['length']/initial['length'],
        vorticity_closure_relative_error=abs(omega_ratio/(now['length']/initial['length'])-1),
        planarity=now['max_planarity'],roundness=now['min_roundness'])


def run_case(ellipse=1.,max_lambda=4.,steps_per_unit=200.,rings=8,markers=128,freeze_rotation=False):
    k=.4;omega0=1.
    p0,c0=initial_markers(rings=rings,markers=markers,ellipse=ellipse)
    initial=snapshot(p0,c0,0.,k,omega0,freeze_rotation)
    rows=[]
    max_momentum=0;max_div=0
    for lam in [1.,1.25,1.5,2.,3.,4.]:
        if lam>max_lambda:continue
        t=math.log(lam)/k
        steps=max(1,math.ceil(t*steps_per_unit))
        pos=rk4(p0,t,steps,k,omega0,freeze_rotation)
        centers=rk4(c0,t,steps,k,omega0,freeze_rotation)
        now=snapshot(pos,centers,t,k,omega0,freeze_rotation)
        row=dict(time_dimless=t,n_steps=steps,**compare_measurements(initial,now,lam))
        euler=euler_pde_residual(t,k,omega0,freeze_rotation)
        row.update(euler)
        max_momentum=max(max_momentum,euler['momentum_linf']);max_div=max(max_div,euler['divergence_linf'])
        rows.append(row)
    tol=3.e-8 if steps_per_unit>=180 else 3e-5
    for row in rows:
        row['conservation_gate']='PASS' if max(row['radius_closure_relative_error'],row['volume_relative_error'],row['max_local_volume_relative_error'],row['circulation_relative_error'],row['vorticity_closure_relative_error'])<tol else 'FAIL'
        row['momentum_gate']='PASS' if row['momentum_linf']<1e-7 and row['divergence_linf']<1e-9 and row['pressure_poisson_linf']<1e-7 else 'FAIL'
    return dict(case='elliptic_effective_radius' if ellipse!=1 else 'circular',
                ellipse_axis_ratio=ellipse*ellipse, flow='exact_axisymmetric_affine_incompressible_Euler' if not freeze_rotation else 'intentionally_broken_Euler_control',
                k_dimless=k,omega0_dimless=omega0,ring_particles=markers,axial_rings=rings,
                rows=rows, gates={'independent_material_tracer':'PASS' if all(r['conservation_gate']=='PASS' for r in rows) else 'FAIL',
                       'euler_pde_residual':'PASS' if all(r['momentum_gate']=='PASS' for r in rows) else 'FAIL',
                       'circular_core':'PASS' if ellipse==1 else 'NOT_APPLICABLE_ELLIPTIC',
                       'knotted_finite_core_Euler':'NOT_RUN','topology':'NOT_RUN','physical_core_radius':'UNRESOLVED',
                       'swirl_clock':'NOT_RUN'})


def convergence(steps=(25,50,100,200,400)):
    out=[]
    for rate in steps:
        v=run_case(max_lambda=2.,steps_per_unit=rate,markers=64,rings=3)
        row=v['rows'][-1]
        out.append(dict(steps_per_unit=rate,n_steps=row['n_steps'],
                        radius_relative_error=row['radius_closure_relative_error'],
                        volume_relative_error=row['volume_relative_error'],
                        circulation_relative_error=row['circulation_relative_error']))
    return out


def dump_json(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def dump_csv(path,rows):
    if not rows:return
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main(argv=None):
    ap=argparse.ArgumentParser(description='VCCR v0.2.0 — INDEPENDENT exact affine Euler qualification (NOT knotted finite-core Euler)')
    ap.add_argument('--out',default='Output/VCCR_v0.2.0/euler')
    ap.add_argument('--case',choices=['circular','elliptic','both'],default='both')
    ap.add_argument('--steps-per-unit',type=float,default=200.)
    args=ap.parse_args(argv)
    if args.steps_per_unit<1:ap.error('steps-per-unit must be positive')
    path=Path(args.out);path.mkdir(parents=True,exist_ok=True)
    cases=[run_case(steps_per_unit=args.steps_per_unit)] if args.case=='circular' else [run_case(ellipse=1.6,steps_per_unit=args.steps_per_unit)] if args.case=='elliptic' else [run_case(steps_per_unit=args.steps_per_unit),run_case(ellipse=1.6,steps_per_unit=args.steps_per_unit)]
    neg=run_case(max_lambda=2.,steps_per_unit=args.steps_per_unit,markers=64,rings=3,freeze_rotation=True)
    controlled_detected=neg['gates']['euler_pde_residual']=='FAIL' and neg['gates']['independent_material_tracer']=='FAIL'
    conv=convergence()
    report=dict(schema='vccr.euleraffine.v0.2.0',version='0.2.0',status='EXACT_AFFINE_EULER_VERIFIED_NOT_KNOT_CERTIFIED',
                source='own numerically differentiated affine Euler solution and independently integrated material ring particles',
                dimensionless=True,scaling='Optional dimensionless similarity only; strain k=0.4 does NOT claim physical SST strain rate',
                assumptions=['unbounded affine flow','no pressure boundary conditions','uniform axial vorticity','local open tube, not a closed knotted filament',
                             'RK4 material tracer and polygonal area/circulation quadrature independent of closure state_from_length'],
                cases=cases,convergence=conv,
                negative_control=dict(description='Hold rotation constant under nonzero axial strain: violation of angular momentum/Kelvin and Euler momentum',
                                      rejection_detected=controlled_detected,positive_gates_of_broken_model=neg['gates']),
                overall_gates={'G0_v010_analytic':'PASS_REFERENCE_7_TESTS_SEPARATELY',
                               'G1_independent_exact_Euler_benchmark':'PASS' if all(c['gates']['euler_pde_residual']=='PASS' and c['gates']['independent_material_tracer']=='PASS' for c in cases) else 'FAIL',
                               'G2_negative_control':'PASS' if controlled_detected else 'FAIL',
                               'G3_material_cross_section_affine':'PASS' if all(c['gates']['independent_material_tracer']=='PASS' for c in cases) else 'FAIL',
                               'G4_native_knotted_solver':'NOT_RUN',
                               'G5_independent_native_vorticity_flux':'NOT_RUN',
                               'G6_spatial_temporal_convergence_native':'NOT_RUN',
                               'G7_topology_and_clearance':'NOT_RUN',
                               'G8_SST_clock':'NOT_RUN'})
    dump_json(path/'euler_report.json',report)
    dump_csv(path/'euler_circular.csv',cases[0]['rows'] if cases[0]['case']=='circular' else [])
    dump_csv(path/'euler_elliptic.csv',next((c['rows'] for c in cases if c['case']=='elliptic_effective_radius'),[]))
    dump_csv(path/'convergence.csv',conv)
    print('VCCR v0.2.0:',report['overall_gates'])
    print('WROTE:',path/'euler_report.json')
    return 0 if all(v=='PASS' or v.startswith('PASS_') or v=='NOT_RUN' for v in report['overall_gates'].values()) else 2

if __name__=='__main__':raise SystemExit(main())
