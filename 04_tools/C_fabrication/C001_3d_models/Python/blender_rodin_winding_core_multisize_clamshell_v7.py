
import bpy
import os
import math

# =========================
# User settings
# =========================
# Output directory (set to a writable folder). If empty, uses folder of saved .blend, else Blender temp dir.
OUTPUT_DIR = r"C:\workspace\projects\SwirlStringTheory\images\Python"  # e.g. r"C:\Users\Omar\Desktop\rodin_out"

# Geometry (mm)
OUTER_RADIUS  = 45.0   # mm  => outer diameter = 90 mm
HOLE_DIAMETER = 10.0   # mm  => inner hole diameter (must be > 0)

# Lane topology (Rodin-like)
P = 5        # major wraps
Q = 12       # minor wraps (handedness via sign)
SAMPLES = 2200

# Lane offsets (degrees) and handedness:
# Group A: 0,120,240 with +Q
# Group B: 60,180,300 with -Q (mirrored handedness)
LANE_SPECS = [
    (+Q,   0), (+Q, 120), (+Q, 240),
    (-Q,  60), (-Q, 180), (-Q, 300),
]

# Wire variants (wire_d_mm, clearance_mm, groove_depth_mm, tag)
WIRE_VARIANTS = [
    (0.8, 0.35, 0.50, "0p8"),
    (1.2, 0.40, 0.65, "1p2"),
]

# Split into two halves for easier wire placement and assembly
MAKE_CLAMSHELL = True
SPLIT_PLANE = "X"   # "X" (recommended) or "Z"

# Alignment pegs (mm)
PEG_RADIUS = 2.0
PEG_LENGTH = 12.0          # along split axis
PEG_HOLE_CLEARANCE = 0.25  # radial clearance

# Boolean robustness
USE_VOXEL_REMESH = False
VOXEL_SIZE = 0.35

# =========================
# Utilities
# =========================
def get_output_dir():
    if OUTPUT_DIR:
        d = bpy.path.abspath(OUTPUT_DIR)
    else:
        d = bpy.path.abspath("//")
        if not d:
            d = bpy.app.tempdir
    if not d:
        d = "."
    os.makedirs(d, exist_ok=True)
    return d

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # purge orphan data
    for _ in range(2):
        try:
            bpy.ops.outliner.orphans_purge(do_recursive=True)
        except Exception:
            pass

def deselect_all():
    for o in bpy.context.selected_objects:
        o.select_set(False)

def set_active(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

def apply_modifier(obj, mod_name):
    set_active(obj)
    bpy.ops.object.modifier_apply(modifier=mod_name)

def add_voxel_remesh(obj, voxel_size):
    mod = obj.modifiers.new(name="VoxelRemesh", type='REMESH')
    mod.mode = 'VOXEL'
    mod.voxel_size = voxel_size
    mod.use_smooth_shade = False
    return mod

def boolean(obj, cutter, op='DIFFERENCE', name="Bool"):
    mod = obj.modifiers.new(name=name, type='BOOLEAN')
    mod.operation = op
    mod.object = cutter
    try:
        mod.solver = 'EXACT'
    except Exception:
        pass
    apply_modifier(obj, mod.name)

def _enable_stl_addon_if_needed():
    for module in ("io_mesh_stl", "io_scene_stl"):
        try:
            bpy.ops.preferences.addon_enable(module=module)
        except Exception:
            pass

def _call_op_filtered(op, kwargs):
    props = None
    try:
        props = op.get_rna_type().properties.keys()
    except Exception:
        props = None
    if props:
        kwargs = {k:v for k,v in kwargs.items() if k in props}
    return op(**kwargs)

def export_stl(obj, filepath):
    filepath = bpy.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    deselect_all()
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    _enable_stl_addon_if_needed()

    if hasattr(bpy.ops.wm, "stl_export"):
        _call_op_filtered(
            bpy.ops.wm.stl_export,
            dict(filepath=filepath, export_selected_objects=True, ascii_format=False, global_scale=1.0, apply_modifiers=True)
        )
        return

    if hasattr(bpy.ops.export_mesh, "stl"):
        _call_op_filtered(
            bpy.ops.export_mesh.stl,
            dict(filepath=filepath, use_selection=True, ascii=False, global_scale=1.0, use_mesh_modifiers=True)
        )
        return

    raise RuntimeError("No STL export operator found. Enable the STL addon.")

def make_curve_from_points(name, pts, bevel_radius):
    curve_data = bpy.data.curves.new(name=name+"_Curve", type='CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(pts) - 1)
    for i,(x,y,z) in enumerate(pts):
        spline.points[i].co = (x, y, z, 1.0)
    curve_data.bevel_depth = bevel_radius
    curve_data.bevel_resolution = 6
    curve_data.resolution_u = 8

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    return obj

def convert_to_mesh(obj):
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

def torus_point(R, r, theta, phi):
    x = (R + r*math.cos(phi)) * math.cos(theta)
    y = (R + r*math.cos(phi)) * math.sin(theta)
    z = r*math.sin(phi)
    return (x,y,z)

def make_lane_points(R, r, p, q, minor_offset_rad, n=SAMPLES):
    pts = []
    for i in range(n):
        t = 2*math.pi * (i/(n-1))
        theta = p*t
        phi   = q*t + minor_offset_rad
        pts.append(torus_point(R, r, theta, phi))
    return pts

def make_halfspace_cube(axis="X", side="+", size=500.0):
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0,0,0))
    c = bpy.context.view_layer.objects.active
    if axis == "X":
        c.location.x = +size/4.0 if side == "+" else -size/4.0
        c.scale.x = 0.5
    elif axis == "Z":
        c.location.z = +size/4.0 if side == "+" else -size/4.0
        c.scale.z = 0.5
    else:
        raise ValueError("axis must be X or Z")
    return c

