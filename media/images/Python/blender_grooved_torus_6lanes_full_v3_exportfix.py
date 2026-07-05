# Blender 5.x script: FULL torus with 6 carved grooves (3-phase + 3 mirrored)
# v3: export/cleanup hardened (prevents "only cutters exported" situations)
#
# What you get:
#   - rodin_torus_solid.stl
#   - rodin_torus_grooved_6lane.stl
#   - rodin_torus_grooved_6lane.blend
#
# Key guarantee:
#   Grooves are BOOLEAN DIFFERENCE cuts into the torus. Cutters are deleted before export.

import bpy, os, math

# =========================
# User parameters
# =========================
OUTPUT_DIR = r"."   # <-- SET THIS to an absolute path you can write to.

OUTER_RADIUS  = 45.0   # mm (outer diameter 90 mm)
HOLE_DIAMETER = 10.0   # mm

P = 5
Q = 12

# Wire/groove parameters
WIRE_D       = 1.20    # mm (set 0.80 or 1.20)
CLEARANCE    = 0.40    # mm total diameter clearance
GROOVE_DEPTH = 0.70    # mm visible depth (<= GROOVE_R). For "very obvious" grooves use ~GROOVE_R.

LANE_POINTS = 900
CURVE_RESOLUTION_U = 32
BEVEL_RESOLUTION = 10
TORUS_MAJOR_SEG = 180
TORUS_MINOR_SEG = 110

USE_VOXEL_REMESH = False
VOXEL_SIZE = 0.25  # mm

EXPORT_SOLID = True
EXPORT_GROOVED = True

# =========================
# Derived radii
# =========================
R_MAJOR = 0.5 * (OUTER_RADIUS + 0.5 * HOLE_DIAMETER)
R_TUBE  = 0.5 * (OUTER_RADIUS - 0.5 * HOLE_DIAMETER)
if R_TUBE <= 0 or R_MAJOR <= R_TUBE:
    raise ValueError("Invalid radii. Ensure OUTER_RADIUS large enough and HOLE_DIAMETER not too big.")

GROOVE_D = WIRE_D + CLEARANCE
GROOVE_R = 0.5 * GROOVE_D
if GROOVE_DEPTH > GROOVE_R:
    raise ValueError("GROOVE_DEPTH must be <= GROOVE_R.")

SINK = max(0.0, GROOVE_R - GROOVE_DEPTH)

print(f"R_MAJOR={R_MAJOR:.3f} mm, R_TUBE={R_TUBE:.3f} mm")
print(f"GROOVE_D={GROOVE_D:.3f} mm, GROOVE_R={GROOVE_R:.3f} mm, GROOVE_DEPTH={GROOVE_DEPTH:.3f} mm => SINK={SINK:.3f} mm")

# =========================
# Helpers
# =========================
def ensure_units_mm():
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 0.001  # 1 BU = 1 mm
    s.unit_settings.length_unit = 'MILLIMETERS'

def get_output_dir():
    d = bpy.path.abspath(OUTPUT_DIR) if OUTPUT_DIR else (bpy.path.abspath("//") or bpy.app.tempdir or ".")
    os.makedirs(d, exist_ok=True)
    return d

def clear_scene_data_api():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

def make_torus_ops(name):
    # Ensure object mode (best effort)
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
    deps = bpy.context.evaluated_depsgraph_get()
    obj_eval = curve_obj.evaluated_get(deps)
    mesh = bpy.data.meshes.new_from_object(obj_eval)
    mesh_obj = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.collection.objects.link(mesh_obj)
    # remove curve
    bpy.data.objects.remove(curve_obj, do_unlink=True)
    return mesh_obj

def add_voxel_remesh(obj, voxel_size_mm):
    mod = obj.modifiers.new(name="VoxelRemesh", type='REMESH')
    mod.mode = 'VOXEL'
    mod.voxel_size = voxel_size_mm / 1000.0
    mod.use_smooth_shade = False
    return mod

def apply_modifier(obj, mod_name):
    # This op requires an active object context; set it explicitly.
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
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
    for m in ("io_mesh_stl", "io_scene_stl"):
        try:
            bpy.ops.preferences.addon_enable(module=m)
        except Exception:
            pass

