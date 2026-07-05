# Blender Python: 6-lane Rodin (p,q)=(5,12) groove mold (clamshell), with inward-sunk grooves
# Run inside Blender: Scripting tab -> open this file -> Run Script
#
# Outputs (next to the .blend, or set OUTPUT_DIR below):
#   - rodin_mold_full.stl
#   - rodin_mold_top.stl
#   - rodin_mold_bottom.stl
#   - rodin_mold.blend
#
# Notes:
# - This builds *true grooves* by subtracting tube-sweeps (curves with bevel) from a solid torus.
# - "6 separate lanes" are created via minor-angle offsets spaced by 60 degrees:
#     Group A (3-phase): 0, 120, 240 deg
#     Group B (mirrored set): 60, 180, 300 deg
#   The "mirrored" behavior is electrical (wind direction/polarity), not geometric overlap.
#
# Tested conceptually for Blender 3.6+ (Boolean EXACT solver).
# If the boolean fails, enable the optional voxel remesh steps below.

import bpy
import math
from math import sin, cos
from mathutils import Vector

# -------------------------
# User parameters (mm)
# -------------------------
P = 5
Q = 12

# Torus geometry (must fit <= 90 mm outer diameter)
R_MAJOR = 33.40    # mm
R_TUBE  = 9.00     # mm

# Lane placement around minor circle (degrees)
# 6 separate lanes (60° spacing): A={0,120,240}, B={60,180,300}
MINOR_OFFSETS_DEG = [0, 120, 240, 60, 180, 300]

# Groove sizing
WIRE_D = 1.20      # mm
CLEARANCE = 0.40   # mm
GROOVE_R = 0.5*(WIRE_D + CLEARANCE)  # cutter radius

# Inward sink: move groove centerline into the torus so outer skin remains thicker
SINK = 0.90        # mm (typical 0.6–1.2)

# Curve sampling
N_POINTS = 2200     # per lane (higher = smoother, slower)

# Mesh quality
TORUS_MAJOR_SEG = 256
TORUS_MINOR_SEG = 128
CURVE_BEVEL_RES = 12

# Clamshell split
SPLIT_Z = 0.0       # mm

# Alignment pegs
PEG_R = 2.0
PEG_H = 5.0
PEG_CLEAR = 0.25
PEG_ANGLES_DEG = [45, 135, 225, 315]
PEG_RAD = R_MAJOR + R_TUBE - 2.4

# Optional robustness helpers
USE_VOXEL_REMESH = False
VOXEL_SIZE = 0.35   # mm (0.25–0.6). Smaller = heavier.

# Output directory ("" means the current .blend directory)
OUTPUT_DIR = ""


# -------------------------
# Utilities
# -------------------------
def mm(v):  # keep everything in mm (STL is unitless; slicers interpret as mm)
    return v

def deselect_all():
    for o in bpy.context.selected_objects:
        o.select_set(False)

def delete_all_objects():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)

def ensure_scene_units_mm():
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    # Keep scale length at 1.0; we treat 1 Blender unit == 1 mm for modeling.
    scene.unit_settings.scale_length = 1.0

def get_output_dir():
    if OUTPUT_DIR:
        return bpy.path.abspath(OUTPUT_DIR)
    # default: directory of the current blend
    d = bpy.path.abspath("//")
    if not d:
        d = bpy.path.abspath("//")  # may still be empty if unsaved
    return d if d else "."

def set_object_name(obj, name):
    obj.name = name
    obj.data.name = name + "_data"

def apply_modifier(obj, mod_name):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod_name)

def add_boolean_difference(target_obj, cutter_obj, solver='EXACT'):
    mod = target_obj.modifiers.new(name="BooleanGrooves", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = solver
    mod.object = cutter_obj
    return mod

def add_voxel_remesh(obj, voxel_size):
    mod = obj.modifiers.new(name="VoxelRemesh", type='REMESH')
    mod.mode = 'VOXEL'
    mod.voxel_size = voxel_size
    mod.use_smooth_shade = True
    return mod

def export_stl(obj, filepath):
    deselect_all()
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True, global_scale=1.0, ascii=False)

