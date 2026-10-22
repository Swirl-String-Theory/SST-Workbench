"""A003 v0.2.7: temporary, version-guarded scale-invariant pyknotid crossing fix.

Does not edit installed pyknotid.  Single-threaded diagnostic control: patches
Python 0.5.3 helper and SpaceCurve dispatch inside try/finally, restores both.
The target is the unnormalised abs(cross)<1e-5 check in the Python fallback.
"""
from __future__ import annotations
from contextlib import contextmanager
import hashlib
import importlib.metadata
import inspect
import math
import re
import threading
from typing import Iterator

ANGULAR_SINE_TOLERANCE = 1e-8
EXPECTED_PYKNOTID_VERSION = '0.5.3'
_LOCK = threading.RLock()


def scale_invariant_intersection(px, py, dpx, dpy, qx, qy, dqx, dqy):
    """Strict interior 2-D crossing with dimensionless parallelism cutoff.

    Preserve 0.5.3's strict (0,1) parametric intervals and its return forms.
    A zero projected segment is a diagnostic nonintersection, never a divide-by-zero.
    """
    vals=(px,py,dpx,dpy,qx,qy,dqx,dqy)
    if not all(math.isfinite(float(x)) for x in vals):
        raise ValueError('non-finite projected segment coordinate')
    len_p=math.hypot(dpx,dpy)
    len_q=math.hypot(dqx,dqy)
    if not len_p or not len_q:return (0,0.,0.)
    cross=dpx*dqy-dpy*dqx
    if abs(cross) < ANGULAR_SINE_TOLERANCE*len_p*len_q:
        return (0,0.,0.)
    t=((qx-px)*dqy-(qy-py)*dqx)/cross
    if 0.0<t<1.0:
        u=((qx-px)*dpy-(qy-py)*dpx)/cross
        if 0.0<u<1.0:
            return (1,t,u)
    return (0,-1.,-1.)


def cutoff_report(u,v):
    """Numerical control independent of provider availability."""
    cp=float(u[0]*v[1]-u[1]*v[0]);length_product=math.hypot(*u)*math.hypot(*v)
    sine=abs(cp)/length_product if length_product else None
    return {'raw_abs_cross_product':abs(cp),'normalized_abs_sin':sine,
            'stock_guard_rejects':abs(cp)<1e-5,
            'corrected_guard_rejects':sine is None or sine < ANGULAR_SINE_TOLERANCE}


@contextmanager
def scoped_pyknotid_crossing_fix() -> Iterator[dict]:
    """Ensure *all* Knot crossing entrypoints take the patched Python path.

    `Knot.alexander_polynomial()` calls Knot.gauss_code(), which defaults to
    SpaceCurve.raw_crossings(try_cython=True).  Patching only helpers is
    ineffective when compiled chelpers is available; temporarily forcing
    try_cython=False makes that path reproducible without touching site-packages.
    """
    with _LOCK:
        version=importlib.metadata.version('pyknotid')
        if version!=EXPECTED_PYKNOTID_VERSION:
            raise RuntimeError(f'Unsupported pyknotid version {version}; expected {EXPECTED_PYKNOTID_VERSION}')
        from pyknotid.spacecurves import helpers
        from pyknotid.spacecurves.spacecurve import SpaceCurve
        original=helpers.do_vectors_intersect
        original_raw=SpaceCurve.raw_crossings
        source=inspect.getsource(original)
        guard_pattern=r'if\s+abs\(cross_product\(dpx,\s*dpy,\s*dqx,\s*dqy\)\)\s*<\s*0\.00001\s*:'
        if not re.search(guard_pattern,source):
            raise RuntimeError('Pyknotid helper signature or stock crossing guard differs; refuse unverified patch')
        def forced_python_raw(self,*args,**kwargs):
            # Overrides any Cython path, including explicit try_cython=True.
            kwargs['try_cython']=False
            return original_raw(self,*args,**kwargs)
        if helpers.do_vectors_intersect is not original or SpaceCurve.raw_crossings is not original_raw:
            raise RuntimeError('provider monkeypatch preflight failed')
        meta={'pyknotid_version':version,'stock_helper_sha256':hashlib.sha256(source.encode('utf-8')).hexdigest(),
              'patch':'PYTHON_ONLY_SCOPED_ANGULAR_CROSSING_GUARD','angular_sine_tolerance':ANGULAR_SINE_TOLERANCE,
              'python_raw_crossings_forced':True,'site_packages_modified':False,
              'topology_certification':False}
        helpers.do_vectors_intersect=scale_invariant_intersection
        SpaceCurve.raw_crossings=forced_python_raw
        try:
            yield meta
        finally:
            SpaceCurve.raw_crossings=original_raw
            helpers.do_vectors_intersect=original
            if (SpaceCurve.raw_crossings is not original_raw or helpers.do_vectors_intersect is not original):
                raise RuntimeError('FAILED TO RESTORE PYKNOTID CROSSING PATCH')


@contextmanager
def scoped_pyknotid_python_backend() -> Iterator[dict]:
    """Control: run unmodified 0.5.3 Python crossing helper, never Cython.

    Both stock and corrected routes must use the same Python crossing backend;
    otherwise a Cython/Python implementation difference is confounded with
    the dimensional tolerance change.
    """
    with _LOCK:
        version=importlib.metadata.version('pyknotid')
        if version!=EXPECTED_PYKNOTID_VERSION:
            raise RuntimeError(f'Unsupported pyknotid version {version}; expected {EXPECTED_PYKNOTID_VERSION}')
        from pyknotid.spacecurves import helpers
        from pyknotid.spacecurves.spacecurve import SpaceCurve
        original=SpaceCurve.raw_crossings
        source=inspect.getsource(helpers.do_vectors_intersect)
        if not re.search(r'if\s+abs\(cross_product\(dpx,\s*dpy,\s*dqx,\s*dqy\)\)\s*<\s*0\.00001\s*:',source):
            raise RuntimeError('Stock Python 0.5.3 crossing guard not recognized')
        def force(self,*args,**kwargs):
            kwargs['try_cython']=False
            return original(self,*args,**kwargs)
        SpaceCurve.raw_crossings=force
        try:
            yield {'backend':'PYTHON_HELPERS_0.5.3_UNMODIFIED',
                   'helper_sha256':hashlib.sha256(source.encode()).hexdigest(),
                   'site_packages_modified':False}
        finally:
            SpaceCurve.raw_crossings=original
            if SpaceCurve.raw_crossings is not original:
                raise RuntimeError('Stock Python backend dispatch not restored')
