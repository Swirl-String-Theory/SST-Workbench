from __future__ import annotations
import contextlib
import io
import importlib
import importlib.metadata
import shutil
from typing import Any
import numpy as np
from ..models import CertificationResult, TopologyReference
from ..registry import KAtlasSnapshot, normalize_knot_id


def _pkg_version(name):
    try: return importlib.metadata.version(name)
    except Exception: return None


def _module_capability(module_name, attribute):
    try:
        m=importlib.import_module(module_name)
        return hasattr(m,attribute)
    except Exception:
        return False


def provider_status() -> dict:
    rows={
        'internal': {'available':True,'role':'geometry, braid closure, KAtlas snapshot integrity','bundled':True},
        'pyknotid': {'available':importlib.util.find_spec('pyknotid') is not None,'version':_pkg_version('pyknotid'),'role':'space-curve topology identification/invariants','bundled':False,'license':'MIT'},
        'spherogram': {'available':_module_capability('spherogram','Link'),'version':_pkg_version('spherogram'),'role':'diagram/DT/braid independent topology cross-check','bundled':False,'license':'GPLv2+'},
        'snappy': {'available':_module_capability('snappy','Manifold'),'version':_pkg_version('snappy'),'role':'hyperbolic complement cross-check','bundled':False,'license':'GPLv2+'},
        'knotplot': {'available':bool(shutil.which('knotplot') or shutil.which('KnotPlot')),'path':shutil.which('knotplot') or shutil.which('KnotPlot'),'role':'external visualization/relaxation and independent exported invariants','bundled':False,'license':'external/proprietary; not redistributed'},
        'ridgerunner': {'available':bool(shutil.which('ridgerunner')),'path':shutil.which('ridgerunner'),'role':'external constrained ropelength relaxation; VECT/XYZ output is importable','bundled':False,'license':'external; not redistributed by this library'},
    }
    return rows


def _certify_pyknotid(points: np.ndarray, ref: TopologyReference) -> CertificationResult:
    try:
        from pyknotid.spacecurves import Knot
    except Exception as e:
        return CertificationResult('UNVERIFIED',ref.knot_id,'pyknotid',notes=[f'provider unavailable: {e}'])
    try:
        # pyknotid can be noisy; capture logs so a falsifier output remains machine-readable.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try: k=Knot(np.asarray(points,float),verbose=False)
            except TypeError: k=Knot(np.asarray(points,float))
            ids=k.identify()
            determinant=None
            try: determinant=int(round(float(k.determinant())))
            except Exception: pass
        names=[]
        for obj in ids or []:
            txt=str(obj)
            # Typical pyknotid repr contains '3_1'. Preserve raw text as well.
            names.append(txt)
        expected=ref.knot_id
        normalized=[normalize_knot_id(x.replace('<Knot ','').replace('>','').strip()) for x in names]
        id_match=expected in normalized or any(expected in x for x in names)
        det_match=(ref.determinant is None or determinant is None or determinant==ref.determinant)
        status='CERTIFIED' if id_match and det_match else 'MISMATCH'
        return CertificationResult(status,expected,'pyknotid',
            observed={'identify_raw':names,'identify_normalized':normalized,'determinant':determinant},
            reference={'determinant':ref.determinant,'dt':list(ref.dt) if ref.dt else None},
            checks={'identity_match':id_match,'determinant_compatible':det_match},
            notes=['Certification depends on pyknotid projection/simplification and its catalogue.'])
    except Exception as e:
        return CertificationResult('ERROR',ref.knot_id,'pyknotid',notes=[f'{type(e).__name__}: {e}'])


def certify_geometry(points: np.ndarray, expected_topology: str, *, provider: str='auto', registry: KAtlasSnapshot|None=None) -> CertificationResult:
    registry=registry or KAtlasSnapshot()
    kid=normalize_knot_id(expected_topology)
    registered=registry.has(kid)
    ref=registry.get(kid) if registered else TopologyReference(knot_id=kid,source='expected topology label; no local KAtlas record')
    p=provider.lower()
    if p=='auto':
        if provider_status()['pyknotid']['available']: p='pyknotid'
        else:
            status='UNVERIFIED' if registered else 'NOT_REGISTERED'
            return CertificationResult(status,kid,'none',reference=ref.to_dict(),notes=[
                'No installed space-curve topology provider. Filename/metadata is treated only as expected topology.',
                'Install pyknotid to certify arbitrary catalogue knots; the bundled KAtlas snapshot is intentionally small and immutable.'
            ])
    if p=='pyknotid': return _certify_pyknotid(points,ref)
    if p in {'none','reference-only'}:
        return CertificationResult('UNVERIFIED',kid,p,reference=ref.to_dict(),notes=['reference-only mode does not certify a 3D geometry'])
    return CertificationResult('ERROR',kid,p,reference=ref.to_dict(),notes=[f'unknown geometry certification provider: {provider}'])


def crosscheck_reference(knot_id: str, *, registry: KAtlasSnapshot|None=None) -> dict:
    """Cross-check immutable KAtlas metadata with optional independent packages.

    This validates reference metadata/providers, not a user XYZ geometry.
    """
    registry=registry or KAtlasSnapshot(); ref=registry.get(knot_id); out={'knot_id':ref.knot_id,'reference':ref.to_dict(),'providers':{}}
    st=provider_status()
    if st['spherogram']['available']:
        try:
            from spherogram import Link
            L=Link(ref.knot_id)
            det=None
            try: det=int(L.determinant())
            except Exception: pass
            out['providers']['spherogram']={'status':'OK','determinant':det,'determinant_match': ref.determinant is None or det is None or det==ref.determinant}
        except Exception as e: out['providers']['spherogram']={'status':'ERROR','error':f'{type(e).__name__}: {e}'}
    else: out['providers']['spherogram']={'status':'UNAVAILABLE'}
    if st['snappy']['available']:
        try:
            import snappy
            M=snappy.Manifold(ref.knot_id)
            vol=float(M.volume())
            match=(ref.hyperbolic_volume is None or abs(vol-ref.hyperbolic_volume)<5e-4)
            out['providers']['snappy']={'status':'OK','volume':vol,'volume_match':match}
        except Exception as e: out['providers']['snappy']={'status':'ERROR','error':f'{type(e).__name__}: {e}'}
    else: out['providers']['snappy']={'status':'UNAVAILABLE'}
    return out
