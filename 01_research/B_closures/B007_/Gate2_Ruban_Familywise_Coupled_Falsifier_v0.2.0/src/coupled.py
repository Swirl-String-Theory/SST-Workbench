"""Development-only live-background finite-core Fourier-Euler pilot.

Cubic periodic domain supports axial translation but not arbitrary rotation.
No nonlinear root solve and no proof of material isotopy.
"""
from __future__ import annotations
import numpy as np
import math
from scipy.spatial import cKDTree
from .reference_euler import EulerGrid,racetrack
from .geometry import total_length


def centres(style):
    if style=='none':return []
    if style=='single':return [(0.,0.)]
    if style=='triple':return [(.28*math.cos(2*math.pi*j/3),.28*math.sin(2*math.pi*j/3)) for j in range(3)]
    if style=='3x3':return [(i*.36,j*.36) for i in (-1,0,1) for j in (-1,0,1)]
    if style=='5x5':return [(i*.32,j*.32) for i in (-2,-1,0,1,2) for j in (-2,-1,0,1,2)]
    raise ValueError(style)

def racetrack_shift(base,x,y):
    dr=np.array([x,y]);r=np.linalg.norm(dr)
    dr=dr/r if r>1e-10 else np.array([1.,0.])
    p=base.copy();p[:,0]=x+dr[0]*base[:,0];p[:,1]=y+dr[1]*base[:,0]
    return p

def pair_distance_preflight(parts,sigma):
    """Conservative *sampled* no-overlap gate. Does NOT certify continuous reach."""
    if len(parts)<2:return {'sampled_minimum':None,'max_edge':None,'clearance_lower_bound':None,'status':'SINGLE_COMPONENT'}
    smallest=float('inf')
    for i in range(len(parts)):
        tree=cKDTree(parts[i])
        for j in range(i+1,len(parts)):
            d=float(np.min(tree.query(parts[j])[0]));smallest=min(smallest,d)
    max_edge=max(float(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).max()) for p in parts)
    # Any curve point within at most half of the maximum edge length of a vertex.
    # This is sufficient but overly conservative for polygon edges (not smooth curves).
    lower=max(0.,smallest-max_edge)
    return {'sampled_minimum':smallest,'max_edge':max_edge,'clearance_lower_bound':lower,
         'status':'PASS_CONSERVATIVE_POLYGON_SEPARATION' if lower>2*sigma else 'BLOCKED_NO_CERTIFIED_TUBE_CLEARANCE'}

def fixed_residual(g,fields,U,L0):
    rhs=g.rhs(fields)
    dz=1j*g.K[2][None,None,:,:,:]*fields
    residual=g.inv(rhs+U*dz)
    per=[float(np.sqrt(np.mean(np.sum(r*r,axis=0)))*L0**4) for r in residual]
    div=[float(np.max(np.abs(g.inv(1j*np.einsum('ixyz,ixyz->xyz',g.K,f))))*L0**3) for f in fields]
    return {'max_Rstar':max(per),'per_component_Rstar':per,'max_Dstar':max(div),
            'U_frozen':float(U)}

def evaluate(parts,style='single',grid=20,holdout=24,sigma=.12,box=6.,gamma_bg=.05,dt=.001):
    curves=parts+[racetrack_shift(racetrack(return_x=1.65,straight_halfheight=1.3,n_straight=48,n_arc=48),x,y) for x,y in centres(style)]
    pre=pair_distance_preflight(curves,sigma)
    ncore=len(parts);gamma_core=1.0/ncore
    def build(n):
        g=EulerGrid(int(n),box)
        fields=[];infos=[]
        for j,pts in enumerate(curves):
            w,info=g.seed(pts,gamma=gamma_core if j<ncore else gamma_bg,sigma=sigma)
            fields.append(w);infos.append(info)
        return g,np.stack(fields),infos
    g,W,infos=build(grid)
    if style!='none':
        knot=g.diagnostics(W[:ncore],total_length(parts),gamma=1.)
        bg=g.diagnostics(W[ncore:],total_length(parts),gamma=1.)
    else:
        knot=g.diagnostics(W,total_length(parts),gamma=1.);bg=None
    coupled=g.diagnostics(W,total_length(parts),gamma=1.)
    U=coupled['U_z_fitted'];train=fixed_residual(g,W,U,total_length(parts))
    q,W2,infos2=build(holdout);test=fixed_residual(q,W2,U,total_length(parts))
    drift=float(np.linalg.norm((g.rk4(W,dt)-W).ravel())/max(np.linalg.norm(W.ravel()),1e-30))
    projection=max(float(x['spectral_projection_correction_ratio']) for x in infos)
    projhold=max(float(x['spectral_projection_correction_ratio']) for x in infos2)
    filters_pass=projection<=.1 and projhold<=.1
    status='BLOCKED_GEOMETRIC_SEPARATION' if pre['status']=='BLOCKED_NO_CERTIFIED_TUBE_CLEARANCE' else (
       'BLOCKED_SPECTRAL_UNDERRESOLUTION' if not filters_pass else 'UNRESOLVED_NO_ZERO_RESIDUAL_CERTIFICATE')
    return {'background':style,'number_torus_components':ncore,'number_background_loops':len(centres(style)),
     'geometry':pre,'grid_train':grid,'grid_holdout':holdout,'sigma':sigma,'box':box,
     'projection_change_train_max':projection,'projection_change_holdout_max':projhold,
     'knot_only_max_Rstar':knot['max_R_star'],'bg_only_max_Rstar':bg['max_R_star'] if bg else None,
     'coupled_max_Rstar_fitted':coupled['max_R_star'],'train':train,'holdout':test,
     'max_divergence_spectral':test['max_Dstar'],'rk4_relative_one_step_change':drift,
     'rationale':'No Omega on cubic torus; per-component Euler residual; RK4 does not certify material tube topology.',
     'status':status,'scientific_conclusion':'G2_UNRESOLVED'}
