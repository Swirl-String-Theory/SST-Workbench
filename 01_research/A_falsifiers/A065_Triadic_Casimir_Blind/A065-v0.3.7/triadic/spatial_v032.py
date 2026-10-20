"""Independent *numerical diagnostics* on the ONE original 300-node trefoil.

600 nodes use preregistered periodic cubic midpoint interpolation, not new data.
This does NOT assert a second upstream provider or Euler PDE solution.
"""
from __future__ import annotations
import math, hashlib, json
from pathlib import Path
from .dynamics import evolve,rms_difference,velocities,length
from .pklsa import load_geometry
from .security import readjson

def interpolate_600(p):
    """Periodic Catmull-Rom at t=1/2; even output vertices are byte-identical anchors."""
    n=len(p);out=[]
    for i in range(n):
        a,b,c,d=p[(i-1)%n],p[i],p[(i+1)%n],p[(i+2)%n]
        out.append(tuple(b))
        out.append(tuple((-a[k]+9*b[k]+9*c[k]-d[k])/16.0 for k in range(3)))
    return out

def compare(a,b,initial,step):
    selected=b[::step]
    err=rms_difference(a,selected)
    denom=rms_difference(initial,a)
    return {'rms_absolute':err,'relative_to_coarse_displacement':err/max(denom,1e-14),
            'coarse_displacement_rms':denom,'status_at_five_percent':'PASS' if err/max(denom,1e-14)<=.05 else 'FAIL'}

def diagnose(root):
    root=Path(root)
    d=root/'data/D01_EULER/pklsa'
    source=readjson(d/'source.json')
    p=d/source['source_file']
    if hashlib.sha256(p.read_bytes()).hexdigest()!=source['raw_sha256']:
        raise ValueError('GEOMETRY_HASH_CHANGED')
    spec=readjson(root/'preregistration/QUALIFICATION_V032.json')
    old=readjson(root/'data/D01_EULER/pklsa/filament_dynamics_protocol.json')
    require=[spec['gamma']==old['gamma']==1.0,spec['epsilon']==old['core_epsilon']==.12,
             spec['T']==old['final_time']==.04,spec['fine_steps']==old['step_count_fine']==8,
             spec['periodic_midpoint']=='Catmull-Rom[-1,9,9,-1]/16',spec['threshold']==.05]
    if not all(require):raise ValueError('V032_PRECOMMITTED_PARAMETER_CHANGE')
    points=load_geometry(p)
    if len(points)!=300:raise ValueError('AUTHENTIC_GEOMETRY_REQUIRES_N300')
    levels={75:points[::4],150:points[::2],300:points,600:interpolate_600(points)}
    T=spec['T'];eps=spec['epsilon'];gamma=spec['gamma']
    trajectories={n:evolve(y,eps,gamma,T,spec['fine_steps']) for n,y in levels.items()}
    pairs={}
    for n,m in ((75,150),(150,300),(300,600),(75,300)):
        pairs[f'{n}_vs_{m}']=compare(trajectories[n],trajectories[m],levels[n],m//n)
    coarse=evolve(levels[300],eps,gamma,T,spec['coarse_steps'])
    fine300=trajectories[300]
    temporal_300=rms_difference(coarse,fine300)/max(rms_difference(levels[300],fine300),1e-14)
    ultra600=evolve(levels[600],eps,gamma,T,spec['extra_fine_steps'])
    temporal_600=rms_difference(trajectories[600],ultra600)/max(rms_difference(levels[600],ultra600),1e-14)
    pairs_high=compare(trajectories[300],ultra600,levels[300],2)
    ratio1=pairs['150_vs_300']['relative_to_coarse_displacement']/pairs['75_vs_150']['relative_to_coarse_displacement']
    ratio2=pairs['300_vs_600']['relative_to_coarse_displacement']/pairs['150_vs_300']['relative_to_coarse_displacement']
    # Qualify only the refined-grid sequence; the historical 75-150 gate stays separate FAIL.
    high_ok=pairs['150_vs_300']['relative_to_coarse_displacement']<=spec['threshold'] and pairs['300_vs_600']['relative_to_coarse_displacement']<=spec['threshold'] and ratio1<1 and ratio2<1
    time_ok=max(temporal_300,temporal_600)<spec['temporal_threshold']
    return {'schema':'A065-SPATIAL-QUALIFICATION-V032-1', 'source_sha256':source['raw_sha256'],
            'source_provider_count':1,'new_nodes_are_interpolated':True,
            'model':'dimensionless regularized midpoint-segment Biot-Savart RK4; NOT full Euler',
            'fixed_parameters':{'epsilon':eps,'gamma':gamma,'T':T},
            'levels':[75,150,300,600], 'pairs':pairs,
            'truncation_trend_ratios':{'75_150_to_150_300':ratio1,'150_300_to_300_600':ratio2},
            'time_refinement_relative':{'N300_4_vs_8':temporal_300,'N600_8_vs_16':temporal_600},
            'N300_vs_N600_time16':pairs_high,
            'geometry_lengths':{str(n):length(pts) for n,pts in levels.items()},
            'mesh_to_core':{str(n):(length(pts)/n)/eps for n,pts in levels.items()},
            'status_refined_spatial':'PASS' if high_ok else 'FAIL',
            'status_temporal':'PASS' if time_ok else 'FAIL',
            'status_full_historical':'FAIL' if pairs['75_vs_150']['status_at_five_percent']=='FAIL' else 'PASS',
            'physical_status':'NO_EULER_PDE_OR_MATERIAL_CASIMIR_CLOSURE',
            'caution':'N600 is interpolated from N300 and is a quadrature discretization, NOT independent physical geometry.'}
