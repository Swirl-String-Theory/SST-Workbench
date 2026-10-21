from pathlib import Path
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tikz_roundfold import dense_xyz
ROOT=Path(__file__).resolve().parents[1]
fig,axes=plt.subplots(1,2,figsize=(13,6))
for ax,label in zip(axes,('5_2','6_1')):
    src,diag=dense_xyz(label,density=200)
    xyz=np.vstack((src,src[0]))
    ax.plot(xyz[:,0],xyz[:,1],linewidth=1.6,color='black')
    ax.set_title(f'TikZ points → smooth projection: {label}\n{diag["crossings"]} crossings; determinant {diag["determinant"]}')
    ax.set_aspect('equal');ax.axis('off')
fig.suptitle('RoundFolded v0.2.1 — supplied control points; periodic spline approximation to Hobby',fontsize=13)
fig.tight_layout()
fig.savefig(ROOT/'preview_tikz_roundfold.png',dpi=150)
print('Saved preview',ROOT/'preview_tikz_roundfold.png')
