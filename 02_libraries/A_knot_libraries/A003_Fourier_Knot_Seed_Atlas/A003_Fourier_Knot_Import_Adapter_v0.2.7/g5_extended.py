"""A003 v0.2.5 extended G5 — *necessary* invariants, no knot certification.

G5a: symbolic Alexander polynomial from the actual polygon via pyknotid,
      only when bounded by crossing-complexity guard.
G5b: signed degree-3 Vassiliev invariant and reflection-odd check.
G5c: exact torus reference with an independently coded unreduced Burau braid
      modular identity. This references (p,q), NOT the imported XYZ geometry.
G5d: checks G5a/G5b over two mesh resolutions and two fixed, generic projections.

No diagnostic here is proof of ambient isotopy or knot/chirality classification.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import math
from pathlib import Path
from collections import Counter
import sys
from typing import Callable

import numpy as np
from gates_g4_g5 import (_pyknotid_numpy_legacy_compatibility,
                         _safe_provider_version, QualificationError)

SCHEMA = 'sst.a003.extended-g5/1'
TORUS_FAMILIES = {'torus', 'fibonacci_torus', 'torus_control'}


def torus_polynomial_coefficients(p: int, q: int) -> list[int]:
    """Normalized Delta(T(p,q)): (1-t^(pq))(1-t)/((1-t^p)(1-t^q))."""
    if p < 2 or q < 2 or math.gcd(p, q) != 1:
        raise QualificationError('torus parameters must be coprime integers >= 2')
    d = (p-1)*(q-1)
    c = [0]*(d+1)
    for k in range(d+1):
        c[k] = (1 if k == 0 else -1 if k == 1 else 0)
        if k >= p: c[k] += c[k-p]
        if k >= q: c[k] += c[k-q]
        if k >= p+q: c[k] -= c[k-p-q]
    if c[0] != 1 or c[-1] != 1 or c != c[::-1] or sum(c) != 1:
        raise QualificationError('internal torus polynomial reference failure')
    return c


def known_polynomial_reference(rec: dict) -> list[int] | None:
    fam = rec.get('family')
    if fam in TORUS_FAMILIES:
        return torus_polynomial_coefficients(int(rec['p']), int(rec['q']))
    if fam == 'fibonacci_fourier':
        return [1, -1, 1] if rec.get('fibonacci_index') == 3 else None
    if fam == 'twist':
        m = rec.get('m')
        if not isinstance(m, int) or m < 1:
            return None
        a = (m + 1)//2
        # Normalize all Alexander polynomials by Delta(1)=+1.
        # even m=2: -1+3t-t²; odd m=3: 2-3t+2t².
        return [a, -(2*a-1), a] if m % 2 else [-a, 2*a+1, -a]
    return None


def expected_crossings(rec: dict) -> int | None:
    if rec.get('family') in TORUS_FAMILIES:
        p, q = int(rec['p']), int(rec['q'])
        return min((p-1)*q, (q-1)*p)
    if rec.get('family') == 'twist':
        m = rec.get('m')
        return m+2 if isinstance(m, int) and m >= 1 else None
    if rec.get('family') == 'fibonacci_fourier' and rec.get('fibonacci_index') == 3:
        return 3
    # The complex Fibonacci Fourier curves are not assumed to be torus knots.
    return None


def modular_det(matrix: list[list[int]], prime: int) -> int:
    arr = [list(row) for row in matrix]
    n = len(arr)
    accum = 1
    for c in range(n):
        pivot = next((r for r in range(c,n) if arr[r][c] % prime), None)
        if pivot is None: return 0
        if pivot != c:
            arr[c],arr[pivot] = arr[pivot],arr[c]
            accum = -accum
        v = arr[c][c] % prime
        accum = (accum * v) % prime
        inv = pow(v,-1,prime)
        for row in range(c+1,n):
            mult = arr[row][c]*inv % prime
            if not mult:continue
            for k in range(c+1,n):
                arr[row][k] = (arr[row][k] - mult*arr[c][k]) % prime
            arr[row][c] = 0
    return accum % prime


def unreduced_burau_minor_mod(p: int, q: int, t: int, prime: int) -> int:
    """Minor det(I-B(beta)), beta=(sigma_1..sigma_(p-1))^q.

    Unreduced positive Artin generator block [[1-t,t],[1,0]].
    With this convention the minor equals t^(p-1)*Delta_torus(t),
    including polynomial normalization, for coprime positive p,q.
    """
    b = [[int(i == j) for j in range(p)] for i in range(p)]
    for _ in range(q):
        for i in range(p-1):
            for r in range(p):
                a, v = b[r][i], b[r][i+1]
                b[r][i] = ((1-t)*a + v) % prime
                b[r][i+1] = (t*a) % prime
    minor = [[(int(r==c) - b[r][c]) % prime for c in range(p-1)] for r in range(p-1)]
    return modular_det(minor, prime)


def analytic_braid_screen(rec: dict) -> dict:
    """Separate braid algebra reference: NEVER a certificate for the XYZ curve."""
    if rec.get('family') not in TORUS_FAMILIES:
        return {'status':'NOT_APPLICABLE','geometric_independence':False}
    p, q = int(rec['p']), int(rec['q'])
    c = torus_polynomial_coefficients(p, q)
    checks=[]
    for prime in (1000003, 1000033):
        for t in (2,3,7):
            expected = (pow(t,p-1,prime) *
                        sum(co * pow(t,i,prime) for i,co in enumerate(c))) % prime
            actual = unreduced_burau_minor_mod(p,q,t,prime)
            checks.append({'prime':prime,'t_mod_prime':t,
                           'reference_mod_prime':expected,'burau_minor_mod_prime':actual,
                           'match':actual==expected})
    return {'status':'PASS_BRAID_REFERENCE_ONLY' if all(x['match'] for x in checks)
            else 'FAIL_BRAID_ALGEBRA','braid':'(sigma_1...sigma_(p-1))^q',
            'p':p,'q':q, 'torus_alexander_coefficients':c,
            'prime_field_checks':checks,
            'geometric_independence':False,
            'note':'Both references use declared p,q, not independent XYZ topology.'}


def normalized_alexander(expr) -> list[int]:
    """Remove multiplication by ±t^k from pyknotid's Laurent polynomial."""
    import sympy as sp
    t = sp.symbols('t')
    rational = sp.cancel(sp.together(expr))
    numer,denom = sp.fraction(rational)
    numerator_poly = sp.Poly(numer, t)
    denominator_poly = sp.Poly(denom, t)
    if len(denominator_poly.terms()) != 1:
        raise QualificationError('provider returned a non-Laurent rational Alexander result')
    scalar = denominator_poly.terms()[0][1]
    coefficients = []
    for value in reversed(numerator_poly.all_coeffs()):
        q = sp.N(value/scalar, 22)
        if not q.is_real:
            raise QualificationError('provider returned complex Alexander coefficients')
        f = float(q)
        if not math.isfinite(f) or abs(f-round(f))>1e-6:
            raise QualificationError(f'nonintegral Alexander coefficient: {q}')
        coefficients.append(int(round(f)))
    while coefficients and coefficients[0]==0:coefficients.pop(0)
    while coefficients and coefficients[-1]==0:coefficients.pop()
    if not coefficients:raise QualificationError('identically zero Alexander polynomial')
    value_at_one=sum(coefficients)
    if value_at_one==-1:coefficients=[-c for c in coefficients]
    if abs(value_at_one)!=1:
        raise QualificationError('Alexander polynomial failed Delta(1)=1 normalization')
    return coefficients


