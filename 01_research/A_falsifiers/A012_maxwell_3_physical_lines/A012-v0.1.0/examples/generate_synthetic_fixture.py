from __future__ import annotations
import csv, math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"examples"/"synthetic_campaign"; FIELDS=OUT/"fields"; FIELDS.mkdir(parents=True,exist_ok=True)
rows=[]; case_n=0
# Full-rank scan. Solid-body rotation has coarse kinetic stress with two equal transverse eigenvalues.
for rho in (0.5,1.0,2.0):
  for vref in (1.0,2.0,4.0):
    for geom in (0.75,1.25):
      case_n+=1; N=24; dx=geom/(N-1); x=(np.arange(N)-0.5*(N-1))*dx; X,Y,Z=np.meshgrid(x,x,x,indexing="ij")
      Om=vref/geom; u=np.stack((-Om*Y,Om*X,np.zeros_like(X)),axis=-1)
      cid=f"scale_{case_n:03d}"; np.savez_compressed(FIELDS/f"{cid}.npz",u=u,spacing=np.array([dx,dx,dx]))
      rows.append(dict(case_id=cid,file=f"fields/{cid}.npz",rho_kg_m3=rho,v_ref_m_s=vref,geom_scale=geom,family_id=cid,resolution=N,pair_id="",handedness=0,filter_radius_cells=2))
# Handedness pair at otherwise identical settings.
for hand in (+1,-1):
  N=24; geom=1.0; vref=2.0; rho=1.0; dx=geom/(N-1); x=(np.arange(N)-0.5*(N-1))*dx; X,Y,Z=np.meshgrid(x,x,x,indexing="ij")
  Om=hand*vref/geom; u=np.stack((-Om*Y,Om*X,np.zeros_like(X)),axis=-1); cid=f"hand_{'p' if hand>0 else 'm'}"
  np.savez_compressed(FIELDS/f"{cid}.npz",u=u,spacing=np.array([dx,dx,dx])); rows.append(dict(case_id=cid,file=f"fields/{cid}.npz",rho_kg_m3=rho,v_ref_m_s=vref,geom_scale=geom,family_id="hand",resolution=N,pair_id="pair_hand",handedness=hand,filter_radius_cells=2))
with (OUT/"campaign.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
# Reduced-momentum synthetic data: arbitrary coefficients intentionally unrelated to hidden theoretical target.
rng=np.random.default_rng(12345); rm=[]
beta_pu=3.25; beta_Ap=0.017
for i in range(180):
  g=f"g{i%6}"; u=rng.normal(size=3); p=beta_pu*u*(1+rng.normal(scale=0.003)); A=beta_Ap*p*(1+rng.normal(scale=0.003))
  rm.append([f"r{i:04d}",g,*u,*p,*A])
with (OUT/"reduced_momentum.csv").open("w",newline="",encoding="utf-8") as f:
  w=csv.writer(f); w.writerow(["case_id","group","u_x","u_y","u_z","p_x","p_y","p_z","A_x","A_y","A_z"]); w.writerows(rm)
# Optional storage-current synthetic closure.
nt=31; dt=0.02; t=np.arange(nt)*dt; D=np.zeros((nt,5,4,3));
for k in range(3): D[...,k]=np.sin((k+1)*2.3*t)[:,None,None]*(1+0.1*np.arange(5)[None,:,None])
dD=np.empty_like(D); dD[1:-1]=(D[2:]-D[:-2])/(2*dt); dD[0]=(D[1]-D[0])/dt; dD[-1]=(D[-1]-D[-2])/dt
Y=2.7*dD + rng.normal(scale=0.003*np.std(dD),size=dD.shape); np.savez_compressed(OUT/"storage_current.npz",D_struct=D,ampere_minus_J=Y,dt=np.array(dt))
print(OUT)
