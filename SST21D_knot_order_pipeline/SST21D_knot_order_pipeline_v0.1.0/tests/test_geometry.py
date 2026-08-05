import numpy as np
from sst21d.geometry import edge_stats,curvature,analyze_components

def test_circle_geometry():
    n=256; t=np.linspace(0,2*np.pi,n,endpoint=False); p=np.c_[np.cos(t),np.sin(t),np.zeros(n)]
    e=edge_stats(p); k=curvature(p); assert abs(e['length']-2*np.pi)<1e-3; assert abs(k.mean()-1)<2e-3
    g=analyze_components([p],auto_build_native=False); assert g['global_sampled_reach_proxy']>0.9
