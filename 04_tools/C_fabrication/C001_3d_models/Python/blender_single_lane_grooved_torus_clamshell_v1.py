#!/usr/bin/env python3
# Blender 5.x script: Single-lane grooved torus + optional clamshell halves with alignment pegs/holes.
# Focus: torus + ONE groove carved (boolean difference), not the raised "wire" cutter.
#
# Usage:
#   - Open Blender -> Scripting -> open this file -> set OUTPUT_DIR -> Run Script
#   - Exports: grooved_torus_full.stl, grooved_torus_halfA.stl, grooved_torus_halfB.stl (if MAKE_HALVES=True)

import bpy
import os
import math

# =========================
# Output
# =========================
OUTPUT_DIR = r"C:\workspace\projects\SwirlStringTheory\images\Python"  # e.g. r"C:\Users\Omar\Desktop\rodin_out"  (leave empty to use the .blend folder / temp)

# =========================
# Torus geometry (mm)
# =========================
OUTER_RADIUS   = 45.0   # mm (R_MAJOR + R_TUBE). Outer diameter = 90 mm.
HOLE_DIAMETER  = 10.0   # mm (inner hole diameter = 2*(R_MAJOR - R_TUBE))

# Derived (horn-ish if HOLE_DIAMETER ~ 0)
R_MAJOR = 0.5 * (OUTER_RADIUS + 0.5 * HOLE_DIAMETER)
R_TUBE  = 0.5 * (OUTER_RADIUS - 0.5 * HOLE_DIAMETER)
if not (R_MAJOR > R_TUBE > 0):
    raise ValueError("Invalid radii: need R_MAJOR > R_TUBE > 0. Adjust OUTER_RADIUS / HOLE_DIAMETER.")

# Torus mesh resolution
TORUS_MAJOR_SEG = 192
TORUS_MINOR_SEG = 128

# =========================
# Groove sizing (mm) — for inserting wire after printing
# =========================
WIRE_D     = 1.20   # mm  (set to 0.80 or 1.20)
CLEARANCE  = 0.40   # mm  (total diameter clearance)
GROOVE_R   = 0.5 * (WIRE_D + CLEARANCE)  # cutter radius (mm)

# Visible groove depth into the surface (must be <= GROOVE_R)
# Suggested:
#  - 0.8 mm wire: 0.50
#  - 1.2 mm wire: 0.65
GROOVE_DEPTH = 0.65  # mm

# Sink the cutter centerline inward: surface depth ≈ GROOVE_R - SINK
GROOVE_DEPTH = min(GROOVE_DEPTH, GROOVE_R)  # clamp
SINK = max(0.0, GROOVE_R - GROOVE_DEPTH)

# Lane curve resolution
LANE_POINTS = 1400

# =========================
# Lane definition (Rodin-like 5,12) — single lane for now
# =========================
P = 5
Q = 12
MINOR_OFFSET_DEG = 0.0
Q_SIGN = +1  # flip to -1 for mirrored handedness

# =========================
# Clamshell option + attachments
# =========================
MAKE_HALVES = True
SPLIT_AXIS = "X"    # split plane at X=0

PEG_R = 2.0         # mm
PEG_LEN = 6.0       # mm
HOLE_CLEAR = 0.25   # mm (radial)
PEG_POS = [(0.0,  15.0, 0.0), (0.0, -15.0, 0.0)]  # positions on split face (x auto)

# =========================
# Helpers
# =========================
def _abspath(p):
    return bpy.path.abspath(p)

def get_output_dir():
    if OUTPUT_DIR:
        d = _abspath(OUTPUT_DIR)
    else:
        d = _abspath("//")
        if not d:
            d = bpy.app.tempdir
    if not d:
        d = "."
    os.makedirs(d, exist_ok=True)
    return d

def enable_stl_addon():
    for mod in ("io_mesh_stl", "io_scene_stl"):
        try:
            bpy.ops.preferences.addon_enable(module=mod)
        except Exception:
            pass

