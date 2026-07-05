# Blender 5.x script: FULL torus with 6 carved grooves (3-phase + 3 mirrored)
# Context-safe version (avoids ops that require a VIEW_3D context where possible).
#
# Exports:
#   - rodin_torus_solid.stl
#   - rodin_torus_grooved_6lane.stl
#   - rodin_torus_grooved_6lane.blend
#
# Usage:
#   Blender -> Scripting -> open this file -> set OUTPUT_DIR -> Run Script

import bpy, os, math

# =========================
# User parameters
# =========================
OUTPUT_DIR = None  # e.g. r"C:\Users\Omar\Desktop\rodin_out"

# Geometry (keep within ~9x9x9 cm)
OUTER_RADIUS  = 45.0   # mm (outer diameter = 90 mm)
HOLE_DIAMETER = 10.0   # mm (center hole diameter; set small but nonzero for printability)

# Torus-knot lane (p,q)
P = 5
Q = 12

# Wire / groove sizing (mm) for placing wire afterwards
WIRE_D       = 1.20    # set to 0.80 or 1.20
CLEARANCE    = 0.40    # total extra diameter clearance
GROOVE_DEPTH = 0.70    # mm visible groove depth (<= GROOVE_R)

# Quality
LANE_POINTS = 900
CURVE_RESOLUTION_U = 32
BEVEL_RESOLUTION = 10
TORUS_MAJOR_SEG = 160
TORUS_MINOR_SEG = 96

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
    raise ValueError("GROOVE_DEPTH must be <= GROOVE_R.")

# Sink derived from depth: depth ≈ GROOVE_R - SINK  => SINK = GROOVE_R - GROOVE_DEPTH
SINK = max(0.0, GROOVE_R - GROOVE_DEPTH)

print(f"R_MAJOR={R_MAJOR:.3f} mm, R_TUBE={R_TUBE:.3f} mm")
print(f"GROOVE_D={GROOVE_D:.3f} mm, GROOVE_R={GROOVE_R:.3f} mm, GROOVE_DEPTH={GROOVE_DEPTH:.3f} mm => SINK={SINK:.3f} mm")


# =========================
# Helpers (context-safe)
# =========================
def ensure_units_mm():
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 0.001  # 1 Blender unit = 1 mm
    s.unit_settings.length_unit = 'MILLIMETERS'

def get_output_dir():
    if OUTPUT_DIR:
        d = bpy.path.abspath(OUTPUT_DIR)
    else:
        d = bpy.path.abspath("//") or bpy.app.tempdir or "."
    os.makedirs(d, exist_ok=True)
    return d

def clear_scene_data_api():
    # Remove objects without bpy.ops (avoids context poll issues)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    # Optional: purge orphan data (safe but not necessary)
    # for datablock in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
    #     for b in list(datablock):
    #         if b.users == 0:
    #             datablock.remove(b)

def make_torus_mesh(name):
    # Use ops for primitive creation; usually works from script, but ensure object mode
    try:
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass

    bpy.ops.mesh.primitive_torus_add(
        major_radius=R_MAJOR,
        minor_radius=R_TUBE,
        major_segments=TORUS_MAJOR_SEG,
        minor_segments=TORUS_MINOR_SEG,
        align='WORLD',
        location=(0,0,0),
        rotation=(0,0,0)
    )
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    return obj

def create_curve_from_points(name, pts):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = CURVE_RESOLUTION_U

    spline = curve_data.splines.new(type='POLY')
    spline.points.add(len(pts) - 1)
    for i, (x, y, z) in enumerate(pts):
        spline.points[i].co = (x, y, z, 1.0)

    curve_data.bevel_depth = GROOVE_R
    curve_data.bevel_resolution = BEVEL_RESOLUTION
    curve_data.fill_mode = 'FULL'

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    obj.hide_render = True
    return obj

def curve_to_mesh_object(curve_obj, mesh_name):
    # Convert without bpy.ops using evaluated mesh
    deps = bpy.context.evaluated_depsgraph_get()
    obj_eval = curve_obj.evaluated_get(deps)
    mesh = bpy.data.meshes.new_from_object(obj_eval)
    mesh_obj = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.collection.objects.link(mesh_obj)
    # Remove the curve object
    bpy.data.objects.remove(curve_obj, do_unlink=True)
    return mesh_obj

