#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_rodin_guide_stl.py

Parametric generator for a toroidal winding guide ("mold") intended to help weave
a bidirectional 3‑phase Rodin-style coil (6 interleaved windings, 120° phase offset).
The guide provides:
  • A printable toroidal frame (annulus with rectangular cross-section)
  • Two concentric rings of through-holes (12 nodes each) for routing wire top↔bottom
  • Two shallow top grooves (optional) aligned with the hole rings for wire seating
  • Six start markers on the outer rim at 0,60,120,180,240,300 degrees

No external boolean engine is required: geometry is built via an SDF and extracted
with marching cubes.

Units: millimeters (mm). STL is unitless; slicers typically interpret as mm.

Dependencies: numpy, scikit-image, trimesh
"""

import math
import numpy as np
import trimesh
from skimage.measure import marching_cubes


def sd_ring_annulus(x, y, z, r_in, r_out, h):
    """SDF of an annulus (ring) with rectangular cross-section."""
    r = np.sqrt(x * x + y * y)
    sd_outer = r - r_out          # <=0 inside outer cylinder
    sd_inner = r_in - r           # <=0 when r >= r_in (outside inner cylinder)
    sd_radial = np.maximum(sd_outer, sd_inner)
    sd_z = np.abs(z) - h / 2.0
    return np.maximum(sd_radial, sd_z)


def sd_cylinder_z(x, y, z, cx, cy, radius):
    """SDF of an infinite cylinder oriented along +z."""
    return np.sqrt((x - cx) ** 2 + (y - cy) ** 2) - radius


def sd_band_top_groove(x, y, z, r_g, w, z_mid, d):
    """SDF of a shallow ring-band groove near the top surface."""
    r = np.sqrt(x * x + y * y)
    sd_band = np.abs(r - r_g) - w / 2.0
    sd_slab = np.abs(z - z_mid) - d / 2.0
    return np.maximum(sd_band, sd_slab)


def sd_union(sds):
    sd = sds[0]
    for s in sds[1:]:
        sd = np.minimum(sd, s)
    return sd


def make_guide_sdf(X, Y, Z,
                   outer_d=90.0, inner_d=42.0, height=25.0,
                   hole_d=3.2, n_nodes=12,
                   hole_r_factors=(0.36, 0.64),
                   groove=True, groove_w=3.4, groove_d=1.4,
                   markers=True, marker_d=3.0, marker_h=1.0):
    """Build final SDF (negative = inside solid)."""
    r_out = outer_d / 2.0
    r_in = inner_d / 2.0
    h = height

    # Base ring
    sd = sd_ring_annulus(X, Y, Z, r_in, r_out, h)

    # Through-holes (two concentric rings, 12 nodes each by default)
    dr = (r_out - r_in)
    hole_rs = [r_in + f * dr for f in hole_r_factors]
    hole_r = hole_d / 2.0

    holes = []
    for rg in hole_rs:
        for k in range(n_nodes):
            theta = 2 * math.pi * k / n_nodes
            cx = rg * math.cos(theta)
            cy = rg * math.sin(theta)
            holes.append(sd_cylinder_z(X, Y, Z, cx, cy, hole_r))

    sd_holes = sd_union(holes)
    sd = np.maximum(sd, -sd_holes)  # subtract holes

    # Optional top grooves to seat wire along each hole radius
    if groove:
        grooves = []
        z_mid = h / 2.0 - groove_d / 2.0
        for rg in hole_rs:
            grooves.append(sd_band_top_groove(X, Y, Z, rg, groove_w, z_mid, groove_d))
        sd_grooves = sd_union(grooves)
        sd = np.maximum(sd, -sd_grooves)  # subtract groove volume

    # Optional 6 start markers (bumps) on the outer rim
    if markers:
        bumps = []
        rb = r_out - 2.5
        zc = h / 2.0 + marker_h / 2.0 - 0.05  # slight overlap for union
        br = marker_d / 2.0
        for k in range(6):
            theta = 2 * math.pi * k / 6
            cx = rb * math.cos(theta)
            cy = rb * math.sin(theta)
            sd_cyl = sd_cylinder_z(X, Y, Z, cx, cy, br)
            sd_slab = np.abs(Z - zc) - marker_h / 2.0
            bumps.append(np.maximum(sd_cyl, sd_slab))
        sd_bumps = sd_union(bumps)
        sd = np.minimum(sd, sd_bumps)  # union with base

    return sd


def sdf_to_mesh(sd, pitch, origin_xyz):
    verts, faces, *_ = marching_cubes(sd, level=0.0, spacing=(pitch, pitch, pitch))
    verts = verts + np.array(origin_xyz, dtype=float)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    return mesh


def generate(out_stl="rodin_guide.stl",
             outer_d=90.0, inner_d=42.0, height=25.0,
             hole_d=3.2, pitch=0.6):
    # Bounding box (include marker bumps)
    r_out = outer_d / 2.0
    zmax = height / 2.0 + 1.5
    margin = 2.0
    bounds = np.array([[-r_out - margin, -r_out - margin, -zmax - margin],
                       [ r_out + margin,  r_out + margin,  zmax + margin]])

    xs = np.arange(bounds[0, 0], bounds[1, 0] + pitch, pitch)
    ys = np.arange(bounds[0, 1], bounds[1, 1] + pitch, pitch)
    zs = np.arange(bounds[0, 2], bounds[1, 2] + pitch, pitch)

    X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')

    sd = make_guide_sdf(
        X, Y, Z,
        outer_d=outer_d, inner_d=inner_d, height=height,
        hole_d=hole_d,
        n_nodes=12,
        hole_r_factors=(0.36, 0.64),
        groove=True, groove_w=3.4, groove_d=1.4,
        markers=True, marker_d=3.0, marker_h=1.0
    )

    mesh = sdf_to_mesh(sd, pitch=pitch, origin_xyz=(xs[0], ys[0], zs[0]))
    mesh.export(out_stl)
    return mesh


if __name__ == "__main__":
    m = generate(out_stl="rodin_3phase_6coil_guide_90mm.stl")
    print("Wrote:", "rodin_3phase_6coil_guide_90mm.stl")
    print("Watertight:", m.is_watertight)
    print("Extents (mm):", m.extents)