def independent_geometry_invariants(points: np.ndarray) -> dict:
    """Measured from a transformed polygon, not declared knot or torus params."""
    with _pyknotid_numpy_legacy_compatibility():
        import sympy as sp
        from pyknotid.spacecurves import Knot
        knot = Knot(points, verbose=False)
        pol = knot.alexander_polynomial(sp.symbols('t'))
        v3 = knot.vassiliev_degree_3(try_cython=False)
    fv3 = float(np.real(v3))
    if not math.isfinite(fv3) or abs(fv3-round(fv3)) > 1e-6:
        raise QualificationError('non-integer Vassiliev degree-3 result')
    return {'alexander_coefficients':normalized_alexander(pol),
            'vassiliev_3':int(round(fv3))}


# Primary projective orientations are frozen from v0.2.4: NEVER silently replace.
# Supplementary orientations are PREDECLARED for diagnostics only, and excluded
# from any PASS decision.  They must not be tuned to rescue a failed seed.
PROJECTION_ANGLES = ((0.37, 0.71), (0.63, 1.17), (0.91, 0.43), (1.29, 0.87))
PRIMARY_PROJECTIONS = (0, 1)
DIAGNOSTIC_PROJECTIONS = (2, 3)
# Heuristics only; their statuses never change the certification decision.
MIN_CROSSING_SIN = 1e-5
MIN_DEPTH_DIAMETER_RATIO = 1e-6


