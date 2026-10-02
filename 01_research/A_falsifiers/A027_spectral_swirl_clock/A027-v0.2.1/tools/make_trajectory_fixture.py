from pathlib import Path
import numpy as np, pandas as pd, argparse
ap=argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--speed",type=float,default=8e5); a=ap.parse_args()
T,N=256,128; R=2e-6; L=2*np.pi*R; mode=3; k=2*np.pi*mode/L; omega=a.speed*k
t=np.linspace(0,2*np.pi*30/omega,T)
s=np.arange(N)/N*2*np.pi
rows=[]
for ti,tt in enumerate(t):
    amp=1e-8*np.cos(mode*s-omega*tt)
    x=(R+amp)*np.cos(s); y=(R+amp)*np.sin(s); z=1e-8*np.sin(mode*s-omega*tt)
    for i in range(N): rows.append((tt,i,x[i],y[i],z[i]))
pd.DataFrame(rows,columns=["time_s","point_id","x_m","y_m","z_m"]).to_csv(a.out,index=False)
