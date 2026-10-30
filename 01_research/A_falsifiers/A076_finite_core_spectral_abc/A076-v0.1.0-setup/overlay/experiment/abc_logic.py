"""Blind A/B/C decision rules. A failure to promote is not evidence for A."""
from __future__ import annotations
from dataclasses import dataclass
import math

VALID_STATES = {'A_SUPPORTED_WITHIN_GRID_SCOPE','B_SPECTRAL_ONLY','C_HIERARCHY_SUPPORTED',
                'UNRESOLVED','REJECTED_NUMERICAL_ARTIFACT','C_NOT_EVALUATED'}


def events_of(cases, *, kind='fourier_sector_growth_transition', abs_m=2):
    out=[]
    for case in cases:
        for c in case['result'].get('candidates',[]):
            if c.get('kind') == kind and int(c.get('dominant_abs_m',-1)) == abs_m:
                if c.get('equilibrium_gate_ok') is not True: continue
                if float(c.get('mode_overlap_prev',0.)) < .80: continue
                out.append({'case':case['case'],'axis':case['axis'],'value':case['value'],
                            'q':float(c['q']),'abs_m':abs_m,'sector':c['sector'],
                            'kind':kind})
    return out


def adjudicate(cases, *, q_tol=.005, q_triplet_tol=.02):
    """Do not silently turn a missing event into a FAIL or a different mode into a match."""
    from .finite_core_spectral.fourier_convergence import evaluate_fourier_convergence
    clusters=evaluate_fourier_convergence(cases,q_cluster_tol=q_triplet_tol,q_gate_tol=q_tol)
    passing=[x for x in clusters if x.get('promote_converged_candidate') is True]
    growth=[x for x in passing if x.get('kind')=='fourier_sector_growth_transition_cluster'
            and int(x.get('dominant_abs_m',-1))==2]
    b=bool(growth)
    # The original full Jacobian may still have growing modes outside this sector.
    # Thus even a confirmed m=2 neutral boundary is NOT whole-flow stability.
    other=[x for x in passing if int(x.get('dominant_abs_m',0))>=3]
    return {'A':'UNRESOLVED',
            'B':'B_SPECTRAL_ONLY' if b else 'UNRESOLVED',
            'C':'UNRESOLVED' if b and other else 'C_NOT_EVALUATED',
            'n_clusters':len(clusters),'n_promoted':len(passing),
            'm2_promoted':growth,'other_mode_promoted':other,
            'criteria':{'q_tol':q_tol,'q_triplet_tol':q_triplet_tol,
             'B_requires':'same physical m=2 transition in required resolution/shell/FD ladders; full-field stability not inferred',
             'A_requires':'predeclared exhaustive and converged negative search; missing B evidence is insufficient',
             'C_requires':'two independent scales plus verified coupling, multiple independent geometry provenance groups, temporal+spatial convergence; spectrum alone insufficient'},
            'all_clusters':clusters}


def classify_hierarchy(*, scales, coupling_verified, topology_providers, spatial_converged, temporal_converged):
    finite=[float(q) for q in scales if isinstance(q,(float,int)) and math.isfinite(q)]
    distinct=len(finite)>=2 and (max(finite)-min(finite))>.10
    if not distinct or not coupling_verified or topology_providers<2 or not spatial_converged or not temporal_converged:
        return 'UNRESOLVED'
    return 'C_HIERARCHY_SUPPORTED'