def export_stl(obj, filepath):
    enable_stl_addon()
    filepath = _abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True, ascii_format=False)
        return
    if hasattr(bpy.ops.export_mesh, "stl"):
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True, ascii=False)
        return
    raise RuntimeError("No STL export operator found. Enable STL addon in Preferences.")

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    try:
        for _ in range(3):
            bpy.ops.outliner.orphans_purge(do_recursive=True)
    except Exception:
        pass

def set_name(obj, name):
    obj.name = name
    if obj.data:
        obj.data.name = name + "_data"

def apply_modifier(obj, mod_name):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod_name)

def boolean_diff(target, cutter, name="BoolDiff"):
    mod = target.modifiers.new(name, 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    apply_modifier(target, mod.name)

def boolean_intersect(target, volume, name="BoolIntersect"):
    mod = target.modifiers.new(name, 'BOOLEAN')
    mod.operation = 'INTERSECT'
    mod.solver = 'EXACT'
    mod.object = volume
    apply_modifier(target, mod.name)

def boolean_union(target, other, name="BoolUnion"):
    mod = target.modifiers.new(name, 'BOOLEAN')
    mod.operation = 'UNION'
    mod.solver = 'EXACT'
    mod.object = other
    apply_modifier(target, mod.name)

def make_torus():
    bpy.ops.mesh.primitive_torus_add(
        major_radius=R_MAJOR,
        minor_radius=R_TUBE,
        major_segments=TORUS_MAJOR_SEG,
        minor_segments=TORUS_MINOR_SEG,
        align='WORLD',
        location=(0,0,0),
        rotation=(0,0,0),
    )
    tor = bpy.context.view_layer.objects.active
    set_name(tor, "Torus")
    return tor

def torus_surface_point(theta, phi):
    x = (R_MAJOR + R_TUBE*math.cos(phi)) * math.cos(theta)
    y = (R_MAJOR + R_TUBE*math.cos(phi)) * math.sin(theta)
    z =  R_TUBE * math.sin(phi)
    return (x,y,z)

def torus_normal(theta, phi):
    nx = math.cos(phi) * math.cos(theta)
    ny = math.cos(phi) * math.sin(theta)
    nz = math.sin(phi)
    return (nx,ny,nz)

def make_lane_curve():
    curve = bpy.data.curves.new("LaneCurve", type='CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 8

    spline = curve.splines.new('POLY')
    spline.points.add(LANE_POINTS-1)

    minor_offset = math.radians(MINOR_OFFSET_DEG)
    q_val = Q_SIGN * Q

    for i in range(LANE_POINTS):
        t = 2.0*math.pi * (i/(LANE_POINTS-1))
        theta = P * t
        phi   = q_val * t + minor_offset

        x,y,z = torus_surface_point(theta, phi)
        nx,ny,nz = torus_normal(theta, phi)

        # sink inward so the groove is carved into the surface
        x -= nx*SINK
        y -= ny*SINK
        z -= nz*SINK
        spline.points[i].co = (x, y, z, 1.0)

    obj = bpy.data.objects.new("LaneCurveObj", curve)
    bpy.context.collection.objects.link(obj)

    curve.bevel_depth = GROOVE_R
    curve.bevel_resolution = 8
    curve.fill_mode = 'FULL'
    return obj

def convert_to_mesh(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    return bpy.context.view_layer.objects.active

def make_halfspace_cube(axis, positive=True, size=300.0):
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0,0,0))
    c = bpy.context.view_layer.objects.active
    set_name(c, "HalfSpace")

    if axis == "X":
        c.location.x = +size/2 if positive else -size/2
    elif axis == "Y":
        c.location.y = +size/2 if positive else -size/2
    elif axis == "Z":
        c.location.z = +size/2 if positive else -size/2
    else:
        raise ValueError("axis must be X/Y/Z")
    return c

def add_pegs_and_holes(halfA, halfB):
    for (_x0, y0, z0) in PEG_POS:
        # Peg on halfA: along +X, starting at split plane x=0
        bpy.ops.mesh.primitive_cylinder_add(radius=PEG_R, depth=PEG_LEN, location=(PEG_LEN/2, y0, z0))
        peg = bpy.context.view_layer.objects.active
        peg.rotation_euler = (0.0, math.radians(90.0), 0.0)
        set_name(peg, "Peg")
        boolean_union(halfA, peg, "PegUnion")
        bpy.ops.object.select_all(action='DESELECT')
        peg.select_set(True)
        bpy.ops.object.delete(use_global=False, confirm=False)

        # Hole in halfB: slightly larger
        hole_r = PEG_R + HOLE_CLEAR
        hole_len = PEG_LEN + 0.8
        bpy.ops.mesh.primitive_cylinder_add(radius=hole_r, depth=hole_len, location=(hole_len/2, y0, z0))
        hole = bpy.context.view_layer.objects.active
        hole.rotation_euler = (0.0, math.radians(90.0), 0.0)
        set_name(hole, "PegHole")
        boolean_diff(halfB, hole, "PegHoleDiff")
        bpy.ops.object.select_all(action='DESELECT')
        hole.select_set(True)
        bpy.ops.object.delete(use_global=False, confirm=False)

def main():
    print(f"R_MAJOR={R_MAJOR:.3f} mm, R_TUBE={R_TUBE:.3f} mm")
    print(f"GROOVE_R={GROOVE_R:.3f} mm, GROOVE_DEPTH={GROOVE_DEPTH:.3f} mm, SINK={SINK:.3f} mm")

    clear_scene()

    # Create torus
    tor = make_torus()

    # Create ONE lane cutter and convert to mesh
    lane_curve = make_lane_curve()
    lane_mesh = convert_to_mesh(lane_curve)
    set_name(lane_mesh, "GrooveCutter_01")

    # Carve: torus - cutter
    boolean_diff(tor, lane_mesh, "GrooveCarve")

    # Delete cutter so it doesn't look like a raised wire
    bpy.ops.object.select_all(action='DESELECT')
    lane_mesh.select_set(True)
    bpy.ops.object.delete(use_global=False, confirm=False)

    set_name(tor, "GroovedTorus_full")

    out_dir = get_output_dir()
    print("Output directory:", out_dir)

    export_stl(tor, os.path.join(out_dir, "grooved_torus_full.stl"))

    if MAKE_HALVES:
        # Duplicate for halves
        halfA = tor.copy()
        halfA.data = tor.data.copy()
        bpy.context.collection.objects.link(halfA)
        set_name(halfA, "GroovedTorus_halfA")

        halfB = tor.copy()
        halfB.data = tor.data.copy()
        bpy.context.collection.objects.link(halfB)
        set_name(halfB, "GroovedTorus_halfB")

        size = max(300.0, 8.0*OUTER_RADIUS)

        cube_neg = make_halfspace_cube(SPLIT_AXIS, positive=False, size=size)  # x<=0
        boolean_intersect(halfA, cube_neg, "HalfA")
        bpy.ops.object.select_all(action='DESELECT')
        cube_neg.select_set(True)
        bpy.ops.object.delete(use_global=False, confirm=False)

        cube_pos = make_halfspace_cube(SPLIT_AXIS, positive=True, size=size)   # x>=0
        boolean_intersect(halfB, cube_pos, "HalfB")
        bpy.ops.object.select_all(action='DESELECT')
        cube_pos.select_set(True)
        bpy.ops.object.delete(use_global=False, confirm=False)

        add_pegs_and_holes(halfA, halfB)

        export_stl(halfA, os.path.join(out_dir, "grooved_torus_halfA.stl"))
        export_stl(halfB, os.path.join(out_dir, "grooved_torus_halfB.stl"))

    blend_path = os.path.join(out_dir, "grooved_torus_single_lane.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("Saved:", blend_path)
    print("Done.")

if __name__ == "__main__":
    main()