def torus_point(theta, phi):
    # Torus param on surface
    x = (R_MAJOR + R_TUBE*cos(phi)) * cos(theta)
    y = (R_MAJOR + R_TUBE*cos(phi)) * sin(theta)
    z = R_TUBE * sin(phi)
    return Vector((x,y,z))

def torus_normal(theta, pt):
    # Unit normal from tube center to point
    center = Vector((R_MAJOR*cos(theta), R_MAJOR*sin(theta), 0.0))
    n = pt - center
    if n.length < 1e-9:
        return Vector((1,0,0))
    return n.normalized()

def make_lane_points(minor_offset_rad):
    pts = []
    for i in range(N_POINTS):
        t = 2.0*math.pi*i/(N_POINTS-1)
        theta = P*t
        phi = Q*t + minor_offset_rad
        p = torus_point(theta, phi)
        n = torus_normal(theta, p)
        p2 = p - SINK*n   # inward sink
        pts.append(p2)
    return pts

def create_curve_from_points(name, pts, bevel_radius):
    curve = bpy.data.curves.new(name=name, type='CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    spline = curve.splines.new('POLY')
    spline.points.add(len(pts)-1)
    for i,p in enumerate(pts):
        spline.points[i].co = (p.x, p.y, p.z, 1.0)

    curve.bevel_depth = bevel_radius
    curve.bevel_resolution = CURVE_BEVEL_RES
    curve.fill_mode = 'FULL'

    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return obj

def convert_to_mesh(obj):
    deselect_all()
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    return bpy.context.view_layer.objects.active

def join_objects(objs, name):
    deselect_all()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    set_object_name(joined, name)
    return joined

def create_base_torus():
    bpy.ops.mesh.primitive_torus_add(
        major_radius=R_MAJOR,
        minor_radius=R_TUBE,
        major_segments=TORUS_MAJOR_SEG,
        minor_segments=TORUS_MINOR_SEG,
        abso_major_rad=1.0,
        abso_minor_rad=0.5,
        align='WORLD',
        location=(0,0,0),
        rotation=(0,0,0)
    )
    tor = bpy.context.view_layer.objects.active
    set_object_name(tor, "BaseTorus")
    return tor

def make_split_cube(z_min, z_max, size_xy=400):
    # cube spanning [z_min, z_max]
    z_center = 0.5*(z_min+z_max)
    z_size = (z_max - z_min)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0,0,z_center))
    c = bpy.context.view_layer.objects.active
    c.scale = (0.5*size_xy, 0.5*size_xy, 0.5*z_size)
    bpy.ops.object.transform_apply(scale=True)
    return c

def boolean_intersect(obj, cutter, name):
    mod = obj.modifiers.new(name="BooleanIntersect", type='BOOLEAN')
    mod.operation = 'INTERSECT'
    mod.solver = 'EXACT'
    mod.object = cutter
    apply_modifier(obj, mod.name)
    set_object_name(obj, name)

