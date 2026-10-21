"""Generate static 2D shape comparisons; these are not KnotPlot relaxations."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tikz_roundfold import dense_xyz,resample3
from near_unknot import params,annulus_squeeze
from smooth_clasp import fold_map,resample_periodic_c2
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'previews';OUT.mkdir(exist_ok=True)
for label in ['5_2','6_1']:
    baseline,_=dense_xyz(label)
    center,R,_=params(baseline)
    old=resample3(annulus_squeeze(baseline,.12,2.5,center,R)*12,512)
    for region in ['FULL','LOWER_CLASP']:
        fig,ax=plt.subplots(figsize=(8.5,7))
        for name in ['SOFT','BALANCED','TIGHT']:
            base,_=dense_xyz(label,width=.02,height=.10)
            xyz,_=fold_map(base,name)
            p=resample_periodic_c2(xyz,512)
            q=np.vstack([p[:,:2],p[0,:2]])
            ax.plot(q[:,0],q[:,1],lw=1.5,label=name)
        o=np.vstack([old[:,:2],old[0,:2]])
        ax.plot(o[:,0],o[:,1],lw=0.9,ls='--',alpha=.8,label='v0.2.2 NEAR_UNKNOT')
        if region=='LOWER_CLASP':
            yc=np.min(o[:,1]);xc=np.median(o[:,0]);
            ax.set_xlim(xc-28,xc+28);ax.set_ylim(yc-12,yc+25)
        ax.set_aspect('equal',adjustable='box')
        ax.set_xlabel('x [KnotPlot units]');ax.set_ylabel('y [KnotPlot units]')
        ax.set_title(f'{label} v0.2.3 — {region} / static XY projection')
        ax.legend(fontsize=9);ax.grid(alpha=.25)
        fig.tight_layout();fig.savefig(OUT/f'{label}_{region}.png',dpi=150)
        plt.close(fig)
print('Previews saved under',OUT)
