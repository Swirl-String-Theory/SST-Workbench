"""Manufacture a labelled synthetic data-contract fixture; NOT independent native Euler data."""
import json,math
from pathlib import Path
import numpy as np
from vccr.euler_qualification import initial_markers,rk4,velocity,curl_z_measured,ring_measure

def create():
    # Dimensionless Euler field mapped to arbitrary SI units: 1 unit length = 1 mm,
    # 1 unit time = 1 s. NOT calibrated to SST physical scales.
    scale=1e-3
    p0,centers0=initial_markers(a0=1.,L0=2.,rings=3,markers=48)
    frames=[]
    for lam in (1.,2.):
        t=math.log(lam)/.4
        nsteps=max(1,math.ceil(t*200))
        p=rk4(p0,t,nsteps)
        centers=rk4(centers0,t,nsteps)
        for j in [1]:
            ringpos=p[j]*scale
            ringvel=velocity(p[j],t)*scale
            m=ring_measure(ringpos,ringvel)
            docseg=dict(material_segment_id='demo_tube_0_segment_0',
                        material_marker_ids=[f'm{i:04d}' for i in range(len(ringpos))],
                        axial_marker_ids=['axial_low','axial_high'],
                        axial_points_m=[(centers[0]*scale).tolist(),(centers[-1]*scale).tolist()],
                        ring_positions_m=ringpos.tolist(),ring_velocities_m_s=ringvel.tolist(),
                        vorticity_flux_m2_s=float(curl_z_measured(centers[j],t,.4,1.)*m['area']))
            frames.append(dict(t_s=t,segments=[docseg]))
    obj=dict(schema='vccr.native.material.v1',source_provenance='synthetic_demo',
             metadata={'simulation':'exact_affine_Euler_synthetic_markers','mesh_independence':'NOT_ESTABLISHED','material_identity':'known_by_construction','units':'SI, 1e-3 meter length unit and 1 second time unit'},
             frames=frames)
    dest=Path(__file__).with_name('synthetic_native_contract_demo.json')
    dest.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
    print(dest)
if __name__=='__main__':create()
