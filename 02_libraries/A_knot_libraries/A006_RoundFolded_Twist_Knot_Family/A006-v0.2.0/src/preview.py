#!/usr/bin/env python3
"""2D diagnostic plots only; not a topological certification."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
fig,ax=plt.subplots(2,2,figsize=(10,10),layout='constrained')
for a,k,n in zip(ax.flat,range(3,7),['5_2','6_1','7_2','8_1']):
    matches=sorted((ROOT/'output'/'individual').glob(f'Tm{k}_{n}_original_N*'))
    if not matches:
        a.text(.5,.5,'Not built',ha='center',va='center');a.axis('off');continue
    p=np.loadtxt(matches[-1]/'component_0.xyz')
    a.plot(p[:,0],p[:,1],linewidth=.8,color='#e6a100')
    a.plot([p[-1,0],p[0,0]],[p[-1,1],p[0,1]],linewidth=.8,color='#e6a100')
    a.set_title(f'Tm{k}: {n} (2D projection)');a.set_aspect('equal');a.axis('off')
fig.suptitle('RoundFolded v0.2.0 — 4-plat projected geometry, NOT physically relaxed')
out=ROOT/'preview_twist_family.png';fig.savefig(out,dpi=145);plt.close(fig)
print(out)
