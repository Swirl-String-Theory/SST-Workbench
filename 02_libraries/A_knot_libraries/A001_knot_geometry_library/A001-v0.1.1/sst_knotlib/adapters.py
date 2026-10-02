from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict
import numpy as np
from .geometry import resample_closed
from .diagnostics import qualify_seed, convergence_report
from .blind import geometry_sha256


def prepare_for_falsifier(points: np.ndarray, *, core_radius: float, n: int = 512,
                           source_family: str = 'unknown', source_parameters: Dict[str,Any] | None = None,
                           convergence_levels=(256,512,1024)):
    """Canonical pre-dynamics adapter used by downstream falsifiers.

    Returns immutable-style geometry + provenance. This routine performs no dynamics and no outcome-based selection.
    """
    p=resample_closed(points,n)
    q=qualify_seed(p,core_radius=core_radius,n=n)
    conv=convergence_report(p,levels=convergence_levels)
    provenance={
        'geometry_library':'sst-knot-geometry/0.1.0',
        'source_family':source_family,
        'source_parameters':source_parameters or {},
        'resample_N':n,
        'core_radius':core_radius,
        'geometry_sha256':geometry_sha256(p),
        'qualification':q,
        'convergence':conv,
    }
    return p,provenance
