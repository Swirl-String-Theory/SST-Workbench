import numpy as np
from src.metrics import winding_charges,segment_plane_hits,characteristic_projection_velocity

def test_phase_charge_pair():
    x=np.linspace(-1,1,128);X,Y=np.meshgrid(x,x)
    z=(X*X-.1)+1j*Y
    q=winding_charges(z.real,z.imag)
    assert sorted(qi for _,_,qi in q)==[-1,1]

def test_no_phase_pair_post():
    x=np.linspace(-1,1,128);X,Y=np.meshgrid(x,x)
    z=(X*X+.1)+1j*Y
    assert winding_charges(z.real,z.imag)==[]

def test_plane_intersections():
    th=np.arange(256)*2*np.pi/256
    c=np.column_stack([np.cos(th),0*th,-0.5+np.sin(th)])
    hits=segment_plane_hits(c)
    assert len(hits)==2
    assert abs(np.diff(np.sort(hits[:,0]))[0]-np.sqrt(3))<.002
    c[:,2]+=2
    assert len(segment_plane_hits(c))==0

def test_linear_fold():
    t=np.linspace(-.6,-.06,10);r=np.sqrt(-.6*t)
    fit=characteristic_projection_velocity(-r,r,t)
    assert fit['status']=='QUALIFIED'
    assert abs(fit['slope_R2_per_t']+2.4)<1e-10
