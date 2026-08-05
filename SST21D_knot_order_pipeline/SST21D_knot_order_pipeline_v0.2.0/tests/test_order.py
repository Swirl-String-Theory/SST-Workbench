import numpy as np
from sst21d.order import shape_order,phase_order,dmin_projected_det1

def test_rigid_invariance():
    t=np.linspace(0,2*np.pi,64,endpoint=False); p=np.c_[np.cos(t),np.sin(t),.2*np.sin(3*t)]
    a=.7; R=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    q=p@R.T+np.array([3,-2,1]); s=shape_order(p,q); assert s['Q_geom']>0.999999
    d=dmin_projected_det1(p,q); assert d.mean()<1e-20

def test_phase_order():
    x=np.linspace(0,2*np.pi,64,endpoint=False); assert phase_order(x,x+1.2)['Q_phase']>0.999999

def test_phase_dispersion_linear_modes():
    n=64; T=80; x=np.linspace(0,2*np.pi,n,endpoint=False); times=np.linspace(0,20,T,endpoint=False)
    points=np.repeat(np.c_[np.cos(x),np.sin(x),np.zeros(n)][None,:,:],T,axis=0)
    phase=np.asarray([x+0.05*np.sin(2*x-1.6*t)+0.04*np.sin(3*x-2.4*t)+0.03*np.sin(5*x-4.0*t) for t in times])
    from sst21d.order import dynamic_analyze
    r=dynamic_analyze(points,times,phase)
    assert len(r.get('dispersion_rows',[]))>=3
    assert abs(r['dispersion_exponent_p']-1.0)<0.15
