#!/usr/bin/env python3
"""Execute stand-alone Hicks/Hill analytic controls; never claim v1.0.7 certification."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import datetime as dt
import math
import numpy as np
from scipy.integrate import solve_ivp
from hicks_hill import SphereVortex,root_families,J
from hicks_hill.bridges import strain_and_pressure_poisson,volume_energy

HERE=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def spectral_winding(field,s0):
    """One-poloidal-cycle winding from an equatorial return in the first lambda1 flow."""
    u0=field.velocity(s0,0)[2]
    direction=1 if u0>0 else -1
    def velocity(t,x):
        s,z,_=x
        us,uphi,uz=field.velocity(s,z)
        return [us,uz,uphi/s]
    def cross(t,x):return x[1] if t>1e-6 else direction*1e-5
    cross.direction=direction;cross.terminal=True
    res=solve_ivp(velocity,(0,30),[s0,0,0],events=cross,rtol=3e-10,atol=3e-10,max_step=.01)
    if res.status!=1:raise RuntimeError('Winding return not found')
    orig=field.psi(s0,0);final=field.psi(res.y[0,-1],res.y[1,-1])
    return {'s0_over_a':s0/field.a,'winding_phi_per_poloidal_cycle':float(res.y[2,-1]/(2*math.pi)),
            'cycle_time':float(res.t[-1]),'psi_relative_drift':float(abs(final-orig)/max(abs(orig),1e-12)),
            'endpoint_s_error':float(abs(res.y[0,-1]-s0))}


def execute(output):
    output.mkdir(parents=True,exist_ok=True)
    proto=HERE/'configs'/'protocol.json'
    protocol=json.loads(proto.read_text())
    roots=root_families(3)
    first=SphereVortex(lam=roots['lambda1'][0])
    rest=SphereVortex(lam=roots['lambda2'][0])
    hill=SphereVortex(lam=0)
    points=[(.23,.41),(.37,.21),(.52,-.3),(.49,.5),(.81,.12)]
    cases={label:{'lambda':field.lam,'translation_U':field.U,
           'surface':field.surface_residual(),
           'interior_residuals':[{'s':s,'z':z,**field.numerical_residual(s,z)} for s,z in points]} for label,field in [('Hill',hill),('Hicks_Beltrami_1',first),('Hicks_static_1',rest)]}
    windings=[spectral_winding(first,s) for s in (.68,.72,.8,.88,.94)]
    eps=1e-7;s=.6;z=math.sqrt(1-s*s)
    inner=np.array(first.velocity(s*(1-eps),z*(1-eps)))
    outer=np.array(first.velocity(s*(1+eps),z*(1+eps)))
    boundary_velocity_jump=float(np.linalg.norm(outer-inner))
    boundary_pressure_jump=abs(first.pressure(s*(1+eps),z*(1+eps))-first.pressure(s*(1-eps),z*(1-eps)))
    max_div=max(abs(v['divergence']) for c in cases.values() for v in c['interior_residuals'])
    max_euler=max(v['euler_norm'] for c in cases.values() for v in c['interior_residuals'])
    max_beltrami=max(v['beltrami_norm'] for v in cases['Hicks_Beltrami_1']['interior_residuals'])
    max_surf=max(c['surface']['normal_velocity_abs_max'] for c in cases.values())
    max_psi=max(c['surface']['psi_abs_max'] for c in cases.values())
    allroots=max(max(abs(J(x)) for x in roots['lambda1']),max(abs(3*J(x)-x*math.sin(x)) for x in roots['lambda2']))
    gates=[]
    def add(gid,question,condition,metrics,reason):
        status=('PASS' if condition else 'FAIL') if condition is not None else 'UNRESOLVED'
        gates.append({'gate_id':gid,'status':status,'question':question,'reason':reason,
            'metrics':metrics,'actual_backend':'python_scipy_fp64','authority':'REFERENCE_ONLY'})
    add('H0','Protocol/source integrity recorded?',proto.is_file(),{'protocol_sha256':digest(proto),'scope':'standalone analytical prototype'},'Not a v1.0.7 frozen framework instance.')
    add('H1','Do analytical roots satisfy registered equations?',allroots<1e-10,{'max_root_equation_abs_residual':allroots,'lambda1':roots['lambda1'],'lambda2':roots['lambda2']},'Hicks lambda1/lambda2 control equations.')
    add('H2','Does Hill zero-swirl control satisfy Euler/divergence?',max(v['euler_norm'] for v in cases['Hill']['interior_residuals'])<2e-5,{'max_hill_euler_residual':max(v['euler_norm'] for v in cases['Hill']['interior_residuals'])},'Analytic Hill control: not proof of stability.')
    add('H3','Does first Hicks Beltrami field satisfy curl(u)=k*u and stationary Euler?',max_beltrami<2e-5 and max_euler<2e-5 and max_div<2e-5,{'max_beltrami':max_beltrami,'max_euler':max_euler,'max_div':max_div},'Finite differences at points strictly inside sphere; Python reference only.')
    add('H4','Does Hicks lambda2 first mode have zero translation?',abs(rest.U)<1e-10,{'translation_U':rest.U},'Zero external aggregate translation does not imply zero internal motion.')
    add('H5','Is the spherical boundary a material surface in the co-moving frame?',max_surf<1e-10 and max_psi<1e-10,{'max_surface_normal_velocity':max_surf,'max_surface_psi':max_psi},'No normal flux across spherical separatrix in exact field.')
    add('H6','Do internal/external pressure and velocity match at the surface?',boundary_velocity_jump<1e-4 and boundary_pressure_jump<1e-4,{'boundary_velocity_jump_eps1e7':boundary_velocity_jump,'pressure_jump_eps1e7':boundary_pressure_jump},'One matched mid-latitude point, finite-offset diagnostic only.')
    add('H7','Are torus-knot accessibility and finite-core vortex-tube stability certified?',None,{'sampled_windings':[round(w['winding_phi_per_poloidal_cycle'],8) for w in windings]},'Five closed vortex-line winding diagnostics do NOT classify finite vortex tubes or certify inaccessible topologies.')
    add('H8','Has independent C++ FP64 certification run through v1.0.7 frozen protocol?',None,{'backend':'Python FP64 reference only'},'Must instantiate official v1.0.7 template and run native certification; not executed in this portable prototype.')
    poisson={label:strain_and_pressure_poisson(field,.4,.25,.2) for label,field in [('Hill',hill),('Beltrami_1',first)]}
    energies={label:volume_energy(field,order=60) for label,field in [('Hill',hill),('Beltrami_1',first),('Static_1',rest)]}
    echeck={label:volume_energy(field,order=36) for label,field in [('Hill',hill),('Beltrami_1',first),('Static_1',rest)]}
    max_poisson=max(abs(x['pressure_poisson_residual']) for x in poisson.values())
    max_energy_rel=max(abs(energies[k]['total_lab_kinetic_energy']-echeck[k]['total_lab_kinetic_energy'])/max(1e-12,energies[k]['total_lab_kinetic_energy']) for k in energies)
    add('H9','Does exact pressure satisfy incompressible pressure-Poisson closure?',max_poisson<0.005,{'max_pressure_poisson_abs':max_poisson},'A046 analytical field control at two interior samples; no gravity metric claims.')
    add('H10','Does finite laboratory-frame kinetic-energy quadrature converge?',max_energy_rel<5e-5,{'max_order36_60_relative_error':max_energy_rel,'energies':{k:round(v['total_lab_kinetic_energy'],8) for k,v in energies.items()}},'A057 reference energy control only; not at matched fixed circulation or topology and not a mass ratio.')
    # Keep schema deliberately distinct from official frozen framework evidence.
    ledger={'schema':'SST-HICKS-PROTOTYPE-GATE-LEDGER-1','definitions':[{'gate_id':k,'question':v} for k,v in protocol['gates'].items()], 'records':gates}
    ledger['ledger_sha256']=hashlib.sha256(json.dumps(ledger,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (output/'GATE_LEDGER.json').write_text(json.dumps(ledger,indent=2)+'\n')
    summary={'schema':'SST-HICKS-PROTOTYPE-RUN-SUMMARY-1','mode':'ANALYTIC_BASIC','revealed':False,'protocol_bundle_sha256':digest(proto), 'gate_ledger_sha256':ledger['ledger_sha256'], 'scientific_certification':'NOT_RUN','source':'standalone analytical verification, no external source replication'}
    (output/'RUN_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'BACKEND_MANIFEST.json').write_text(json.dumps({'schema':'SST-HICKS-PROTOTYPE-BACKENDS','python_reference':{'precision':'FP64','authority':'REFERENCE'},'cpp_certification':{'status':'NOT_RUN'},'framework_target':'v1.0.7; not instantiated'},indent=2)+'\n')
    data={'schema':'SST-HICKS-ANALYTIC-CONTROLS-1','computed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'roots':roots,'cases':cases,'a046_pressure_poisson_references':poisson,'a057_volume_energy_references':energies,'winding_diagnostics':windings,'boundary_velocity_jump':boundary_velocity_jump,'boundary_pressure_jump':boundary_pressure_jump,'overall':'ANALYTIC_REFERENCE_ONLY'}
    (output/'HICKS_CONTROLS.json').write_text(json.dumps(data,indent=2)+'\n')
    (output/'UPGRADE_READINESS.json').write_text(json.dumps({'A046':'ANALYTIC_FIELD_CONTROL_READY','A054':'CONSTRAINED_STATE_SELECTOR_REFERENCE_DEFINED','A055':'WINDING_GATE_SAMPLED_NOT_CERTIFIED','A057':'VOLUME_ENERGY_FUTURE','A050':'FLOW_MODE_REFERENCE_FUTURE','A060':'FLOWLINE_VS_VORTEX_TUBE_DISCRIMINATOR_FUTURE','A061':'SPATIAL_SWIRL_CONTROL_FUTURE'},indent=2)+'\n')
    print(json.dumps({'output':str(output),'gates':{g['gate_id']:g['status'] for g in gates},'max_div':max_div,'max_euler':max_euler,'winding':windings[2]['winding_phi_per_poloidal_cycle']},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=HERE/'A063_Hicks_Hill_Euler_Separatrix_Falsifier_v0.1.0-outputs');arg=ap.parse_args()
    execute(arg.out.resolve())