def rotation_for_projection(index: int) -> np.ndarray:
    a, b = PROJECTION_ANGLES[index]
    ca,sa,cb,sb=math.cos(a),math.sin(a),math.cos(b),math.sin(b)
    rz=np.array([[ca,-sa,0],[sa,ca,0],[0,0,1.]])
    rx=np.array([[1.,0,0],[0,cb,-sb],[0,sb,cb]])
    return rx@rz


def projected_crossing_diagnostics(points:np.ndarray)->dict:
    """Recalculate geometrical 2D segment crossings independently of pyknotid.

    Crossing count, normalized vertical/depth separation and |sin(theta)|
    are projective numerical diagnostics, NOT complete knot invariants.  This
    routine intentionally uses no declared knot identity and no provider output.
    Exact adjacent polygon segments (including cyclic pair) are excluded.
    """
    points=np.asarray(points,dtype=float)
    if points.ndim!=2 or points.shape[1]!=3 or len(points)<5 or not np.isfinite(points).all():
        raise QualificationError('invalid polygon for projection diagnostic')
    n=len(points)
    start=points
    vec=np.roll(points,-1,axis=0)-points
    a=start[:,:2]; u=vec[:,:2]
    ends=a+u
    mins=np.minimum(a,ends); maxs=np.maximum(a,ends)
    diag=float(np.linalg.norm(np.ptp(points,axis=0)))
    if diag==0:raise QualificationError('degenerate polygon for projection diagnostic')
    crossings=0
    min_depth=float('inf');min_sine=float('inf')
    low_angle=0;low_depth=0; near_endpoints=0
    # BBox query limits algebra to geometrically plausible pairs; vectorized
    # candidate j ranges keep memory bounded (O(N)).  No crossing simplification.
    for i in range(n-2):
        j=np.arange(i+2,n if i>0 else n-1,dtype=int)
        overlap=((mins[j,0]<=maxs[i,0])&(maxs[j,0]>=mins[i,0])&
                 (mins[j,1]<=maxs[i,1])&(maxs[j,1]>=mins[i,1]))
        j=j[overlap]
        if not len(j):continue
        v=u[j]; w=a[j]-a[i]
        det=u[i,0]*v[:,1]-u[i,1]*v[:,0]
        du=np.linalg.norm(u[i]);dv=np.linalg.norm(v,axis=1)
        norm=du*dv
        safe=(np.abs(det)>np.finfo(float).eps*np.maximum(norm,1e-300)*16)
        if not np.any(safe):continue
        j=j[safe];v=v[safe];w=w[safe];det=det[safe];norm=norm[safe]
        ta=(w[:,0]*v[:,1]-w[:,1]*v[:,0])/det
        tb=(w[:,0]*u[i,1]-w[:,1]*u[i,0])/det
        # Strict interior crossings only. An endpoint on a crossing is a
        # separate near-degeneracy and not an unambiguously resolved crossing.
        interior=(ta>0)&(ta<1)&(tb>0)&(tb<1)
        if not np.any(interior):continue
        j=j[interior];ta=ta[interior];tb=tb[interior]
        sine=np.abs(det[interior])/norm[interior]
        depth=np.abs((start[i,2]+ta*vec[i,2])-(start[j,2]+tb*vec[j,2]))/diag
        crossings+=len(j)
        min_depth=min(min_depth,float(np.min(depth)))
        min_sine=min(min_sine,float(np.min(sine)))
        low_angle+=int(np.count_nonzero(sine<MIN_CROSSING_SIN))
        low_depth+=int(np.count_nonzero(depth<MIN_DEPTH_DIAMETER_RATIO))
        near_endpoints+=int(np.count_nonzero(np.minimum.reduce([ta,1-ta,tb,1-tb])<1e-8))
    return {'crossing_count':crossings,
            'min_abs_depth_separation_over_diameter':None if crossings==0 else min_depth,
            'min_abs_sin_crossing_angle':None if crossings==0 else min_sine,
            'near_parallel_crossings':low_angle,'near_depth_coincidence_crossings':low_depth,
            'near_endpoint_crossings':near_endpoints,
            'diagnostic_only':True,
            'geometry_status':'NO_PROJECTED_CROSSINGS' if not crossings else
                'NEAR_DEGENERATE' if low_angle or low_depth or near_endpoints else 'GENERIC_BY_HEURISTIC',
            'threshold_min_sin':MIN_CROSSING_SIN,
            'threshold_min_depth_diameter_ratio':MIN_DEPTH_DIAMETER_RATIO}