def add_voxel_remesh(obj, voxel_size_mm):
    mod = obj.modifiers.new(name="VoxelRemesh", type='REMESH')
    mod.mode = 'VOXEL'
    mod.voxel_size = voxel_size_mm / 1000.0  # scene units are mm => 1 mm = 0.001 m
    mod.use_smooth_shade = False
    return mod

def apply_modifier(obj, mod_name):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod_name)
    obj.select_set(False)

def boolean_difference_apply(target, cutter, name="Cut"):
    mod = target.modifiers.new(name=name, type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    apply_modifier(target, mod.name)

def enable_stl_addon():
    try:
        bpy.ops.preferences.addon_enable(module="io_mesh_stl")
    except Exception:
        pass
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_stl")
    except Exception:
        pass

def export_stl_selected(obj, filepath):
    filepath = bpy.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    enable_stl_addon()

    # Select only obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Blender 5: wm.stl_export
    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True, ascii_format=False, apply_modifiers=True)
        return
    # Older fallback
    if hasattr(bpy.ops.export_mesh, "stl"):
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True, ascii=False)
        return
    raise RuntimeError("No STL export operator found.")

# =========================
# Torus param + normals
# =========================
def torus_surface_point(theta, phi):
    c = math.cos(phi); s = math.sin(phi)
    ct = math.cos(theta); st = math.sin(theta)
    x = (R_MAJOR + R_TUBE * c) * ct
    y = (R_MAJOR + R_TUBE * c) * st
    z = (R_TUBE * s)
    return (x, y, z)

def torus_normal(theta, phi):
    ct = math.cos(theta); st = math.sin(theta)
    c  = math.cos(phi);   s  = math.sin(phi)
    return (c * ct, c * st, s)  # unit normal

def make_lane_points(minor_offset_rad, q_val):
    pts = []
    for i in range(LANE_POINTS + 1):
        t = 2.0 * math.pi * i / LANE_POINTS
        theta = P * t
        phi   = q_val * t + minor_offset_rad

        x, y, z = torus_surface_point(theta, phi)
        nx, ny, nz = torus_normal(theta, phi)

        # Sink inward by SINK along outward normal
        x -= SINK * nx
        y -= SINK * ny
        z -= SINK * nz

        pts.append((x, y, z))
    return pts

# =========================
# Main
# =========================
def main():
    ensure_units_mm()
    clear_scene_data_api()

    torus = make_torus_mesh("GroovedTorus_full")

    # Solid reference copy
    solid = torus.copy()
    solid.data = torus.data.copy()
    bpy.context.collection.objects.link(solid)
    solid.name = "SolidTorus_full"

    # 6 lanes: 3-phase + mirrored handedness
    lane_specs = [
        (+Q, 0), (+Q, 120), (+Q, 240),
        (-Q, 60), (-Q, 180), (-Q, 300)
    ]

    cutters = []
    for idx, (q_val, deg) in enumerate(lane_specs, start=1):
        pts = make_lane_points(math.radians(deg), q_val)
        tag = "A" if q_val > 0 else "B"
        curve = create_curve_from_points(f"LaneCurve_{idx:02d}_{tag}_{deg}deg", pts)
        mesh_cutter = curve_to_mesh_object(curve, f"LaneCutter_{idx:02d}_{tag}_{deg}deg")
        mesh_cutter.hide_render = True
        cutters.append(mesh_cutter)

    # Optional voxel remesh to reduce boolean artifacts
    if USE_VOXEL_REMESH:
        add_voxel_remesh(torus, VOXEL_SIZE); apply_modifier(torus, "VoxelRemesh")
        for c in cutters:
            add_voxel_remesh(c, VOXEL_SIZE); apply_modifier(c, "VoxelRemesh")

    # Boolean subtract EACH cutter (avoids join operator)
    for i, c in enumerate(cutters, start=1):
        boolean_difference_apply(torus, c, name=f"Cut_{i:02d}")
        bpy.data.objects.remove(c, do_unlink=True)

    # Export
    out_dir = get_output_dir()
    print("Output directory:", out_dir)

    if EXPORT_SOLID:
        export_stl_selected(solid, os.path.join(out_dir, "rodin_torus_solid.stl"))
        print("Exported rodin_torus_solid.stl")

    if EXPORT_GROOVED:
        export_stl_selected(torus, os.path.join(out_dir, "rodin_torus_grooved_6lane.stl"))
        print("Exported rodin_torus_grooved_6lane.stl")

    blend_path = os.path.join(out_dir, "rodin_torus_grooved_6lane.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("Saved:", blend_path)

if __name__ == "__main__":
    main()