#!/usr/bin/env python3
from pathlib import Path
import sys,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src import sst_v030 as s
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)

fig=plt.figure(figsize=(10,4.1))
for i,(name,geo) in enumerate([('0_1 ring',s.ring(256)),('3_1 trefoil',s.trefoil(256))]):
    ax=fig.add_subplot(1,2,i+1,projection='3d')
    g=np.vstack((geo,geo[0]));ax.plot(g[:,0],g[:,1],g[:,2],lw=1.7)
    ax.set_title(f'{name} — synthetic, not PKLSA native')
    for j,lab in enumerate(['x/r_c','y/r_c','z/r_c']):[ax.set_xlabel,ax.set_ylabel,ax.set_zlabel][j](lab)
    ax.set_box_aspect([1,1,.6])
fig.tight_layout();fig.savefig(OUT/'geometry.png',dpi=155);plt.close(fig)

r=[s.ring_mechanics(n) for n in (64,128,256,512)]
fig,ax=plt.subplots(figsize=(8,3.6));ax.plot([v['n'] for v in r],[v['mean_drift_dimless'] for v in r],marker='o')
ax.set_xscale('log',base=2);ax.set_xlabel('Segments N');ax.set_ylabel('Self-induced ring speed / (Gamma/r_c)');ax.grid(alpha=.25)
fig.tight_layout();fig.savefig(OUT/'ring_convergence.png',dpi=170);plt.close(fig)

x=np.linspace(-2,2,300)
fig,ax=plt.subplots(figsize=(8,3.6))
for sg in [.2,.4,.8]:ax.plot(x,[s.overlap(x0,sg,[(0.,.3,1.)]) for x0 in x],label=f'Gaussian width sigma={sg}')
ax.set_xlabel('Normalized detuning (arbitrary frequency unit)');ax.set_ylabel('Spectral overlap Y (normalized response scale)');ax.legend(fontsize=8);ax.grid(alpha=.25)
fig.tight_layout();fig.savefig(OUT/'voigt_overlap.png',dpi=170);plt.close(fig)

f=ROOT/'results'/'v030_validation.json'
d=json.loads(f.read_text())
with (OUT/'ring_refinement.csv').open('w',encoding='utf-8') as ff:
    ff.write('N,ring_speed_dimless,energy_proxy_dimless,impulse_z_dimless,expected_impulse_z\n')
    for row in r:ff.write(f"{row['n']},{row['mean_drift_dimless']:.13g},{row['energy_dimless']:.13g},{row['impulse_z_dimless']:.13g},{row['expected_impulse_z']:.13g}\n")
with (OUT/'derived_scales.json').open('w',encoding='utf-8') as ff:
    json.dump({'r_c_m':s.R_C,'v_swirl_m_s':s.V_SWIRL,'rho_f_kg_m3':s.RHO_F,
               'Gamma_m2_s':s.GAMMA,'Omega0_rad_s':s.OMEGA_0,
               'filament_time_scale_s':s.T_REF,
               'ring_drift_256_m_s':r[2]['mean_drift_dimless']*s.GAMMA/s.R_C,
               'ring_drift_512_m_s':r[3]['mean_drift_dimless']*s.GAMMA/s.R_C},ff,indent=2)
print('Figures and data saved to',OUT)
