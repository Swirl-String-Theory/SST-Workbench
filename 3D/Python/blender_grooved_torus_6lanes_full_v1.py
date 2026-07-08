# Blender 5.x script: full torus with 6 carved grooves (3-phase + 3 mirrored)
# Exports STL(s) and saves a .blend. No halves.
#
# Usage:
#   - Open Blender -> Scripting -> open this file -> set OUTPUT_DIR -> Run Script
#
# Notes:
#   - Grooves are created by BOOLEAN DIFFERENCE (cut out of torus).
#   - The cutter meshes are deleted afterwards, so nothing is "added on the inside".
#   - A copy of the original solid torus is kept as SolidTorus (for "filled" version).

import bpy, os, math

# =========================
# User parameters
# =========================
OUTPUT_DIR = None  # e.g. r"C:\Users\Omar\Desktop\rodin_out"

# Geometry: keep within 9x9x9 cm by default
OUTER_RADIUS  = 45.0   # mm => outer diameter 90 mm
HOLE_DIAMETER = 10.0   # mm => inner hole diameter (0 = horn torus, not recommended)

# Lane (Rodin-style) torus knot parameters: (p,q)
P = 5
Q = 12

# Wire / groove sizing (mm) for placing wire afterwards
WIRE_D       = 1.20    # set to 0.80 or 1.20
CLEARANCE    = 0.40    # total extra diameter clearance (0.25–0.45 typical)
GROOVE_DEPTH = 0.70    # mm visible groove depth (<= GROOVE_R). Try 0.55 for 0.8mm wire.

# Curve / mesh quality
LANE_POINTS = 900      # increase for smoother curves
CURVE_RESOLUTION_U = 32
BEVEL_RESOLUTION = 10

# Robust boolean
USE_VOXEL_REMESH = False
VOXEL_SIZE = 0.25      # mm (smaller = finer, slower)

# Exports
EXPORT_SOLID = True
EXPORT_GROOVED = True

# =========================
# Derived radii
# =========================
# From: R+r = OUTER_RADIUS and 2(R-r)=HOLE_DIAMETER
R_MAJOR = 0.5 * (OUTER_RADIUS + 0.5 * HOLE_DIAMETER)
R_TUBE  = 0.5 * (OUTER_RADIUS - 0.5 * HOLE_DIAMETER)
if R_TUBE <= 0 or R_MAJOR <= R_TUBE:
    raise ValueError("Invalid torus radii. Ensure OUTER_RADIUS is large enough and HOLE_DIAMETER not too big.")

GROOVE_D = WIRE_D + CLEARANCE
GROOVE_R = 0.5 * GROOVE_D

if GROOVE_DEPTH > GROOVE_R:
    raise ValueError("GROOVE_DEPTH must be <= GROOVE_R. Decrease GROOVE_DEPTH or increase groove radius.")

# Sink derived from depth: surface depth ≈ GROOVE_R - SINK  => SINK = GROOVE_R - GROOVE_DEPTH
SINK = max(0.0, GROOVE_R - GROOVE_DEPTH)

print(f"Radii: OUTER_RADIUS={OUTER_RADIUS:.3f} mm HOLE_DIAMETER={HOLE_DIAMETER:.3f} mm -> R_MAJOR={R_MAJOR:.3f} mm R_TUBE={R_TUBE:.3f} mm")
print(f"Groove: WIRE_D={WIRE_D:.3f} mm CLEARANCE={CLEARANCE:.3f} mm => GROOVE_D={GROOVE_D:.3f} mm GROOVE_R={GROOVE_R:.3f} mm GROOVE_DEPTH={GROOVE_DEPTH:.3f} mm => SINK={SINK:.3f} mm")

# =========================
# Helpers
# =========================
def deselect_all():
    for o in bpy.context.selected_objects:
        o.select_set(False)

def set_active(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

def apply_modifier(obj, mod_name):
    set_active(obj)
    bpy.ops.object.modifier_apply(modifier=mod_name)

def add_voxel_remesh(obj, voxel_size_mm):
    mod = obj.modifiers.new(name="VoxelRemesh", type='REMESH')
    mod.mode = 'VOXEL'
    mod.voxel_size = voxel_size_mm / 1000.0  # Blender default is meters; our scene will be in mm scale below
    mod.use_smooth_shade = False
    return mod

def ensure_units_mm():
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 0.001  # 1 Blender unit = 1 mm
    s.unit_settings.length_unit = 'MILLIMETERS'

def get_output_dir():
    if OUTPUT_DIR:
        d = bpy.path.abspath(OUTPUT_DIR)
    else:
        d = bpy.path.abspath("//")  # if .blend saved
        if not d:
            d = bpy.app.tempdir
    if not d:
        d = "."
    os.makedirs(d, exist_ok=True)
    return d

def export_stl(obj, filepath):
    filepath = bpy.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    deselect_all()
    set_active(obj)

    # Try to enable STL addon
    try:
        bpy.ops.preferences.addon_enable(module="io_mesh_stl")
    except Exception:
        pass
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_stl")
    except Exception:
        pass

    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True, ascii_format=False)
        return
    if hasattr(bpy.ops.export_mesh, "stl"):
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True, ascii=False)
        return
    raise RuntimeError("No STL export operator found.")