def summarize_invariant_observations(obs:list[dict], known:list[int]|None)->dict:
    """v0.2.5 stricter gate assessment; no zero==(-zero) chirality witness."""
    clean={(x['N'],x['projection']):x for x in obs if not x['mirror']}
    mirror={(x['N'],x['projection']):x for x in obs if x['mirror']}
    if not clean or set(clean)!=set(mirror):
        raise QualificationError('incomplete signed projection observations')
    polys={tuple(x['alexander_coefficients']) for x in obs}
    polynomial_ok=len(polys)==1 and (known is None or list(next(iter(polys)))==known)
    clean_v3={k:int(x['vassiliev_3']) for k,x in clean.items()}
    mirror_v3={k:int(x['vassiliev_3']) for k,x in mirror.items()}
    odd_relation=all(v==-mirror_v3[k] for k,v in clean_v3.items())
    stable_v3=len(set(clean_v3.values()))==1
    nonzero_witness=all(v!=0 and mirror_v3[k]!=0 for k,v in clean_v3.items())
    stable_polynomial=len(polys)==1
    g5b='PASS_NONZERO_MIRROR_ODD_DIAGNOSTIC_ONLY' if odd_relation and stable_v3 and nonzero_witness else \
         'UNRESOLVED_ZERO_V3_WITNESS' if odd_relation and not nonzero_witness else \
         'UNRESOLVED_UNSTABLE_V3' if odd_relation else 'FAIL_MIRROR_ODD_RELATION'
    good=polynomial_ok and known is not None and stable_v3 and odd_relation and nonzero_witness
    status='MULTI_INVARIANT_MATCH_NOT_CERTIFIED' if good else \
           'INVARIANT_MISMATCH' if (not polynomial_ok or not stable_v3 or not odd_relation) else \
           'ZERO_V3_UNRESOLVED' if not nonzero_witness else 'NO_REFERENCE_INVARIANT'
    issues=[]
    primary=Counter(clean_v3.values()).most_common(1)[0][0]
    for key,x in sorted(clean.items()):
        if known is not None and x['alexander_coefficients']!=known:
            issues.append({'N':key[0],'projection':key[1], 'kind':'ALEXANDER_MISMATCH',
                           'observed_polynomial':x['alexander_coefficients'],'expected_polynomial':known})
        if clean_v3[key]!=primary:
            issues.append({'N':key[0],'projection':key[1], 'kind':'V3_NONMODAL_VALUE',
                           'observed_v3':clean_v3[key],'modal_v3':primary})
        if clean_v3[key]==0:
            issues.append({'N':key[0],'projection':key[1], 'kind':'ZERO_V3_NO_CHIRALITY_WITNESS'})
        if clean_v3[key]!=-mirror_v3[key]:
            issues.append({'N':key[0],'projection':key[1], 'kind':'MIRROR_ODD_RELATION_FAILURE'})
    return {'G5a_polynomial':'MATCH' if polynomial_ok and known is not None else 'NO_REFERENCE' if polynomial_ok else 'MISMATCH',
            'G5b_mirror_odd':g5b,
            'G5b_signed_v3':next(iter(clean_v3.values())) if stable_v3 else None,
            'G5d_projection_resolution':'PASS' if stable_polynomial and stable_v3 and odd_relation and nonzero_witness else 'FAIL',
            'chirality_evidence':'V3_NONZERO_MIRROR_ODD_NOT_KNOT_ID' if stable_v3 and odd_relation and nonzero_witness else 'UNRESOLVED',
            'status':status,
            'primary_case_issues':issues,
            'zero_v3_witness_count':sum(v==0 for v in clean_v3.values())}


