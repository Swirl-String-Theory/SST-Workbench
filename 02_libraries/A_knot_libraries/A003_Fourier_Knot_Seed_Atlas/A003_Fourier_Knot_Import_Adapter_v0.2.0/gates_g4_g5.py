"""A003 v0.2.0: physical-length hypothesis and independent invariant screens.

Only reference-scale bookkeeping is done in G4. G5 intentionally cannot promote
invariant agreement to a certified knot equivalence or verified chirality.
The atlas and frozen knot library are never edited.
"""
from __future__ import annotations

import copy
import importlib.metadata
import math
from pathlib import Path
from typing import Any

import numpy as np

CANONICAL_RC_M = 1.40897017e-15
SCHEMA_G4 = 'sst.a003.physical-scale-hypothesis/1'
SCHEMA_G5 = 'sst.a003.independent-topology-screen/1'


class QualificationError(ValueError):
    pass


def expected_determinant(rec: dict) -> int | None:
    """Reference necessary invariant only; never sufficient to identify a knot."""
    if rec['family'] == 'torus':
        p, q = int(rec['p']), int(rec['q'])
        if math.gcd(p, q) != 1:
            return None
        # For coprime positive torus parameters: det(T(p,q)) =
        # q (p even), p (q even), 1 (p and q odd).
        return q if p % 2 == 0 else p if q % 2 == 0 else 1
    if rec['family'] == 'twist':
        m = rec.get('m')
        if isinstance(m, int) and m > 0:
            return 2 * m + 1
    return None


def bind_physical_scale(registry: dict, report: dict, *,
                        assumed_core_radius_units: float | None = None,
                        canonical_core_radius_m: float = CANONICAL_RC_M) -> dict:
    """Explicitly map dimensionless geometric centerlines into SI units.

    No core radius is inferred from a centerline. Choosing the dimensionless
    radius is a physical/model hypothesis, not a scientific inference.
    """
    if assumed_core_radius_units is None:
        return {'schema': SCHEMA_G4, 'status': 'NOT_DEFINED',
                'explanation': 'No core radius was assigned in atlas coordinate units.',
                'canonical_reference_core_radius_m': CANONICAL_RC_M}
    if (not math.isfinite(assumed_core_radius_units) or
        assumed_core_radius_units <= 0):
        raise QualificationError('reference-core-radius-units must be positive and finite')
    if (not math.isfinite(canonical_core_radius_m) or
        canonical_core_radius_m <= 0):
        raise QualificationError('physical core radius must be positive and finite')
    factor = canonical_core_radius_m / assumed_core_radius_units
    if factor <= 0 or not math.isfinite(factor):
        raise QualificationError('physical scale factor underflow/overflow')
    for rec in registry['records']:
        # Physical length derived from the actual length measured on source polygons.
        L_coord = rec.get('measured_polyline_length_coordinate_units',
                          rec['polyline_length_coordinate_units'])
        L_si = factor * L_coord
        if not math.isfinite(L_si) or L_si <= 0:
            raise QualificationError('invalid physical length after mapping')
        rec['physical_scale_m_per_unit'] = factor
        rec['physical_length_m'] = L_si
        rec['physical_core_radius_m_assumed'] = canonical_core_radius_m
        rec['physical_core_radius_units_assumed'] = assumed_core_radius_units
        rec['physical_binding_status'] = 'HYPOTHESIS_ONLY'
    report['gate_results']['G4_PHYSICAL_SCALE'] = 'PASS_DIMENSIONAL_HYPOTHESIS_ONLY'
    return {'schema':SCHEMA_G4, 'status':'PASS_DIMENSIONAL_HYPOTHESIS_ONLY',
            'physical_basis':'ASSUMED_CORE_RADIUS_EQUIVALENCE',
            'reference_core_radius_units_assumed': assumed_core_radius_units,
            'canonical_reference_core_radius_m': CANONICAL_RC_M,
            'core_radius_m_assumed':canonical_core_radius_m,
            'meters_per_atlas_unit':factor,
            'length_m_min':min(rec['physical_length_m'] for rec in registry['records']),
            'length_m_max':max(rec['physical_length_m'] for rec in registry['records']),
            'source_geometry_modified':False,
            'geometry_thickness_certified':False,
            'dynamical_self_confinement_certified':False,
            'notes':['No tube or finite-core dynamics is derived by the centerline atlas.',
                     'This binding is a hypothesis: the user supplies the dimensionless core radius.',
                     'No mass, force, or clock calibration follows from a length-unit conversion.']}


def _safe_provider_version() -> str:
    try:
        return importlib.metadata.version('pyknotid')
    except (importlib.metadata.PackageNotFoundError, ValueError):
        return 'unknown'


def _independent_determinant(xyz: np.ndarray) -> int:
    """pyknotid calculates knot determinant from a spatial projection/Gauss code."""
    from pyknotid.spacecurves import Knot
    knot = Knot(xyz, verbose=False)
    det = knot.determinant()
    value = float(np.real(det))
    if not math.isfinite(value) or abs(value - round(value)) > 1e-6:
        raise QualificationError(f'non-integral determinant from provider: {det}')
    return abs(int(round(value)))


