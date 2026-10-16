"""Full 3-D Euler tangent evolution of two direction-labelled *candidate* packets.
Counter-propagation and collision are output gates, never inserted as dynamics.
Complex fields represent two independently propagated real quadratures.
"""
from __future__ import annotations
import numpy as np
from scipy.spatial import cKDTree
from euler_tangent import Euler3D, L,load_geometry,normalized_components

def arc_map(g,curves):
    c=curves[0]
    seg=(np.roll(c,-1,axis=0)-c+L/2)%L-L/2
    lens=np.linalg.norm(seg,axis=1)
    total=float(lens.sum())
    samp=[]; sidx=[]
    cum=np.concatenate(([0.],np.cumsum(lens)))
    for i,dl in enumerate(lens):
        ns=max(2,int(np.ceil(dl/(g.dx*.3))))
        for j in range(ns):
            t=j/ns
            samp.append((c[i]+seg[i]*t)%L)
            sidx.append(cum[i]+dl*t)
    tree=cKDTree(np.asarray(samp),boxsize=L)
    positions=g.coords.reshape(3,-1).T
    distance, idx=tree.query(positions,k=1)
    arclength=np.asarray(sidx)[idx].reshape((g.n,)*3)
    r=distance.reshape((g.n,)*3)
    return arclength,r,total

def signed_arc_delta(s,s0,length):return (s-s0+length/2)%length-length/2

def packet(g,s,r,length,s0,sign,k_wave=8.0,radial=.45,arc_width_frac=.105):
    d=signed_arc_delta(s,s0,length)
    env=np.exp(-r*r/(2*radial**2)-d*d/(2*(arc_width_frac*length)**2))
    A=env*np.exp(1j*sign*k_wave*2*np.pi*d/length)
    # A0 is a genuine vector potential; its curl is divergence free, with grid filtering.
    potential=np.zeros((3,g.n,g.n,g.n),dtype=np.complex128)
    potential[2]=A
    real=g.project(g.curl(potential.real))
    imag=g.project(g.curl(potential.imag))
    z=real+1j*imag
    energy=np.mean(np.sum(np.abs(z)**2,axis=0))
    if energy < 1e-12:raise RuntimeError('Packet field lost in projection')
    return z/np.sqrt(energy)

def diagnostics(DA,DB,s,r,length,detector_window=.085,radial_window=.6):
    phase=np.exp(2j*np.pi*s/length)
    tube=np.exp(-r*r/(2*radial_window**2))
    detector=tube*np.exp(-signed_arc_delta(s,length/2,length)**2/(2*(detector_window*length)**2))
    vals={}
    for name,z in [('A',DA),('B',DB)]:
        e=np.sum(np.abs(z)**2,axis=0)
        signal=float(np.mean(detector*e))
        tube_e=e*tube
        norm=np.sum(tube_e)+1e-30
        m=np.sum(tube_e*phase)/norm
        vals[name+'_detector']=signal
        vals[name+'_centroid_s']=float((np.angle(m)%(2*np.pi))*length/(2*np.pi))
        vals[name+'_localization']=float(abs(m))
    cross=2*np.real(np.sum(DA*np.conj(DB),axis=0))
    I_a=vals['A_detector'];I_b=vals['B_detector']
    interference=float(np.mean(detector*cross))
    vals['detector_cross']=interference
    vals['detector_total']=I_a+I_b+interference
    vals['detector_cross_fraction']=float(interference/(I_a+I_b+1e-30))
    vals['global_cross']=float(np.mean(cross))
    vals['total_perturbation_rms_A']=float(np.sqrt(np.mean(np.sum(np.abs(DA)**2,axis=0))))
    vals['total_perturbation_rms_B']=float(np.sqrt(np.mean(np.sum(np.abs(DB)**2,axis=0))))
    return vals

def integrate_packets(path,n=16,core=.4,steps=160,dt=.045, background_sign=1, no_flow=False):
    geom,sha=load_geometry(path);g=Euler3D(n,core)
    curves,_=normalized_components(geom)
    U=g.velocity_from_curve(curves)*background_sign
    if no_flow: U*=0
    s,r,length=arc_map(g,curves)
    # Locations are chosen before any evolution: ±0.14 circumference from splitter s=0.
    A=packet(g,s,r,length, .14*length,+1)
    B=packet(g,s,r,length,-.14*length,-1)
    D=np.stack([A.real,A.imag,B.real,B.imag])
    data=[]
    for i in range(steps+1):
        da=D[0]+1j*D[1];db=D[2]+1j*D[3]
        q=diagnostics(da,db,s,r,length)
        q.update(t=float(i*dt),base_rms=float(np.sqrt(np.mean(np.sum(U*U,axis=0)))) ,
                 max_divergence=float(max(g.divergence_relative(U),*[g.divergence_relative(d) for d in D]))) 
        data.append(q)
        if i<steps: U,D=g.rk4(U,D,dt)
    # Objective packet-displacement and arrival gates; failures are kept in output.
    import pandas as pd
    f=pd.DataFrame(data)
    prop={}
    for name,expected in [('A',1),('B',-1)]:
        phase=np.unwrap(f[name+'_centroid_s'].to_numpy()*2*np.pi/length)
        shift=float((phase[-1]-phase[0])*length/(2*np.pi))
        coherence=float(f[name+'_localization'].min())
        start=float(f[name+'_detector'].iloc[0]); peak=float(f[name+'_detector'].max());peak_index=int(f[name+'_detector'].to_numpy().argmax())
        time=float(f.t.iloc[peak_index])
        evidence=bool(expected*shift>0.07*length and coherence>.22 and peak_index>1 and peak>2*max(start,1e-10))
        prop[name]=dict(shift_signed_dimless=shift,expected_sign=expected,
                        min_localization=coherence,signal_start=start,signal_peak=peak,
                        time_peak=time,evidence=evidence)
    collision=bool(prop['A']['evidence'] and prop['B']['evidence'] and abs(prop['A']['time_peak']-prop['B']['time_peak'])<.25*(steps*dt))
    return f,dict(source_sha256=sha,grid=n,core=core,dt=dt,steps=steps,T=steps*dt,
                  circumference_dimensionless=length,
                  source_arc_fractions=[.14,.86],detector_arc_fraction=.5,
                  vortex_background_reversed=bool(background_sign<0),no_flow=bool(no_flow),
                  max_divergence=float(f.max_divergence.max()),
                  max_abs_interference_fraction=float(f.detector_cross_fraction.abs().max()),
                  max_signal_A=float(f.A_detector.max()), max_signal_B=float(f.B_detector.max()),
                  evidence=prop,verified_collision=collision,
                  scientific_status='DYNAMIC_3D_EULER_TANGENT_PACKET_SCREEN_ONLY')