def add_alignment_pegs(halfA, halfB, axis="X", R_major=25.0):
    positions = [(0.0, +R_major, 0.0), (0.0, -R_major, 0.0)]
    for k,(x,y,z) in enumerate(positions, start=1):
        # Peg on halfA
        if axis == "X":
            loc = (-PEG_LENGTH/4.0, y, z)  # embed into negative-X half
            rot = (0.0, math.radians(90.0), 0.0)  # axis along X
        else:  # Z split
            loc = (x, y, -PEG_LENGTH/4.0)
            rot = (0.0, 0.0, 0.0)  # axis along Z
        bpy.ops.mesh.primitive_cylinder_add(radius=PEG_RADIUS, depth=PEG_LENGTH, location=loc, rotation=rot)
        peg = bpy.context.view_layer.objects.active
        peg.name = f"Peg_{k:02d}"

        if USE_VOXEL_REMESH:
            add_voxel_remesh(peg, VOXEL_SIZE); apply_modifier(peg, "VoxelRemesh")
            add_voxel_remesh(halfA, VOXEL_SIZE); apply_modifier(halfA, "VoxelRemesh")

        boolean(halfA, peg, op='UNION', name=f"UnionPeg{k:02d}")

        # Hole in halfB (slightly larger)
        if axis == "X":
            hole_loc = (+PEG_LENGTH/4.0, y, z)
            hole_rot = (0.0, math.radians(90.0), 0.0)
        else:
            hole_loc = (x, y, +PEG_LENGTH/4.0)
            hole_rot = (0.0, 0.0, 0.0)
        bpy.ops.mesh.primitive_cylinder_add(radius=PEG_RADIUS+PEG_HOLE_CLEARANCE, depth=PEG_LENGTH, location=hole_loc, rotation=hole_rot)
        hole = bpy.context.view_layer.objects.active
        hole.name = f"Hole_{k:02d}"

        if USE_VOXEL_REMESH:
            add_voxel_remesh(hole, VOXEL_SIZE); apply_modifier(hole, "VoxelRemesh")
            add_voxel_remesh(halfB, VOXEL_SIZE); apply_modifier(halfB, "VoxelRemesh")

        boolean(halfB, hole, op='DIFFERENCE', name=f"DiffHole{k:02d}")

        deselect_all()
        peg.select_set(True); hole.select_set(True)
        bpy.ops.object.delete()

