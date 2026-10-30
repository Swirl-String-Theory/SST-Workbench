"""Read-only, hash-verified seed loader for a FUTURE A075 instance integration.

Does not modify A075-v0.2.7, frozen protocols, or any framework files.
This only returns a verified centerline and exact provenance; it does NOT
turn Ruban's filament delta into A075's Euler Gaussian core parameter.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import numpy as np


def load_ruban_t23(seed_package_root: str | Path, *, n: int = 2048,
                   target_outer_radius: float | None = None,
                   center_z: float = 0.0):
    root = Path(seed_package_root)
    if n not in (2048, 4096):
        raise ValueError('Only shipped arclength N=2048 and N=4096 seeds are admitted')
    if not np.isfinite(center_z):
        raise ValueError('center_z must be finite')
    manifest = json.loads((root / 'SEED_MANIFEST.json').read_text(encoding='utf-8'))
    item = next((x for x in manifest['files']
                 if x['n_vertices'] == n and x['sampling'] == 'equal_arclength'), None)
    if item is None:
        raise ValueError('No matching admitted seed entry')
    path = root / 'seeds' / item['filename']
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('Seed hash mismatch: refusing source')
    points = np.loadtxt(path, comments='#', usecols=(0, 1, 2))
    if points.shape != (n,3) or not np.isfinite(points).all():
        raise ValueError('Invalid geometry array')
    rxy = np.hypot(points[:,0],points[:,1])
    assert max(abs(np.hypot(rxy-1.0,points[:,2])-0.154)) < 1e-12
    factor = 1.0
    if target_outer_radius is not None:
        if not np.isfinite(target_outer_radius) or target_outer_radius <= 0:
            raise ValueError('target_outer_radius must be positive finite')
        factor = float(target_outer_radius) / 1.154
    output = points.copy() * factor
    output[:,2] += float(center_z)
    params = manifest['exact_parameters']
    provenance = {'kind':'ruban_t23','source':'ANALYTICAL_RECONSTRUCTION_NOT_AUTHOR_INITIAL_VERTICES',
        'source_file':path.name,'source_sha256':item['sha256'],
        'n':n,'p_toroidal':2,'q_poloidal':3,'B0_exact':'77/500',
        'scale_factor':factor,'original_R0':1.0,'scaled_R0':factor,
        'scaled_r0':0.154*factor,
        'scaled_ruban_regularization_delta_NOT_EULER_SIGMA':float(params['delta'])*factor,
        'scaled_ruban_effective_xi_NOT_EULER_SIGMA':float(params['xi_over_R0_65d'])*factor,
        'center_z':float(center_z),
        'scientific_note':'Ruban delta is not the A075 Euler finite-core Gaussian width'}
    return output,provenance
