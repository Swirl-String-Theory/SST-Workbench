from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
fig,axes=plt.subplots(2,3,figsize=(13,8))
for row,k in enumerate(['5_2','6_1']):
 for col,profile in enumerate(['ROUND','TOROIDAL','NEAR_UNKNOT']):
  path=ROOT/'output'/'individual'/f'NearUnknot_{k}_{profile}_N0512'/f'NearUnknot_{k}_{profile}_N0512.xyz'
  if not path.exists():
   path=ROOT/'output'/'individual'/f'NearUnknot_{k}_{profile}_N0256'/f'NearUnknot_{k}_{profile}_N0256.xyz'
  if not path.exists():continue
  p=np.loadtxt(path);p=np.vstack((p,p[0]))
  ax=axes[row,col];ax.plot(p[:,0],p[:,1],linewidth=.9);ax.set_aspect('equal');ax.axis('off');ax.set_title(f'{k} · {profile}')
fig.suptitle('RoundFolded v0.2.2 — geometry-only: all curves retain their source knot type')
fig.tight_layout();fig.savefig(ROOT/'preview_near_unknot.png',dpi=160)
print('Wrote preview_near_unknot.png')