def convert_to_mesh(obj):
    deselect_all()
    set_active(obj)
    bpy.ops.object.convert(target='MESH')
    return bpy.context.view_layer.objects.active

def join_objects(objs, name):
    deselect_all()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = name
    return joined

def boolean_difference(target, cutter, name="BooleanDiff"):
    mod = target.modifiers.new(name=name, type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    apply_modifier(target, mod.name)

# =========================
# Torus-knot lane points
# =========================
def torus_surface_point(theta, phi):
    # Standard torus param (R_MAJOR, R_TUBE)
    c = math.cos(phi)
    s = math.sin(phi)
    ct = math.cos(theta)
    st = math.sin(theta)
    x = (R_MAJOR + R_TUBE * c) * ct
    y = (R_MAJOR + R_TUBE * c) * st
    z = (R_TUBE * s)
    return (x, y, z)

def torus_normal(theta, phi):
    # Unit normal on torus surface (points outward from tube center)
    ct = math.cos(theta); st = math.sin(theta)
    c = math.cos(phi);   s = math.sin(phi)
    nx = c * ct
    ny = c * st
    nz = s
    # already unit length
    return (nx, ny, nz)

def make_lane_points(minor_offset_rad, q_val):
    pts = []
    # Use t in [0, 2π] for a closed (p,q) curve
    for i in range(LANE_POINTS + 1):
        t = 2.0 * math.pi * i / LANE_POINTS
        theta = P * t
        phi   = q_val * t + minor_offset_rad

        x, y, z = torus_surface_point(theta, phi)
        nx, ny, nz = torus_normal(theta, phi)

        # Sink inward by SINK along normal (towards tube center => subtract outward normal)
        x -= SINK * nx
        y -= SINK * ny
        z -= SINK * nz

        pts.append((x, y, z))
    return pts

def create_curve_from_points(name, pts):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = CURVE_RESOLUTION_U

    spline = curve_data.splines.new(type='POLY')
    spline.points.add(len(pts) - 1)
    for i, (x, y, z) in enumerate(pts):
        spline.points[i].co = (x, y, z, 1.0)

    # Bevel: make it a tube cutter
    curve_data.bevel_depth = GROOVE_R
    curve_data.bevel_resolution = BEVEL_RESOLUTION
    curve_data.fill_mode = 'FULL'

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    obj.display_type = 'WIRE'
    obj.hide_render = True
    return obj

# =========================
# Main
# =========================
def main():
    ensure_units_mm()

    # Clean scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Base torus (outer)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=R_MAJOR,
        minor_radius=R_TUBE,
        major_segments=160,
        minor_segments=96,
        align='WORLD',
        location=(0,0,0),
        rotation=(0,0,0)
    )
    torus = bpy.context.view_layer.objects.active
    torus.name = "GroovedTorus_full"

    # Keep a solid copy (filled version)
    solid = torus.copy()
    solid.data = torus.data.copy()
    bpy.context.collection.objects.link(solid)
    solid.name = "SolidTorus_full"

    # Build 6 lanes: 3-phase + mirrored handedness
    # Group A (3-phase): offsets 0,120,240 with +Q
    # Group B (mirrored): offsets 60,180,300 with -Q
    lane_specs = [
        (+Q, 0), (+Q, 120), (+Q, 240),
        (-Q, 60), (-Q, 180), (-Q, 300)
    ]

    lane_curves = []
    for idx, (q_val, deg) in enumerate(lane_specs, start=1):
        pts = make_lane_points(math.radians(deg), q_val)
        tag = "A" if q_val > 0 else "B"
        c = create_curve_from_points(f"Lane_{idx:02d}_{tag}_Q{q_val:+d}_{deg}deg", pts)
        lane_curves.append(c)

    # Convert curves to mesh cutters
    cutter_meshes = [convert_to_mesh(o) for o in lane_curves]
    cutters_joined = join_objects(cutter_meshes, "GrooveCutters")
    cutters_joined.hide_set(True)
    cutters_joined.hide_render = True

    # Optional voxel remesh to make boolean more reliable
    if USE_VOXEL_REMESH:
        add_voxel_remesh(cutters_joined, VOXEL_SIZE); apply_modifier(cutters_joined, "VoxelRemesh")
        add_voxel_remesh(torus, VOXEL_SIZE);          apply_modifier(torus, "VoxelRemesh")

    # Boolean difference: carve grooves out of the torus
    boolean_difference(torus, cutters_joined, name="CutGrooves")

    # Delete cutters: ensures nothing is "added" anywhere
    deselect_all()
    cutters_joined.select_set(True)
    bpy.ops.object.delete()

    # Exports
    out_dir = get_output_dir()
    print("Output directory:", out_dir)

    if EXPORT_SOLID:
        export_stl(solid, os.path.join(out_dir, "rodin_torus_solid.stl"))
        print("Exported: rodin_torus_solid.stl")

    if EXPORT_GROOVED:
        export_stl(torus, os.path.join(out_dir, "rodin_torus_grooved_6lane.stl"))
        print("Exported: rodin_torus_grooved_6lane.stl")

    # Save .blend
    blend_path = os.path.join(out_dir, "rodin_torus_grooved_6lane.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("Saved:", blend_path)

if __name__ == "__main__":
    main()