def boolean_difference(obj, cutter, name=None):
    mod = obj.modifiers.new(name="BooleanDiff", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    apply_modifier(obj, mod.name)
    if name:
        set_object_name(obj, name)

def add_alignment_features(top_obj, bottom_obj):
    # Bottom pegs (additive)
    pegs = []
    for a in PEG_ANGLES_DEG:
        x = PEG_RAD*math.cos(math.radians(a))
        y = PEG_RAD*math.sin(math.radians(a))
        bpy.ops.mesh.primitive_cylinder_add(radius=PEG_R, depth=PEG_H, location=(x,y,SPLIT_Z - 0.5*PEG_H))
        cyl = bpy.context.view_layer.objects.active
        pegs.append(cyl)
    pegs_union = join_objects(pegs, "PegsUnion")
    # Union pegs into bottom
    mod = bottom_obj.modifiers.new(name="UnionPegs", type='BOOLEAN')
    mod.operation = 'UNION'
    mod.solver = 'EXACT'
    mod.object = pegs_union
    apply_modifier(bottom_obj, mod.name)
    # delete pegs object
    deselect_all()
    pegs_union.select_set(True)
    bpy.ops.object.delete()

    # Top holes (subtractive)
    holes = []
    for a in PEG_ANGLES_DEG:
        x = PEG_RAD*math.cos(math.radians(a))
        y = PEG_RAD*math.sin(math.radians(a))
        bpy.ops.mesh.primitive_cylinder_add(radius=PEG_R + PEG_CLEAR, depth=PEG_H + 0.6, location=(x,y,SPLIT_Z - 0.5*(PEG_H+0.6)))
        cyl = bpy.context.view_layer.objects.active
        holes.append(cyl)
    holes_union = join_objects(holes, "HolesUnion")
    boolean_difference(top_obj, holes_union, name="MoldTop")
    deselect_all()
    holes_union.select_set(True)
    bpy.ops.object.delete()

# -------------------------
# Main build
# -------------------------
def main():
    ensure_scene_units_mm()
    delete_all_objects()

    # Base torus
    base = create_base_torus()

    # Lane cutters as curves -> meshes
    lane_objs = []
    for idx, deg in enumerate(MINOR_OFFSETS_DEG, start=1):
        pts = make_lane_points(math.radians(deg))
        c = create_curve_from_points(f"LaneCurve_{idx:02d}_{deg}deg", pts, bevel_radius=GROOVE_R)
        lane_objs.append(c)

    # Convert to mesh and join
    cutter_meshes = [convert_to_mesh(o) for o in lane_objs]
    cutters = join_objects(cutter_meshes, "GrooveCutters")

    # Optional voxel remesh for robustness
    if USE_VOXEL_REMESH:
        add_voxel_remesh(cutters, VOXEL_SIZE)
        apply_modifier(cutters, "VoxelRemesh")

        add_voxel_remesh(base, VOXEL_SIZE)
        apply_modifier(base, "VoxelRemesh")

    # Boolean subtract grooves
    add_boolean_difference(base, cutters, solver='EXACT')
    apply_modifier(base, "BooleanGrooves")
    set_object_name(base, "MoldFull")

    # We can hide cutters to keep file clean
    cutters.hide_set(True)
    cutters.hide_render = True

    # Make top/bottom halves
    top = base.copy()
    top.data = base.data.copy()
    bpy.context.collection.objects.link(top)
    set_object_name(top, "MoldTop_raw")

    bottom = base.copy()
    bottom.data = base.data.copy()
    bpy.context.collection.objects.link(bottom)
    set_object_name(bottom, "MoldBottom_raw")

    # Split via intersection with half-cubes
    cube_top = make_split_cube(SPLIT_Z, SPLIT_Z + 250)
    boolean_intersect(top, cube_top, "MoldTop")
    deselect_all()
    cube_top.select_set(True); bpy.ops.object.delete()

    cube_bot = make_split_cube(SPLIT_Z - 250, SPLIT_Z)
    boolean_intersect(bottom, cube_bot, "MoldBottom")
    deselect_all()
    cube_bot.select_set(True); bpy.ops.object.delete()

    # Add alignment pegs/holes
    add_alignment_features(top, bottom)

    # Export
    out_dir = get_output_dir()
    full_stl = bpy.path.abspath(out_dir + "/rodin_mold_full.stl")
    top_stl  = bpy.path.abspath(out_dir + "/rodin_mold_top.stl")
    bot_stl  = bpy.path.abspath(out_dir + "/rodin_mold_bottom.stl")

    export_stl(base, full_stl)
    export_stl(top, top_stl)
    export_stl(bottom, bot_stl)

    # Save blend
    blend_path = bpy.path.abspath(out_dir + "/rodin_mold.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

    print("Done.")
    print("Saved:", blend_path)
    print("Exported:", full_stl, top_stl, bot_stl)

if __name__ == "__main__":
    main()