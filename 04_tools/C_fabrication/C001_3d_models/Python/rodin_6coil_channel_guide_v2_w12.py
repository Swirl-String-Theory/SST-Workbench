#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rodin_6coil_channel_guide_v2.py

"Mold-like" winding guide for a 6-lane Rodin/torus-knot coil:
- 3 phases at 0°,120°,240°
- mirrored (underside) set -> 6 lanes total
- additive fences (two walls per lane) create channels

This v2 version:
- builds a watertight base torus using trimesh.creation.revolve (no 'triangle' dependency)
- exports FULL + TOP + BOTTOM by slicing *each watertight part* and concatenating

Outputs (mm):
- rodin_6coil_channel_guide_full_v2.stl
- rodin_6coil_channel_guide_top_v2.stl
- rodin_6coil_channel_guide_bottom_v2.stl
- rodin_6coil_channel_guide_preview_v2.png

Deps:
  pip install trimesh numpy matplotlib
"""

import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from trimesh.intersections import slice_mesh_plane


# =========================
# Envelope and torus (mm)
# =========================
MAX_XY = 90.0
MAX_Z = 90.0

R_MAJOR = 33.53      # mm (tuned so fences stay within 90 mm XY)
R_TUBE  = 9.0        # mm
TORUS_PROFILE_SAMPLES = 160
TORUS_SECTIONS = 240

# Lane curve (torus-knot style)
P = 5
Q = 12
N_PATH = 2600

PHASE_ANGLES = [0.0, 2*np.pi/3, 4*np.pi/3]
MIRROR = True

# Channel sizing (adjust after you choose wire)
WIRE_DIAMETER = 1.2       # mm baseline (typical enamel copper)
WIRE_CLEARANCE = 0.4      # mm
FENCE_THICKNESS = 0.8     # mm
FENCE_HEIGHT = 2.2        # mm
FENCE_SEGMENTS = 440      # fences per lane (higher = smoother)
FENCE_BOX_MINLEN = 0.65   # mm

# small lift so fences sit on top cleanly
BASE_LIFT = 0.15          # mm

# Output names
OUT_FULL = "rodin_6coil_channel_guide_full_v2_wire12.stl"
OUT_TOP = "rodin_6coil_channel_guide_top_v2.stl"
OUT_BOTTOM = "rodin_6coil_channel_guide_bottom_v2.stl"
OUT_PNG = "rodin_6coil_channel_guide_preview_v2_wire12.png"


# =========================
# Geometry helpers
# =========================
def torus_lane(R_major: float, r_surface: float, p: int, q: int, t: np.ndarray,
               phase_angle: float = 0.0, mirror: bool = False, offset: float = 0.0) -> np.ndarray:
    theta = p * t + phase_angle
    phi = q * t
    r_eff = r_surface + offset

    x = (R_major + r_eff * np.cos(phi)) * np.cos(theta)
    y = (R_major + r_eff * np.cos(phi)) * np.sin(theta)
    z = r_eff * np.sin(phi)

    if mirror:
        z = -z
    return np.column_stack([x, y, z])


def torus_frame(pt: np.ndarray, tangent: np.ndarray, R_major: float):
    """
    (t_hat, n_hat, l_hat)
    t_hat: lane tangent
    n_hat: outward torus surface normal
    l_hat: lateral within surface, perpendicular to tangent
    """
    t_hat = tangent / max(np.linalg.norm(tangent), 1e-12)

    x, y, z = pt
    theta = np.arctan2(y, x)
    center = np.array([R_major*np.cos(theta), R_major*np.sin(theta), 0.0])
    n = pt - center
    n_hat = n / max(np.linalg.norm(n), 1e-12)

    l = np.cross(n_hat, t_hat)
    l_hat = l / max(np.linalg.norm(l), 1e-12)
    return t_hat, n_hat, l_hat


def make_oriented_box(center: np.ndarray, t_hat: np.ndarray, n_hat: np.ndarray, l_hat: np.ndarray,
                      length: float, thickness: float, height: float) -> trimesh.Trimesh:
    """
    Local axes:
      x -> l_hat (thickness)
      y -> n_hat (height)
      z -> t_hat (length)
    """
    box = trimesh.creation.box(extents=[thickness, height, length])

    T = np.eye(4)
    T[:3, 0] = l_hat
    T[:3, 1] = n_hat
    T[:3, 2] = t_hat
    box.apply_transform(T)
    box.apply_translation(center)
    return box


def build_base_torus_revolve(R_major: float, r_tube: float,
                             profile_samples: int, sections: int) -> trimesh.Trimesh:
    """
    Build watertight torus by revolving a circle (offset from axis) around the Y-axis.
    We then rotate it to be around Z-axis (cosmetic; geometry identical).
    """
    phi = np.linspace(0.0, 2*np.pi, profile_samples, endpoint=True)
    linestring = np.column_stack([R_major + r_tube*np.cos(phi), r_tube*np.sin(phi)])  # 2D
    torus = trimesh.creation.revolve(linestring, sections=sections)

    torus.remove_duplicate_faces()
    torus.remove_degenerate_faces()
    torus.merge_vertices()
    return torus


def build_lane_fences(path_pts: np.ndarray, R_major: float,
                      wire_d: float, clearance: float,
                      fence_th: float, fence_h: float,
                      segments: int) -> list:
    half_gap = 0.5 * (wire_d + clearance)
    fence_center_offset = half_gap + 0.5 * fence_th

    idx = np.linspace(0, len(path_pts)-1, segments, dtype=int)

    fences = []
    for i0, i1 in zip(idx[:-1], idx[1:]):
        a = path_pts[i0]
        b = path_pts[i1]
        seg = b - a
        seg_len = float(np.linalg.norm(seg))
        if seg_len < FENCE_BOX_MINLEN:
            continue
        mid = 0.5*(a+b)
        t_hat, n_hat, l_hat = torus_frame(mid, seg, R_major)

        mid_lifted = mid + n_hat * BASE_LIFT

        # centers of fences, lifted so their bases sit just above surface
        cL = mid_lifted + l_hat * fence_center_offset + n_hat * (0.5*fence_h)
        cR = mid_lifted - l_hat * fence_center_offset + n_hat * (0.5*fence_h)

        fences.append(make_oriented_box(cL, t_hat, n_hat, l_hat, length=seg_len, thickness=fence_th, height=fence_h))
        fences.append(make_oriented_box(cR, t_hat, n_hat, l_hat, length=seg_len, thickness=fence_th, height=fence_h))
    return fences


def slice_part(mesh: trimesh.Trimesh, top: bool) -> trimesh.Trimesh:
    origin = np.array([0.0, 0.0, 0.0])
    if top:
        return slice_mesh_plane(mesh, plane_normal=[0,0,1], plane_origin=origin, cap=True)
    else:
        return slice_mesh_plane(mesh, plane_normal=[0,0,-1], plane_origin=origin, cap=True)


def preview(centerline: np.ndarray, lanes: list, out_png: str):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot(centerline[:,0], centerline[:,1], centerline[:,2], linewidth=1, alpha=0.28)

    for name, pts in lanes:
        ax.plot(pts[:,0], pts[:,1], pts[:,2], linewidth=2, alpha=0.85, label=name)

    all_pts = np.vstack([centerline] + [pts for _, pts in lanes])
    mins, maxs = all_pts.min(axis=0), all_pts.max(axis=0)
    span = float(np.max(maxs - mins))
    mid = 0.5*(mins+maxs)

    ax.set_xlim(mid[0]-span/2, mid[0]+span/2)
    ax.set_ylim(mid[1]-span/2, mid[1]+span/2)
    ax.set_zlim(mid[2]-span/2, mid[2]+span/2)

    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title("6-lane channel guide preview (lane centerlines)")
    ax.legend(loc="upper left", fontsize=7)
    plt.tight_layout()
    plt.savefig(out_png, dpi=170)
    plt.close(fig)


def main():
    # base torus (watertight)
    base = build_base_torus_revolve(R_MAJOR, R_TUBE, TORUS_PROFILE_SAMPLES, TORUS_SECTIONS)

    # lanes
    t = np.linspace(0.0, 2*np.pi, N_PATH, endpoint=True)
    lanes = []
    for k, ang in enumerate(PHASE_ANGLES):
        pts_top = torus_lane(R_MAJOR, R_TUBE, P, Q, t, phase_angle=ang, mirror=False)
        lanes.append((f"Phase {k+1} top", pts_top))
        if MIRROR:
            pts_bot = torus_lane(R_MAJOR, R_TUBE, P, Q, t, phase_angle=ang, mirror=True)
            lanes.append((f"Phase {k+1} bottom", pts_bot))

    # build all parts
    parts = [base]
    fence_parts = []
    for _, pts in lanes:
        fence_parts.extend(build_lane_fences(
            pts, R_MAJOR,
            wire_d=WIRE_DIAMETER, clearance=WIRE_CLEARANCE,
            fence_th=FENCE_THICKNESS, fence_h=FENCE_HEIGHT,
            segments=FENCE_SEGMENTS
        ))
    parts.extend(fence_parts)

    full = trimesh.util.concatenate(parts)
    full.remove_duplicate_faces()
    full.remove_degenerate_faces()
    full.merge_vertices()
    full.apply_translation(-full.centroid)

    ext = full.bounds[1] - full.bounds[0]
    print("FULL extents (mm):", ext)

    full.export(OUT_FULL)
    print("Wrote:", OUT_FULL)

    # preview
    ang = np.linspace(0.0, 2*np.pi, 600, endpoint=True)
    centerline = np.column_stack([R_MAJOR*np.cos(ang), R_MAJOR*np.sin(ang), np.zeros_like(ang)])
    preview(centerline, lanes, OUT_PNG)
    print("Wrote:", OUT_PNG)


if __name__ == "__main__":
    main()