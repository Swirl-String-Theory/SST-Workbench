from __future__ import annotations
import math
import numpy as np
from scipy.optimize import linear_sum_assignment


def normalized_eigenvalue_distance(a: complex,b: complex,floor=1e-12)->float:
    return float(abs(a-b)/max(abs(a),abs(b),floor))

def normalize_vector(v):
    z=np.asarray(v,dtype=complex).reshape(-1)
    n=float(np.linalg.norm(z))
    if n<=0: raise ValueError('zero eigenvector')
    return z/n

def subspace_overlap(a,b)->float:
    x=normalize_vector(a); y=normalize_vector(b)
    return float(min(1.0,abs(np.vdot(x,y))))

def match_modes(reference_vals, reference_vecs, candidate_vals, candidate_vecs, *, eigenvalue_weight=0.5, overlap_weight=0.5):
    rv=np.asarray(reference_vals,dtype=complex).reshape(-1)
    cv=np.asarray(candidate_vals,dtype=complex).reshape(-1)
    R=np.asarray(reference_vecs,dtype=complex); C=np.asarray(candidate_vecs,dtype=complex)
    if R.ndim!=2 or C.ndim!=2 or R.shape[1]!=len(rv) or C.shape[1]!=len(cv):
        raise ValueError('eigenvector matrices must store eigenvectors as columns')
    cost=np.empty((len(rv),len(cv)),dtype=float)
    details={}
    for i,a in enumerate(rv):
        for j,b in enumerate(cv):
            d=normalized_eigenvalue_distance(a,b); ov=subspace_overlap(R[:,i],C[:,j])
            c=float(eigenvalue_weight)*d + float(overlap_weight)*(1.0-ov)
            cost[i,j]=c; details[(i,j)]=(d,ov,c)
    rr,cc=linear_sum_assignment(cost)
    out=[]
    for i,j in sorted(zip(rr,cc)):
        d,ov,c=details[(int(i),int(j))]
        out.append({'reference_index':int(i),'candidate_index':int(j),'eigenvalue_shift':float(d),'overlap':float(ov),'cost':float(c)})
    return out

def track_from_finest(levels, *, rel_tol: float, overlap_min: float, eigenvalue_weight=0.5, overlap_weight=0.5):
    """Anchor branch identity at the finest level and track backward.

    Each level: {label,eigenvalues,eigenvectors}. Eigenvectors are coefficient
    vectors in the same four-dimensional C006 Kelvin basis, so their normalized
    complex overlap is directly comparable across N.
    """
    if not levels: return {'ok':False,'reason':'NO_LEVELS','branches':[]}
    ordered=sorted(levels,key=lambda z:z['label'])
    fine=ordered[-1]
    fvals=np.asarray(fine['eigenvalues'],dtype=complex).reshape(-1)
    fvec=np.asarray(fine['eigenvectors'],dtype=complex)
    branches=[{'fine_index':i,'points':[{'label':fine['label'],'index':i,'lambda':complex(fvals[i]),'overlap_to_finer':None,'shift_to_finer':None}]} for i in range(len(fvals))]
    current_vals=fvals; current_vecs=fvec
    current_branch_to_index=list(range(len(fvals)))
    for lev in reversed(ordered[:-1]):
        vals=np.asarray(lev['eigenvalues'],dtype=complex).reshape(-1); vecs=np.asarray(lev['eigenvectors'],dtype=complex)
        matches=match_modes(current_vals,current_vecs,vals,vecs,eigenvalue_weight=eigenvalue_weight,overlap_weight=overlap_weight)
        ref_to_match={m['reference_index']:m for m in matches}
        new_branch_to_index=[None]*len(current_branch_to_index)
        for b,refidx in enumerate(current_branch_to_index):
            m=ref_to_match.get(refidx)
            if m is None: continue
            j=m['candidate_index']; new_branch_to_index[b]=j
            branches[b]['points'].append({'label':lev['label'],'index':j,'lambda':complex(vals[j]),'overlap_to_finer':m['overlap'],'shift_to_finer':m['eigenvalue_shift']})
        current_vals=vals; current_vecs=vecs
        # branch map for next coarser matching is indexed by the current level's eigenvalue indices.
        current_branch_to_index=[x if x is not None else -1 for x in new_branch_to_index]
        # Reorder current arrays so reference index equals branch index; simplifies next step.
        valid=all(x>=0 for x in current_branch_to_index)
        if not valid: break
        current_vals=np.asarray([vals[j] for j in current_branch_to_index],dtype=complex)
        current_vecs=np.column_stack([vecs[:,j] for j in current_branch_to_index])
        current_branch_to_index=list(range(len(branches)))
    for b in branches:
        b['points']=list(reversed(b['points']))
        complete=len(b['points'])==len(ordered)
        shifts=[p['shift_to_finer'] for p in b['points'] if p['shift_to_finer'] is not None]
        overlaps=[p['overlap_to_finer'] for p in b['points'] if p['overlap_to_finer'] is not None]
        positive=all(complex(p['lambda']).imag>0 for p in b['points'])
        b['complete']=complete
        b['max_eigenvalue_shift']=float(max(shifts)) if shifts else 0.0
        b['min_eigenvector_overlap']=float(min(overlaps)) if overlaps else 1.0
        b['positive_frequency_all_levels']=bool(positive)
        b['persistent']=bool(complete and positive and all(x<=rel_tol for x in shifts) and all(x>=overlap_min for x in overlaps))
    return {
        'ok':all(b['persistent'] for b in branches),
        'relative_tolerance':float(rel_tol),'overlap_min':float(overlap_min),
        'eigenvalue_weight':float(eigenvalue_weight),'overlap_weight':float(overlap_weight),
        'branch_count':len(branches),'persistent_count':sum(int(b['persistent']) for b in branches),
        'branches':branches,
    }

def select_fine_anchored_branch(tracking, fine_selected_index: int):
    for b in tracking.get('branches',[]):
        if int(b.get('fine_index',-1))==int(fine_selected_index): return b
    raise KeyError(f'fine_selected_index {fine_selected_index} not found')