def diagnostic_extra_projections(levels:dict, root:Path, resolutions:tuple[int,...],
                                 primary_issues:list[dict], provider:Callable)->dict:
    """Frozen extra orientations on suspect resolutions; never affect gate result."""
    suspects=sorted({int(x['N']) for x in primary_issues})
    observations=[]
    for n in suspects:
        if n not in resolutions:continue
        rec=levels[n];source=(root/rec['file']).resolve()
        if not source.is_relative_to(root) or hashlib.sha256(source.read_bytes()).hexdigest()!=rec['sha256']:
            raise QualificationError('diagnostic extra projection hash mismatch')
        pts=np.loadtxt(source,dtype=float)
        for proj in DIAGNOSTIC_PROJECTIONS:
            q=pts@rotation_for_projection(proj).T
            case={'N':n,'projection':proj,'angles_rad':list(PROJECTION_ANGLES[proj]),
                  'crossings':projected_crossing_diagnostics(q)}
            for mirrored, data in ((False,q),(True,q*np.array([-1.,1.,1.]))):
                key='mirror' if mirrored else 'original'
                try:
                    result=provider(data)
                    case[key]={'alexander_coefficients':list(result['alexander_coefficients']),
                               'vassiliev_3':int(result['vassiliev_3'])}
                except Exception as e:
                    case[key]={'status':'PROVIDER_ERROR','error':f'{type(e).__name__}: {e}'}
            observations.append(case)
    return {'status':'DIAGNOSTIC_ONLY_NO_GATE_RESCUE',
            'projection_indices':list(DIAGNOSTIC_PROJECTIONS),
            'angles_rad':[list(PROJECTION_ANGLES[i]) for i in DIAGNOSTIC_PROJECTIONS],
            'case_count':len(observations), 'cases':observations,
            'promotion_to_primary_evidence':False}