def export_only_object_stl(obj, filepath):
    """Export ONLY this object by temporarily hiding all others and selecting just obj.
       Works even if the exporter ignores selection (common cause of 'only cutters exported')."""
    filepath = bpy.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    enable_stl_addon()

    # Save hide state and hide everything else
    hide_state = {}
    for o in bpy.data.objects:
        hide_state[o.name] = o.hide_get()
        o.hide_set(o != obj)

    # Select only obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Choose operator + args robustly
    if hasattr(bpy.ops.wm, "stl_export"):
        props = bpy.ops.wm.stl_export.get_rna_type().properties.keys()
        kwargs = dict(filepath=filepath)
        if "ascii_format" in props: kwargs["ascii_format"] = False
        if "apply_modifiers" in props: kwargs["apply_modifiers"] = True

        # Prefer exporting selection if supported
        if "export_selected_objects" in props:
            kwargs["export_selected_objects"] = True
        elif "use_selection" in props:
            kwargs["use_selection"] = True
        bpy.ops.wm.stl_export(**kwargs)

    elif hasattr(bpy.ops.export_mesh, "stl"):
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True, ascii=False)
    else:
        # Restore hide before raising
        for o in bpy.data.objects:
            o.hide_set(hide_state.get(o.name, False))
        raise RuntimeError("No STL export operator found.")

    # Restore hide state
    for o in bpy.data.objects:
        o.hide_set(hide_state.get(o.name, False))

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
    return (c * ct, c * st, s)  # unit

def make_lane_points(minor_offset_rad, q_val):
    pts = []
    for i in range(LANE_POINTS + 1):
        t = 2.0 * math.pi * i / LANE_POINTS
        theta = P * t
        phi   = q_val * t + minor_offset_rad

        x, y, z = torus_surface_point(theta, phi)
        nx, ny, nz = torus_normal(theta, phi)

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

    torus = make_torus_ops("GroovedTorus_full")

    solid = torus.copy()
    solid.data = torus.data.copy()
    bpy.context.collection.objects.link(solid)
    solid.name = "SolidTorus_full"

    lane_specs = [
        (+Q, 0), (+Q, 120), (+Q, 240),
        (-Q, 60), (-Q, 180), (-Q, 300)
    ]

    cutters = []
    for idx, (q_val, deg) in enumerate(lane_specs, start=1):
        pts = make_lane_points(math.radians(deg), q_val)
        tag = "A" if q_val > 0 else "B"
        curve = create_curve_from_points(f"LaneCurve_{idx:02d}_{tag}_{deg}deg", pts)
        cutter = curve_to_mesh_object(curve, f"LaneCutter_{idx:02d}_{tag}_{deg}deg")
        cutter.hide_render = True
        cutters.append(cutter)

    if USE_VOXEL_REMESH:
        add_voxel_remesh(torus, VOXEL_SIZE); apply_modifier(torus, "VoxelRemesh")
        for c in cutters:
            add_voxel_remesh(c, VOXEL_SIZE); apply_modifier(c, "VoxelRemesh")

    # Boolean subtract and delete cutters
    for i, c in enumerate(cutters, start=1):
        boolean_difference_apply(torus, c, name=f"Cut_{i:02d}")
        bpy.data.objects.remove(c, do_unlink=True)

    # Hard cleanup: remove any leftovers named Lane*
    for obj in list(bpy.data.objects):
        if obj.name.startswith("Lane"):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Force depsgraph update (ensures boolean result visible)
    bpy.context.view_layer.update()

    out_dir = get_output_dir()
    print("Output directory:", out_dir)

    if EXPORT_SOLID:
        export_only_object_stl(solid, os.path.join(out_dir, "rodin_torus_solid.stl"))
        print("Exported rodin_torus_solid.stl")

    if EXPORT_GROOVED:
        export_only_object_stl(torus, os.path.join(out_dir, "rodin_torus_grooved_6lane.stl"))
        print("Exported rodin_torus_grooved_6lane.stl")

    blend_path = os.path.join(out_dir, "rodin_torus_grooved_6lane.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("Saved:", blend_path)

    print("Final objects in scene:", [o.name for o in bpy.data.objects])

if __name__ == "__main__":
    main()