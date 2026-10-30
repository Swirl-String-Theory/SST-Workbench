#!/usr/bin/env python3
"""Generate an analytic, unperturbed Ruban-paper-parameter T(2,3) seed.

This is NOT Ruban's original simulated initial state: his quasi-random
perturbation and full initialization data are unspecified in the paper.

Convention is EXPLICIT: toroidal winding p=2, poloidal winding q=3,
matching A075's pre-existing analytic T(2,3) convention.

The Ruban regularizer delta is solver metadata, never an XYZ coordinate
or an automatically calibrated 3-D Euler Gaussian core.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import numpy as np

B0 = Decimal(77) / Decimal(500)
DELTA = Decimal(1) / Decimal(20)
LAMBDA_EXPR = '(7/5) + (1/2)*ln(200)'
P, Q = 2, 3


def exact_params():
    with localcontext() as ctx:
        ctx.prec = 65
        lam = Decimal(7) / Decimal(5) + Decimal(200).ln() / 2
        xi = (-lam).exp()
        tilde = lam - (Decimal(1) / DELTA).ln()
        return {
            'R0': '1', 'B0': format(B0, 'f'),
            'r0': format(B0, 'f'), 'delta': format(DELTA, 'f'),
            'delta_squared': format(DELTA * DELTA, 'f'),
            'Lambda_expression': LAMBDA_EXPR,
            'Lambda_65d': format(lam, 'f'),
            'xi_over_R0_65d': format(xi, 'f'),
            'tilde_Lambda0_expression': '(7/5)-(1/2)*ln(2)',
            'tilde_Lambda0_65d': format(tilde, 'f'),
            'delta_over_xi_65d': format(DELTA / xi, 'f'),
            'Gamma_model': '2*pi',
            'parameter_system': 'Ruban paper, dimensionless R0=1 and Gamma=2*pi',
        }


def parametrization(n: int, mode: str):
    if n < 128 or not isinstance(n, int):
        raise ValueError('n must be integer >= 128')
    if mode == 'uniform_theta':
        return 2.0 * np.pi * np.arange(n, dtype=np.float64) / n
    if mode != 'equal_arclength':
        raise ValueError('unknown mode')
    # Arc speed of the exact torus parametric curve. Dense quadrature is used
    # ONLY to invert arc length; XYZ are evaluated from the analytic torus,
    # not linearly interpolated between intermediate Cartesian vertices.
    quadrature_n = max(262144, 64 * n)
    t = np.linspace(0.0, 2.0 * np.pi, quadrature_n + 1, dtype=np.float64)
    b = float(B0)
    speed = np.sqrt((P * (1.0 + b * np.cos(Q * t)))**2 + (Q * b)**2)
    delta_s = (speed[1:] + speed[:-1]) * (np.pi / quadrature_n)
    cum = np.empty(quadrature_n + 1, dtype=np.float64)
    cum[0] = 0.0
    cum[1:] = np.cumsum(delta_s)
    theta = np.interp(np.arange(n, dtype=np.float64) * cum[-1] / n, cum, t)
    return theta


def xyz(n: int, mode: str):
    theta = parametrization(n, mode)
    b = float(B0)
    radial = 1.0 + b * np.cos(Q * theta)
    return np.column_stack((radial * np.cos(P * theta),
                            radial * np.sin(P * theta),
                            b * np.sin(Q * theta)))


def check(points, mode):
    if not np.isfinite(points).all() or points.ndim != 2 or points.shape[1] != 3:
        raise AssertionError('nonfinite xyz')
    rho = np.linalg.norm(points[:, :2], axis=1)
    rminor = np.sqrt((rho - 1.0)**2 + points[:, 2]**2)
    err = float(np.max(np.abs(rminor - float(B0))))
    if err > 1.0e-13:
        raise AssertionError(f'minor-radius residual {err} > 1e-13')
    poloidal = np.unwrap(np.arctan2(points[:, 2], rho - 1.0))
    toroidal = np.unwrap(np.arctan2(points[:, 1], points[:, 0]))
    # Phase changes omit the closing segment. Closing segment is well-defined
    # through torus analytical topology; check the integer winding robustly.
    wp = int(np.rint((toroidal[-1] - toroidal[0]) / (2 * np.pi)))
    wq = int(np.rint((poloidal[-1] - poloidal[0]) / (2 * np.pi)))
    if (wp, wq) != (P, Q):
        raise AssertionError(f'unexpected windings {(wp, wq)}')
    steps = np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1)
    if np.min(steps) <= 0:
        raise AssertionError('degenerate segment')
    stat = {
        'n_vertices': len(points),
        'toroidal_winding': wp, 'poloidal_winding': wq,
        'max_torus_minor_radius_residual': err,
        'rminor_min': float(np.min(rminor)),
        'rminor_max': float(np.max(rminor)),
        'segment_min': float(np.min(steps)),
        'segment_max': float(np.max(steps)),
        'segment_ratio_max_to_min': float(np.max(steps) / np.min(steps)),
        'closed_polyline_length': float(np.sum(steps)),
        'closed_curve': True,
        'terminal_point_duplicated': False,
        'source_geometry': 'unperturbed analytic torus, not extracted author simulation points',
        'sampling': mode,
    }
    return stat


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent / 'seeds')
    parser.add_argument('--only', choices=['all', 'primary', 'resolution', 'parameterization'], default='all')
    parser.add_argument('--force', action='store_true', help='Explicitly permit replacing generated seed files')
    args = parser.parse_args()
    variants = {
        'primary': (2048, 'equal_arclength'),
        'resolution': (4096, 'equal_arclength'),
        'parameterization': (2048, 'uniform_theta'),
    }
    selected = variants if args.only == 'all' else {args.only: variants[args.only]}
    args.out.mkdir(parents=True, exist_ok=True)
    # Do not mutate existing files unless explicitly requested.
    planned = [args.out / f'RUBAN_T23_B0_0p154_N{n}_{mode.upper()}.xyz' for n, mode in selected.values()]
    if not args.force and any(p.exists() for p in planned):
        raise FileExistsError('Output seed(s) already exist; use --force only after checking hashes')
    entries = []
    for (role, (n, mode)), dest in zip(selected.items(), planned):
        pts = xyz(n, mode)
        stats = check(pts, mode)
        lines = [
            '# ANALYTIC_RECONSTRUCTION, not original Ruban simulation data',
            '# Source: V. P. Ruban, Long-lived quantum vortex knots (2018), Fig. 3',
            '# T(2,3): toroidal winding 2, poloidal winding 3; positive orientation',
            '# R0=1, r0=77/500, B0=77/500, no perturbation',
            '# delta=1/20 and Lambda=7/5+1/2*ln(200) are SOLVER metadata, NOT XYZ geometry',
            '# x y z (dimensionless units of R0); no repeated closing vertex',
        ]
        lines.extend(f'{x:.17e} {y:.17e} {z:.17e}' for x,y,z in pts)
        dest.write_text('\n'.join(lines) + '\n', encoding='ascii')
        # Read back the actual user format and independently verify.
        recovered = np.loadtxt(dest, comments='#', usecols=(0,1,2))
        if np.max(np.abs(pts-recovered)) > 2.0e-16:
            raise AssertionError('XYZ round-trip error')
        stats['sha256'] = hashlib.sha256(dest.read_bytes()).hexdigest()
        stats['filename'] = dest.name
        stats['role'] = role
        entries.append(stats)
    manifest = {
        'schema': 'SST-RUBAN-T23-ANALYTICAL-SEED-1',
        'classification': 'MATHEMATICAL_CANDIDATE_NOT_VALIDATED_STABLE',
        'reference': {'authors': 'V. P. Ruban', 'title': 'Long-lived quantum vortex knots', 'year': 2018, 'figure': 3,
                      'paper_input_B0': '0.154', 'paper_input_delta': '1/20',
                      'paper_input_Lambda': LAMBDA_EXPR, 'paper_time_shown': '320 (dimensionless)',
                      'source_geometry_vertices_available': False,
                      'paper_random_perturbation_exact_parameters_available': False},
        'geometry_convention': {'p_toroidal': P, 'q_poloidal': Q,
                                'formula': '((1+B0*cos(3*theta))*cos(2*theta), (1+B0*cos(3*theta))*sin(2*theta), B0*sin(3*theta))',
                                'same_convention_as_A075_v0.2.7_analytic_trefoil': True},
        'exact_parameters': exact_params(),
        'note_delta': 'Ruban delta is Biot-Savart filament regularization; NOT A075 Gaussian vorticity sigma.',
        'note_time': 'Do not map t=320 directly to Euler simulation seconds without a scaling derivation.',
        'note_topology': 'Copri​me windings 2,3 and 0<B0<1 define a smooth trefoil on an embedded torus; discrete polygon topology remains numerical approximation.',
        'numpy_version_at_generation': np.__version__,
        'python_version_at_generation': platform.python_version(),
        'files': entries,
    }
    # Only write manifest for full generation (for traceable comprehensive release).
    if args.only == 'all':
        mf = args.out.parent / 'SEED_MANIFEST.json'
        if mf.exists() and not args.force:
            raise FileExistsError('SEED_MANIFEST.json already exists')
        mf.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'files': entries, 'exact_parameters': exact_params()}, indent=2))


if __name__ == '__main__':
    main()