def _g5_source_records(registry: dict, *, sample: str, n_values: tuple[int, ...]):
    by_seed = {}
    for rec in registry['records']:
        if rec['sampling'] == sample and rec['points'] in n_values:
            by_seed.setdefault(rec['id'], {})[rec['points']] = rec
    seeds = sorted({rec['id'] for rec in registry['records']})
    for seed in seeds:
        if seed not in by_seed or set(by_seed[seed]) != set(n_values):
            raise QualificationError(f'missing G5 source levels for {seed}')
    return by_seed


def independent_topology_screen(registry: dict, report: dict, *, atlas_root: Path,
                                enabled: bool = False,
                                sample: str = 'uniform_t',
                                n_values: tuple[int, ...] = (1200, 2400),
                                determinant_fn=None) -> dict:
    """G5 runs on the *actual* source polygon, not on formula labels.

    This is an independent Alexander determinant screen, which is a necessary
    but non-complete invariant. It can reject mismatches, but cannot certify
    knot class, embedding isotopy, chirality or finite-core viability.
    A test callback may be injected for mock regressions; reports from such a
    callback must not be confused with an actual provider campaign.
    """
    result={'schema':SCHEMA_G5, 'status':'NOT_RUN', 'provider':'none',
            'independent_topology_certified':False,
            'chirality_certified':False,'checked_seeds':0, 'checked_embedded_curves':0,
            'seed_results':[], 'sample':sample,'resolutions':list(n_values)}
    if not enabled:
        return result
    if sample not in ('uniform_t','uniform_s_polyline'):
        raise QualificationError('unsupported G5 sampling')
    if not n_values or any(x not in (1200, 2400, 4800, 9600) for x in n_values):
        raise QualificationError('unsupported G5 resolution')
    provider = determinant_fn
    is_mock = provider is not None
    if provider is None:
        try:
            from pyknotid.spacecurves import Knot  # noqa: F401
        except ImportError as e:
            result.update(status='PROVIDER_UNAVAILABLE',provider='pyknotid',
                          explanation=str(e),
                          provider_version=_safe_provider_version())
            report['gate_results']['G5_INDEPENDENT_TOPOLOGY']='PROVIDER_UNAVAILABLE'
            return result
        provider = _independent_determinant
    result['provider'] = 'test-double' if is_mock else 'pyknotid'
    result['provider_version'] = None if is_mock else _safe_provider_version()
    result['scientific_boundary'] = (
        'Alexander determinant is not a complete knot invariant and cannot distinguish mirror knots.'
    )
    by_seed = _g5_source_records(registry,sample=sample,n_values=n_values)
    outcome={}
    for seed, levels in sorted(by_seed.items()):
        first=levels[n_values[0]]
        theory=expected_determinant(first)
        row={'id':seed, 'expected_topology':first['knot'],
             'reference_determinant':theory, 'source_n':list(n_values),
             'observed_determinants':{},'status':'UNVERIFIED'}
        for n in n_values:
            rec=levels[n]
            src=(atlas_root/rec['file']).resolve()
            if not src.is_relative_to(atlas_root.resolve()):
                raise QualificationError('G5 path escapes atlas root')
            try:
                # Recheck bytes explicitly before the independent provider sees geometry.
                import hashlib
                if hashlib.sha256(src.read_bytes()).hexdigest()!=rec['sha256']:
                    raise QualificationError(f'G5 SHA256 mismatch for {src.name}')
                pts=np.loadtxt(src,dtype=float)
                if pts.shape!=(n,3) or not np.isfinite(pts).all():
                    raise QualificationError(f'G5 invalid source polygon {src.name}')
                det=int(provider(pts))
                if det<0:raise QualificationError('negative independent determinant')
                row['observed_determinants'][str(n)] = det
            except Exception as e:
                row['error']=f'{type(e).__name__}: {e}'
                row['status']='ERROR'
                break
        if row['status']!='ERROR':
            distinct=set(row['observed_determinants'].values())
            if len(distinct)>1:
                row['status']='RESOLUTION_MISMATCH'
            elif theory is not None and next(iter(distinct))!=theory:
                row['status']='INVARIANT_MISMATCH'
            elif theory is not None:
                row['status']='INVARIANT_MATCH_NOT_CERTIFIED'
            else:
                row['status']='NO_REFERENCE_INVARIANT'
        outcome[seed]=row
    result['seed_results']=list(outcome.values())
    result['checked_seeds']=len(outcome)
    result['checked_embedded_curves']=sum(len(x['observed_determinants']) for x in outcome.values())
    statuses={x['status'] for x in outcome.values()}
    if any(s in statuses for s in ('INVARIANT_MISMATCH','RESOLUTION_MISMATCH')):
        result['status']='FAIL_INVARIANT_SCREEN'
    elif 'ERROR' in statuses or 'NO_REFERENCE_INVARIANT' in statuses:
        result['status']='PARTIAL_UNRESOLVED'
    else:
        result['status']='INVARIANT_SCREEN_ONLY_NOT_CERTIFIED'
    report['gate_results']['G5_INDEPENDENT_TOPOLOGY']=result['status']
    for rec in registry['records']:
        row=outcome.get(rec['id'])
        if row:
            rec['independent_topology_screen_status']=row['status']
            rec['independent_topology_provider']=result['provider']
            rec['chirality_status']='SOURCE_DECLARED_NOT_CERTIFIED'
            # Do not overwrite legacy topology_status UNVERIFIED/NOT_REGISTERED.
    return result
