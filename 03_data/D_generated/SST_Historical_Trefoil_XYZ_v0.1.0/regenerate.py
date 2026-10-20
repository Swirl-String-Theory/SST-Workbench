#!/usr/bin/env python3
""" Generate 2015 historical trefoil XYZ geometries and their chirality/orientation variants --> headerless, three-column XYZ seeds.

Original mathematical seeds:
A: (cos(t)+1.5*cos(2t), sin(t)-1.5*sin(2t), 0.35*sin(3t))
B: ((2+cos(3t))*cos(2t), (2+cos(3t))*sin(2t), sin(3t))
with 0 <= t < 2*pi.

For each seed and each resolution N, write:
orig_ccw      original chirality, natural t direction
orig_cw       original chirality, reversed vertex order
mirrorX_ccw   opposite chirality, natural t direction
mirrorX_cw    opposite chirality, reversed vertex order

"cw" and "ccw" are traversal labels relative to the *parameter direction*,
NOT an absolute geometric definition of clockwise in 3D (which requires a view).
Reflection x -> -x changes chirality; reversing vertices does not.

Geometry-only seeds: no vortex core, circulation, density, flow or phase clock.
Files use three headerless ASCII columns x y z, without a duplicate endpoint.

Version: 0.1.0. Geometry only: no physical core radius, circulation or Euler/PKLSA solution.
N=600 and 1200, equal arc-length sampling, no duplicate endpoint, original coordinate units.
Dependencies: numpy, scipy.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.integrate import cumulative_trapezoid, quad
from scipy.interpolate import PchipInterpolator

OUT = Path(__file__).resolve().parent
TWO_PI = 2.0 * np.pi
SIZES = (600, 1200, 2400, 4800, 9600)
GRID_N = 262144


def coordinates(name: str, t: np.ndarray) -> np.ndarray:
    if name == "A_Fourier_2015_p32":
        return np.column_stack((np.cos(t) + 1.5 * np.cos(2*t),
                                np.sin(t) - 1.5 * np.sin(2*t),
                                0.35 * np.sin(3*t)))
    if name == "B_Torus_2015_p66":
        r = 2.0 + np.cos(3*t)
        return np.column_stack((r*np.cos(2*t), r*np.sin(2*t), np.sin(3*t)))
    raise ValueError(f"Unknown seed: {name}")


def derivative(name: str, t: np.ndarray) -> np.ndarray:
    if name == "A_Fourier_2015_p32":
        return np.column_stack((-np.sin(t)-3*np.sin(2*t),
                                np.cos(t)-3*np.cos(2*t),
                                1.05*np.cos(3*t)))
    if name == "B_Torus_2015_p66":
        r = 2.0 + np.cos(3*t)
        rp = -3.0*np.sin(3*t)
        return np.column_stack((rp*np.cos(2*t)-2*r*np.sin(2*t),
                                rp*np.sin(2*t)+2*r*np.cos(2*t),
                                3*np.cos(3*t)))
    raise ValueError(f"Unknown seed: {name}")


def length_exact(name: str) -> float:
    def speed(t):
        return float(np.linalg.norm(derivative(name, np.array([t]))[0]))
    return quad(speed, 0, TWO_PI, epsabs=1e-12, epsrel=1e-12, limit=500)[0]


def arc_sample(name: str, n: int) -> tuple[np.ndarray, np.ndarray, float]:
    # Numerically integrate physical arc length of the *exact analytic curve*.
    t_dense = np.linspace(0., TWO_PI, GRID_N+1, endpoint=True)
    v_dense = np.linalg.norm(derivative(name, t_dense), axis=1)
    s_dense = np.concatenate(([0.0], cumulative_trapezoid(v_dense, t_dense)))
    L = float(s_dense[-1])
    target = L*np.arange(n, dtype=float)/n
    ts = np.asarray(PchipInterpolator(s_dense, t_dense)(target))
    return coordinates(name, ts), ts, L


def write_xyz(path: Path, xyz: np.ndarray) -> str:
    # Pure ASCII columns, no count/header, no duplicate endpoint.
    with path.open('w', encoding='ascii', newline='\n') as fh:
        for x, y, z in xyz:
            fh.write(f"{x:.16e} {y:.16e} {z:.16e}\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()

def mirror_x(xyz: np.ndarray) -> np.ndarray:
    q = xyz.copy()
    q[:, 0] *= -1.0
    return q

def reverse_orientation(xyz: np.ndarray) -> np.ndarray:
    return xyz[::-1].copy()

def variant_records(base_xyz: np.ndarray) -> dict[str, np.ndarray]:
    # conventie:
    # ccw = natuurlijke parameter-volgorde
    # cw  = omgekeerde puntvolgorde
    return {
        "orig_ccw": base_xyz,
        "orig_cw": reverse_orientation(base_xyz),
        "mirrorX_ccw": mirror_x(base_xyz),
        "mirrorX_cw": reverse_orientation(mirror_x(base_xyz)),
    }

def run() -> None:
    manifest = {
        'version': '0.1.0',
        'description': 'Historical notebook (2015) geometrical trefoil seeds; NOT validated dynamical PKLSA solutions',
        'point_format': 'headerless ASCII XYZ; space delimited; exactly 3 SI-dimensionless coordinate columns',
        'sampling': 'uniform true parametric arc length by dense quadrature+monotone interpolation',
        'parameter_domain': '[0, 2*pi) with periodic closure implicit; endpoint is NOT repeated',
        'coordinate_units': 'dimensionless historical geometric units, no physical rescaling',
        'assumptions': 'No core radius, density, circulation, physical mass or timestep assigned.',
        'seeds': {},
    }
    for name in ('A_Fourier_2015_p32', 'B_Torus_2015_p66'):
        L_exact = length_exact(name)
        seed = {
            'historical_page': 32 if name.startswith('A_') else 66,
            'original_formula': (
                '[cos(t)+1.5*cos(2t), sin(t)-1.5*sin(2t), 0.35*sin(3t)]'
                if name.startswith('A_') else
                '[(2+cos(3t))*cos(2t), (2+cos(3t))*sin(2t), sin(3t)]'),
            'period': float(TWO_PI),
            'analytic_arclength_nondim': L_exact,
            'files': {},
        }
        assert np.linalg.norm(coordinates(name, np.array([0.]))[0] - coordinates(name, np.array([TWO_PI]))[0]) < 1e-12
        for n in SIZES:
            xyz, ts, L_grid = arc_sample(name, n)
            assert np.all(np.isfinite(xyz))
            assert np.all(np.diff(ts) > 0)
            assert len(xyz) == n
            edges = np.linalg.norm(np.roll(xyz, -1, axis=0) - xyz, axis=1)
            edge_cv = float(np.std(edges)/np.mean(edges))
            assert edge_cv < 1e-3, (name, n, edge_cv)
            assert abs(L_grid - L_exact)/L_exact < 1e-9
            for tag, arr in variant_records(xyz).items():
                edges = np.linalg.norm(np.roll(arr, -1, axis=0) - arr, axis=1)
                edge_cv = float(np.std(edges) / np.mean(edges))

                filename = f"{name}_{tag}_N{n}_arclength.xyz"
                seed['files'][filename] = {
                    'N': n,
                    'variant': tag,
                    'sha256': write_xyz(OUT / filename, arr),
                    'closed_polygon_length_nondim': float(edges.sum()),
                    'mean_closed_edge_length_nondim': float(edges.mean()),
                    'edge_length_relative_sd': edge_cv,
                    'start_xyz': arr[0].tolist(),
                    'last_xyz': arr[-1].tolist(),
                    'closure_edge_length_nondim': float(edges[-1]),
                }
        manifest['seeds'][name] = seed
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k: {'length':v['analytic_arclength_nondim'], 'files': {fn: {'sha256':d['sha256'][:12], 'cv':d['edge_length_relative_sd'], 'polygon_length':d['closed_polygon_length_nondim']} for fn,d in v['files'].items()}} for k,v in manifest['seeds'].items()}, indent=2))

if __name__=='__main__':
    run()