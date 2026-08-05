#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rodin_6coil_guide_generator.py

Generate a 3D-printable winding guide (STL) for a bidirectional 3‑phase Rodin-style coil:
3 phases (0°,120°,240°) + mirrored set = 6 lanes.

This implementation avoids boolean operations AND avoids the optional 'triangle' dependency
by building the base torus as a chain of cylinders.

Outputs:
- rodin_6coil_guide_90mm_pegs.stl
- rodin_6coil_guide_preview.png

Units: millimeters (STL is unitless; interpret as mm in slicer)
"""

import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


# =========================
# Parameters (mm)
# =========================
MAX_SIZE_MM = 90.0

# Base torus (structural ring)
R_MAJOR = 34.0         # major radius
R_TUBE  = 9.0          # tube radius
BASE_SEGMENTS = 240    # number of cylinder segments around the ring

# Winding curve (torus-knot style, per your rodin_double.py)
P = 5
Q = 12
N_PATH = 1800

# 3 phases separated by 120°
PHASE_ANGLES = [0.0, 2*np.pi/3, 4*np.pi/3]

# mirrored partner set (top/bottom)
MIRROR = True

# Guide posts (additive)
POST_RADIUS = 1.0
POST_HEIGHT = 1.8
POST_SECTIONS = 18
POSTS_PER_LANE = 72

# Optional: lane rails (thin tubes) along each lane
ADD_RAILS = True
RAIL_RADIUS = 0.75
RAIL_SECTIONS = 12
RAIL_DECIMATE = 6

OUT_STL = "rodin_6coil_guide_90mm_pegs.stl"
OUT_PNG = "rodin_6coil_guide_preview.png"
OUT_LANES_STL = "rodin_6coil_lane_tubes.stl"
EXPORT_LANES_STL = True


# =========================
# Lane curve definition
# =========================
def torus_lane(R_major: float, r_surface: float, p: int, q: int, t: np.ndarray,
               phase_angle: float = 0.0, mirror: bool = False, offset: float = 0.0) -> np.ndarray:
    """
    (p,q) torus-knot curve on a torus surface:
      x = (R + r cos(q t)) cos(p t)
      y = (R + r cos(q t)) sin(p t)
      z = r sin(q t)

    phase_angle rotates the curve around Z (global 120° separation).
    mirror=True flips z -> -z (gives a distinct "underside" lane).
    """
    theta = p * t + phase_angle
    phi = q * t
    r_eff = r_surface + offset

    x = (R_major + r_eff * np.cos(phi)) * np.cos(theta)
    y = (R_major + r_eff * np.cos(phi)) * np.sin(theta)
    z = r_eff * np.sin(phi)

    if mirror:
        z = -z

    return np.column_stack([x, y, z])


def torus_normal_at_point(pt: np.ndarray, R_major: float) -> np.ndarray:
    """
    Outward unit normal on a ring-torus surface at a point pt:
    n ∝ pt - (R cosθ, R sinθ, 0), θ=atan2(y,x)
    """
    x, y, z = pt
    theta = np.arctan2(y, x)
    center = np.array([R_major*np.cos(theta), R_major*np.sin(theta), 0.0])
    n = pt - center
    norm = np.linalg.norm(n)
    if norm < 1e-9:
        return np.array([1.0, 0.0, 0.0])
    return n / norm


def cylinder_between(a: np.ndarray, b: np.ndarray, radius: float, sections: int) -> trimesh.Trimesh:
    """
    Cylinder whose axis runs from point a to point b.
    """
    v = b - a
    L = float(np.linalg.norm(v))
    if L < 1e-9:
        return trimesh.Trimesh()

    cyl = trimesh.creation.cylinder(radius=radius, height=L, sections=sections)
    cyl.apply_translation([0.0, 0.0, L/2.0])  # base at origin

    vhat = v / L
    R = trimesh.geometry.align_vectors([0, 0, 1], vhat)
    cyl.apply_transform(R)
    cyl.apply_translation(a)
    return cyl


def build_base_torus(R_major: float, r_tube: float, segments: int) -> trimesh.Trimesh:
    """
    Approximate a torus tube by chaining cylinders around a circle.
    """
    ang = np.linspace(0.0, 2*np.pi, segments+1, endpoint=True)
    path = np.column_stack([R_major*np.cos(ang), R_major*np.sin(ang), np.zeros_like(ang)])

    parts = []
    for a, b in zip(path[:-1], path[1:]):
        parts.append(cylinder_between(a, b, radius=r_tube, sections=24))

    mesh = trimesh.util.concatenate(parts)
    mesh.remove_duplicate_faces()
    mesh.remove_degenerate_faces()
    mesh.merge_vertices()
    return mesh


def build_lane_posts(path_pts: np.ndarray, R_major: float,
                     posts_per_lane: int, post_r: float, post_h: float, sections: int) -> list:
    """
    Place outward posts along a lane.
    """
    n = len(path_pts)
    idx = np.linspace(0, n-1, posts_per_lane, dtype=int)
    posts = []
    for i in idx:
        p = path_pts[i]
        nrm = torus_normal_at_point(p, R_major)

        # Make a post from p (base) outward by post_h along nrm
        base = p
        tip = p + nrm * post_h
        post = cylinder_between(base, tip, radius=post_r, sections=sections)
        posts.append(post)
    return posts


def build_lane_rail(path_pts: np.ndarray, rail_r: float, sections: int, decimate: int) -> trimesh.Trimesh:
    """
    Add a thin rail along the lane using chained cylinders (additive).
    """
    pts = path_pts[::max(1, decimate)]
    parts = []
    for a, b in zip(pts[:-1], pts[1:]):
        parts.append(cylinder_between(a, b, radius=rail_r, sections=sections))
    if not parts:
        return trimesh.Trimesh()
    rail = trimesh.util.concatenate(parts)
    rail.remove_duplicate_faces()
    rail.remove_degenerate_faces()
    rail.merge_vertices()
    return rail


def visualize_preview(centerline: np.ndarray, lanes: list, out_png: str):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot(centerline[:, 0], centerline[:, 1], centerline[:, 2], linewidth=1, alpha=0.35, label="torus centerline")

    for name, pts in lanes:
        ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], linewidth=2, alpha=0.85, label=name)

    all_pts = np.vstack([centerline] + [pts for _, pts in lanes])
    mins = all_pts.min(axis=0)
    maxs = all_pts.max(axis=0)
    spans = maxs - mins
    span = float(np.max(spans))
    mid = 0.5 * (mins + maxs)
    ax.set_xlim(mid[0]-span/2, mid[0]+span/2)
    ax.set_ylim(mid[1]-span/2, mid[1]+span/2)
    ax.set_zlim(mid[2]-span/2, mid[2]+span/2)

    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title("6-lane 3-phase + mirrored winding guide (preview)")
    ax.legend(loc="upper left", fontsize=7)
    plt.tight_layout()
    plt.savefig(out_png, dpi=170)
    plt.close(fig)


def main():
    # base torus
    base_torus = build_base_torus(R_MAJOR, R_TUBE, BASE_SEGMENTS)

    # lane paths
    t = np.linspace(0.0, 2*np.pi, N_PATH, endpoint=True)

    lanes = []
    for k, ang in enumerate(PHASE_ANGLES):
        pts_top = torus_lane(R_MAJOR, R_TUBE, P, Q, t, phase_angle=ang, mirror=False)
        lanes.append((f"Phase {k+1} top", pts_top))
        if MIRROR:
            pts_bot = torus_lane(R_MAJOR, R_TUBE, P, Q, t, phase_angle=ang, mirror=True)
            lanes.append((f"Phase {k+1} bottom", pts_bot))

    # build posts and rails
    parts = [base_torus]
    for _, pts in lanes:
        parts.extend(build_lane_posts(pts, R_MAJOR, POSTS_PER_LANE, POST_RADIUS, POST_HEIGHT, POST_SECTIONS))
        if ADD_RAILS:
            parts.append(build_lane_rail(pts, RAIL_RADIUS, RAIL_SECTIONS, RAIL_DECIMATE))

    mesh = trimesh.util.concatenate(parts)
    mesh.remove_duplicate_faces()
    mesh.remove_degenerate_faces()
    mesh.merge_vertices()

        # center whole assembly at origin (keeps bounding box symmetric)
    mesh.apply_translation(-mesh.centroid)
    bounds = mesh.bounds
    ext = bounds[1] - bounds[0]
    print('Bounding box extents after centering (mm):', ext)

    if np.any(ext > MAX_SIZE_MM + 1e-6):
        print("WARNING: exceeds MAX_SIZE_MM; reduce R_MAJOR/R_TUBE/POST_HEIGHT.")

    mesh.export(OUT_STL)
    print("Wrote:", OUT_STL)

    # --- optional export: lane tubes only (for visual checking / separate printing) ---
    if EXPORT_LANES_STL:
        lane_parts = []
        for _, pts in lanes:
            lane_parts.append(build_lane_rail(pts, RAIL_RADIUS, RAIL_SECTIONS, RAIL_DECIMATE))
        lanes_mesh = trimesh.util.concatenate([p for p in lane_parts if p.vertices.shape[0] > 0])
        lanes_mesh.remove_duplicate_faces()
        lanes_mesh.remove_degenerate_faces()
        lanes_mesh.merge_vertices()
        lanes_mesh.apply_translation(-lanes_mesh.centroid)
        lanes_mesh.export(OUT_LANES_STL)
        print("Wrote:", OUT_LANES_STL)


    # preview
    ang = np.linspace(0.0, 2*np.pi, 600, endpoint=True)
    centerline = np.column_stack([R_MAJOR*np.cos(ang), R_MAJOR*np.sin(ang), np.zeros_like(ang)])
    visualize_preview(centerline, lanes, OUT_PNG)
    print("Wrote:", OUT_PNG)


if __name__ == "__main__":
    main()