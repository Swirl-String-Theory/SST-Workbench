"""Auditable centreline plots; line width is illustrative, NOT a physical core."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .model import torus_knot

def closed(x):
    x=np.asarray(x)
    return np.vstack([x,x[0]])

def seed_quad(out:Path,b0:float=.154):
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    x=closed(torus_knot(2048,b0))
    fig=plt.figure(figsize=(10,8.2),layout='constrained')
    dims=[(0,1,'Top (view along +z): x-y'),(1,2,'Side (along +x): y-z'),(0,2,'Front (along +y): x-z')]
    for i,(a,b,title) in enumerate(dims,1):
        ax=fig.add_subplot(2,2,i);ax.plot(x[:,a],x[:,b],lw=1.55,color='#155c83')
        ax.plot(x[0,a],x[0,b],marker='o',ms=3.2,color='#b65d32');ax.set_title(title,fontsize=10)
        ax.set_aspect('equal', adjustable='box');ax.grid(alpha=.17)
        ax.set_xlabel(['x','y','z'][a]+'/R0');ax.set_ylabel(['x','y','z'][b]+'/R0')
    ax=fig.add_subplot(2,2,4,projection='3d')
    ax.plot(*x.T,lw=1.8,color='#155c83');ax.scatter(*x[0],s=18,c='#b65d32')
    ax.set_title('3D perspective (centreline)',fontsize=10)
    ax.view_init(elev=22,azim=35)
    ax.set_box_aspect([1,1,.6]);ax.set_xlabel('x/R0');ax.set_ylabel('y/R0');ax.set_zlabel('z/R0')
    fig.suptitle(f'Ruban T(2,3) analytic seed | B0={b0:g} | closed centreline (no finite-core radius)',fontsize=13)
    fig.savefig(out,dpi=150,bbox_inches='tight');plt.close(fig)
    return out

def evolution_plot(out, npz, trace):
    import csv
    from .metrics import shape_drift
    archive=np.load(npz);times=archive['times'];xs=archive['xyz']
    with open(trace,newline='') as f: rows=list(csv.DictReader(f))
    fig=plt.figure(figsize=(10,6.5),layout='constrained')
    ax=fig.add_subplot(2,2,1,projection='3d')
    x0=closed(xs[0]);xf=closed(xs[-1]);ax.plot(*x0.T,color='#9c9c9c',lw=1,label='t=0')
    center=xs[-1].mean(0)-xs[0].mean(0);ax.plot(*(xf-center).T,color='#155c83',lw=1.3,label=f't={times[-1]:.4g}, recentered')
    ax.set_box_aspect([1,1,.6]);ax.view_init(elev=23,azim=35);ax.set_title('3D: initial vs final, translation removed');ax.legend(fontsize=7)
    ax=fig.add_subplot(2,2,2)
    for k in np.unique(np.linspace(0,len(times)-1,min(5,len(times)),dtype=int)):
        x=closed(xs[k]-xs[k].mean(0));ax.plot(x[:,0],x[:,1],lw=1,label=f't={times[k]:.3g}')
    ax.set_title('Top projection (recentered)');ax.set_aspect('equal');ax.legend(fontsize=7)
    ax=fig.add_subplot(2,2,3)
    ax.plot([float(r['time']) for r in rows],[float(r['energy_rel']) for r in rows],marker='.',ms=3)
    ax.axhline(.001,ls='--',lw=1,color='#aa4433',label='energy stop cap')
    ax.set_xlabel('dimensionless t');ax.set_ylabel('relative energy drift');ax.set_title('Energy diagnostic');ax.legend(fontsize=7)
    ax=fig.add_subplot(2,2,4)
    ax.plot([float(r['time']) for r in rows],[float(r['shape_rms']) for r in rows],marker='.',ms=3)
    ax.axhline(.25,ls='--',lw=1,color='#aa4433',label='deformation cap')
    ax.set_xlabel('dimensionless t');ax.set_ylabel('RMS shape drift / R0');ax.set_title('Geometric diagnostic');ax.legend(fontsize=7)
    fig.suptitle('DEVELOPMENT ONLY - time evolution is not Ruban long-time certification',fontsize=12)
    fig.savefig(out,dpi=150,bbox_inches='tight');plt.close(fig)
    return out