def build_core_for_variant(wire_d, clearance, groove_depth, tag, out_dir):
    # Derive radii from OUTER_RADIUS and HOLE_DIAMETER
    R_MAJOR = 0.5*(OUTER_RADIUS + 0.5*HOLE_DIAMETER)
    R_TUBE  = 0.5*(OUTER_RADIUS - 0.5*HOLE_DIAMETER)
    if R_TUBE <= 0 or R_MAJOR <= R_TUBE:
        raise ValueError("Invalid radii: need R_MAJOR > R_TUBE > 0.")

    groove_r = 0.5*(wire_d + clearance)
    sink = max(0.0, groove_r - groove_depth)

    print(f"[{tag}] R_MAJOR={R_MAJOR:.3f} mm, R_TUBE={R_TUBE:.3f} mm; wire={wire_d}mm, clearance={clearance}mm => groove_r={groove_r:.3f}mm, depth={groove_depth:.3f}mm, sink={sink:.3f}mm")

    # Base torus
    bpy.ops.mesh.primitive_torus_add(
        major_radius=R_MAJOR,
        minor_radius=R_TUBE,
        major_segments=192,
        minor_segments=96,
        location=(0,0,0)
    )
    base = bpy.context.view_layer.objects.active
    base.name = f"WindingCore_{tag}_base"

    # Build 6 lane cutters
    lane_curves = []
    for idx,(q_val, deg) in enumerate(LANE_SPECS, start=1):
        pts = make_lane_points(R_MAJOR, R_TUBE, P, q_val, math.radians(deg))
        c = make_curve_from_points(f"Lane_{tag}_{idx:02d}", pts, bevel_radius=groove_r)
        lane_curves.append(c)

    lane_meshes = [convert_to_mesh(o) for o in lane_curves]
    cutters = join_objects(lane_meshes, f"GrooveCutters_{tag}")
    cutters.display_type = 'WIRE'
    cutters.hide_render = True

    # Sink cutters inward using shrink/fatten (approx)
    if sink > 1e-6:
        set_active(cutters)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.shrink_fatten(value=-sink)
        bpy.ops.object.mode_set(mode='OBJECT')

    if USE_VOXEL_REMESH:
        add_voxel_remesh(base, VOXEL_SIZE); apply_modifier(base, "VoxelRemesh")
        add_voxel_remesh(cutters, VOXEL_SIZE); apply_modifier(cutters, "VoxelRemesh")

    boolean(base, cutters, op='DIFFERENCE', name=f"Grooves_{tag}")
    base.name = f"WindingCore_{tag}_solid"

    # Export full core
    full_path = os.path.join(out_dir, f"winding_core_{tag}_full.stl")
    export_stl(base, full_path)

    halves = []
    if MAKE_CLAMSHELL:
        cube_pos = make_halfspace_cube(axis=SPLIT_PLANE, side="+", size=500.0)
        cube_neg = make_halfspace_cube(axis=SPLIT_PLANE, side="-", size=500.0)

        a = base.copy(); a.data = base.data.copy(); bpy.context.collection.objects.link(a)
        b = base.copy(); b.data = base.data.copy(); bpy.context.collection.objects.link(b)
        a.name = f"WindingCore_{tag}_HalfA"
        b.name = f"WindingCore_{tag}_HalfB"

        boolean(a, cube_neg, op='INTERSECT', name="IntersectNeg")
        boolean(b, cube_pos, op='INTERSECT', name="IntersectPos")

        add_alignment_pegs(a, b, axis=SPLIT_PLANE, R_major=R_MAJOR)

        deselect_all()
        cube_pos.select_set(True); cube_neg.select_set(True)
        bpy.ops.object.delete()

        a_path = os.path.join(out_dir, f"winding_core_{tag}_halfA.stl")
        b_path = os.path.join(out_dir, f"winding_core_{tag}_halfB.stl")
        export_stl(a, a_path)
        export_stl(b, b_path)
        halves = [a_path, b_path]

    cutters.hide_set(True)
    return full_path, halves

def main():
    out_dir = get_output_dir()
    print("Output directory:", out_dir)

    for (wire_d, clearance, groove_depth, tag) in WIRE_VARIANTS:
        clear_scene()
        full_path, halves = build_core_for_variant(wire_d, clearance, groove_depth, tag, out_dir)
        print(f"[{tag}] Exported:", full_path)
        for h in halves:
            print(f"[{tag}] Exported:", h)

        blend_path = os.path.join(out_dir, f"winding_core_{tag}.blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)

if __name__ == "__main__":
    main()