def extended_g5_screen(registry:dict, report:dict, atlas_root:Path, *,
                       enabled:bool=False, sampling:str='uniform_t',
                       resolutions:tuple[int,...]=(1200,2400),
                       max_crossings:int=12, geometry_provider:Callable|None=None,
                       require_complete:bool=False,
                       projection_diagnostics:bool=True) -> dict:
    base={'schema':SCHEMA,'status':'NOT_RUN','provider':'none',
          'scientific_status':'INVARIANT_SCREEN_ONLY_NOT_CERTIFIED',
          'independent_topology_certified':False,'chirality_certified':False,
          'sampling':sampling,'resolutions':list(resolutions),
          'projection_count':2,'max_crossings':max_crossings,
          'primary_projection_angles_rad':[list(PROJECTION_ANGLES[i]) for i in PRIMARY_PROJECTIONS],
          'extra_projections_predeclared':[list(PROJECTION_ANGLES[i]) for i in DIAGNOSTIC_PROJECTIONS],
          'diagnostic_extra_projections_enabled':bool(projection_diagnostics),
          'diagnostic_extra_projections_can_rescue_g5':False,
          'source_atlas_modified':False,'seed_results':[],
          'analytic_braid_references':[],
          'subgates':{'G5a':'NOT_RUN','G5b':'NOT_RUN','G5c':'NOT_RUN','G5d':'NOT_RUN'}}
    if not enabled:return base
    if sampling not in ('uniform_t','uniform_s_polyline') or max_crossings<3:
        raise QualificationError('invalid extended G5 sampling or complexity guard')
    if len(resolutions)<2 or any(n not in (1200,2400,4800,9600) for n in resolutions):
        raise QualificationError('extended G5 requires at least 2 valid distinct resolutions')
    if len(set(resolutions))!=len(resolutions):
        raise QualificationError('duplicate extended G5 resolution')
    root=Path(atlas_root).resolve()
    base['provider_environment']={'python_executable':sys.executable,
        'numpy_version':np.__version__, 'pyknotid_version':_safe_provider_version(),
        'legacy_numpy_aliases_scoped':True}
    if geometry_provider is None:
        try:
            with _pyknotid_numpy_legacy_compatibility():
                import sympy  # noqa: F401
                from pyknotid.spacecurves import Knot  # noqa: F401
        except ImportError as e:
            base.update(status='PROVIDER_UNAVAILABLE',provider='pyknotid',error=str(e))
            report['gate_results']['G5_EXTENDED']='PROVIDER_UNAVAILABLE'
            return base
    provider=geometry_provider or independent_geometry_invariants
    base['provider']='test-double' if geometry_provider is not None else 'pyknotid'
    grouped={}
    for rec in registry['records']:
        if rec['sampling']==sampling and rec['points'] in resolutions:
            grouped.setdefault(rec['id'], {})[rec['points']]=rec
    error=False; mismatch=False; skipped=False; successful=0
    for seed, levels in sorted(grouped.items()):
        if set(levels)!=set(resolutions):
            raise QualificationError('incomplete multi-resolution G5 levels')
        sample=levels[resolutions[0]]
        known=known_polynomial_reference(sample)
        braid=analytic_braid_screen(sample)
        base['analytic_braid_references'].append({'id':seed, **braid})
        if braid['status']=='FAIL_BRAID_ALGEBRA':mismatch=True
        crossing=expected_crossings(sample)
        row={'id':seed,'expected_topology':sample['knot'],
             'expected_polynomial_coefficients':known,
             'crossing_complexity_reference':crossing,
             'braid_reference_status':braid['status'],
             'status':'UNRESOLVED','observations':[],
             'source_chirality_status':'SOURCE_DECLARED_NOT_CERTIFIED'}
        if crossing is None or crossing>max_crossings:
            row['status']='COST_GUARD_UNRESOLVED' if crossing is not None else 'TOPOLOGY_UNKNOWN_COMPLEXITY_UNRESOLVED'
            row['note']='No provider evaluation; declared crossing budget is not a geometry certificate.'
            skipped=True
            base['seed_results'].append(row)
            continue
        for n in resolutions:
            rec=levels[n];src=(root/rec['file']).resolve()
            if not src.is_relative_to(root) or not src.is_file():
                raise QualificationError('path escape or missing extended G5 source')
            if hashlib.sha256(src.read_bytes()).hexdigest()!=rec['sha256']:
                raise QualificationError('extended G5 source hash mismatch')
            pts=np.loadtxt(src,dtype=float)
            if pts.shape!=(n,3) or not np.isfinite(pts).all():
                raise QualificationError('invalid extended G5 source geometry')
            for proj in range(2):
                q=pts@rotation_for_projection(proj).T
                for mirrored, mat in ((False,q),(True,q * np.array([-1.,1.,1.]))):
                    try:
                        got=provider(mat)
                        coefficients=list(got['alexander_coefficients'])
                        v3=int(got['vassiliev_3'])
                        if not coefficients or not all(isinstance(c,int) for c in coefficients):
                            raise QualificationError('invalid provider polynomial coefficients')
                        row['observations'].append({'N':n,'projection':proj,
                            'mirror':mirrored,'alexander_coefficients':coefficients,'vassiliev_3':v3})
                    except Exception as e:
                        row['status']='PROVIDER_ERROR_UNRESOLVED'
                        row['error']=f'{type(e).__name__}: {e}'
                        error=True
                        break
                if row['status']=='PROVIDER_ERROR_UNRESOLVED':break
            if row['status']=='PROVIDER_ERROR_UNRESOLVED':break
        if row['status']!='PROVIDER_ERROR_UNRESOLVED':
            obs=row['observations']
            assessment=summarize_invariant_observations(obs,known)
            row.update(assessment)
            # Post-failure diagnostics are never fed back into assessment.
            if projection_diagnostics and row['status']!='MULTI_INVARIANT_MATCH_NOT_CERTIFIED':
                row['projection_robustness_diagnostics']={
                    'baseline_crossings':[],
                    'supplementary':{'status':'NOT_RUN'},
                    'frozen_baseline_failure':row['status'],
                    'decision_uses_primary_projections_only':True}
                # Preserve matched controls at *both* original resolutions.
                # Otherwise a bad N=2400/projection=1 could be mistaken for
                # a projection singularity without comparing N=1200.
                cases=[(n,proj) for n in resolutions for proj in PRIMARY_PROJECTIONS]
                for n,proj in cases:
                    rec=levels[n];pts=np.loadtxt(root/rec['file'],dtype=float)
                    q=pts@rotation_for_projection(proj).T
                    row['projection_robustness_diagnostics']['baseline_crossings'].append({
                        'N':n,'projection':proj,'angles_rad':list(PROJECTION_ANGLES[proj]),
                        'crossings':projected_crossing_diagnostics(q)})
                geometries=row['projection_robustness_diagnostics']['baseline_crossings']
                if geometries and all(x['crossings']['geometry_status']=='GENERIC_BY_HEURISTIC' for x in geometries):
                    row['projection_robustness_diagnostics']['interpretation']='PRIMARY_INVARIANT_DISAGREEMENT_WITHOUT_DETECTED_GEOMETRIC_DEGENERACY; investigate provider crossing reductions; diagnostic not root-cause proof'
                else:
                    row['projection_robustness_diagnostics']['interpretation']='PROJECTIVE_GEOMETRIC_WARNING_OR_INSUFFICIENT_INFORMATION'
                if row['primary_case_issues']:
                    row['projection_robustness_diagnostics']['supplementary']=diagnostic_extra_projections(
                        levels,root,resolutions,row['primary_case_issues'],provider)
            if row['status']=='INVARIANT_MISMATCH':mismatch=True
            elif row['status']=='MULTI_INVARIANT_MATCH_NOT_CERTIFIED':successful+=1
            else:skipped=True
        base['seed_results'].append(row)
    base['checked_seeds']=len(grouped)
    base['provider_checked_seeds']=sum(x['status'] not in ('COST_GUARD_UNRESOLVED','TOPOLOGY_UNKNOWN_COMPLEXITY_UNRESOLVED') for x in base['seed_results'])
    base['successful_multi_invariant_seeds']=successful
    base['checked_polygon_projection_cases']=sum(len(x['observations']) for x in base['seed_results'])
    base['complexity_skipped_seeds']=sum(x['status'] in ('COST_GUARD_UNRESOLVED','TOPOLOGY_UNKNOWN_COMPLEXITY_UNRESOLVED') for x in base['seed_results'])
    braid_statuses=[r['status'] for r in base['analytic_braid_references'] if r['status']!='NOT_APPLICABLE']
    base['subgates']['G5c']='PASS_REFERENCE_ONLY' if braid_statuses and all(x=='PASS_BRAID_REFERENCE_ONLY' for x in braid_statuses) else 'FAIL' if mismatch and 'FAIL_BRAID_ALGEBRA' in braid_statuses else 'NOT_APPLICABLE'
    if mismatch:base['status']='FAIL_INVARIANT_SCREEN'
    elif error or skipped:base['status']='PARTIAL_UNRESOLVED'
    else:base['status']='MULTI_INVARIANT_SCREEN_ONLY_NOT_CERTIFIED'
    tested = [r for r in base['seed_results'] if r['observations']]
    base['subgates']['G5a']='PASS_SCREEN_NOT_CERTIFIED' if tested and all(r.get('G5a_polynomial')=='MATCH' for r in tested) else 'PARTIAL_UNRESOLVED' if tested else 'NOT_RUN'
    base['subgates']['G5b']='PASS_MIRROR_DIAGNOSTIC_ONLY' if tested and all(r.get('G5b_mirror_odd')=='PASS_NONZERO_MIRROR_ODD_DIAGNOSTIC_ONLY' for r in tested) else 'PARTIAL_UNRESOLVED' if tested else 'NOT_RUN'
    base['subgates']['G5d']='PASS_TESTED_CASES_ONLY' if tested and all(r.get('G5d_projection_resolution')=='PASS' for r in tested) else 'PARTIAL_UNRESOLVED' if tested else 'NOT_RUN'
    report['gate_results']['G5A_FULL_ALEXANDER']=base['subgates']['G5a']
    report['gate_results']['G5B_VASSILIEV3_CHIRALITY']=base['subgates']['G5b']
    report['gate_results']['G5C_TORUS_BRAID_REFERENCE']=base['subgates']['G5c']
    report['gate_results']['G5D_RESOLUTION_PROJECTION']=base['subgates']['G5d']
    report['gate_results']['G5_EXTENDED']=base['status']
    return base
