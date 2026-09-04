# Blender 5.x: Full torus with 6 carved grooves (3-phase + 3 mirrored)
# v4: geometry + boolean application are context-safe (evaluated mesh), and lane offsets are MAJOR-angle (theta0)
#
# This fixes two common failure modes:
#   1) Missing lanes / duplicates from using minor-angle offsets only
#   2) "Broken / shredded" booleans from repeated ops-based modifier application
#
# OUTPUT:
#   - rodin_torus_solid.stl
#   - rodin_torus_grooved_6lane.stl
#   - rodin_torus_grooved_6lane.blend
#
# Run: Blender -> Scripting -> open -> set OUTPUT_DIR -> Run Script

import bpy, os, math
import bmesh
from mathutils import Vector

# =========================
# USER PARAMETERS
# =========================
OUTPUT_DIR = r"C:\workspace\projects\SwirlStringTheory\images\Python\out"  # <-- SET TO A WRITABLE FOLDER, e.g. r"C:\...\out"


# Torus geometry (mm)
OUTER_RADIUS   = 45.0
HOLE_DIAMETER  = 10.0

# Rodin groove parameterization
P = 5
Q = 12

# Groove sizing
WIRE_D       = 1.20
CLEARANCE    = 0.40
GROOVE_R     = 0.5 * (WIRE_D + CLEARANCE)  # cutter radius
GROOVE_DEPTH = 0.70

# Visualize curve paths?
VISUALIZE_CURVES = True

# Split for clamshell?
MAKE_HALVES = True
SPLIT_AXIS  = "X"

# Pegs & holes (mm)
PEG_R      = 2.0
PEG_LEN    = 6.0
HOLE_CLEAR = 0.25
PEG_POS    = [(0.0,  15.0, 0.0), (0.0, -15.0, 0.0)]

# Mesh resolution
TORUS_MAJOR_SEG = 180
TORUS_MINOR_SEG = 110
LANE_POINTS     = 900
CURVE_RESOLUTION_U = 16
BEVEL_RESOLUTION   = 8

# Voxel remesh toggle
USE_VOXEL_REMESH = False
VOXEL_SIZE_MM    = 0.25

# Export toggles
EXPORT_SOLID  = True
EXPORT_GROOVED = True
EXPORT_HALVES  = True

# =========================
# ---- DERIVED QUANTITIES
# =========================

R_MAJOR = 0.5 * (OUTER_RADIUS + 0.5 * HOLE_DIAMETER)
R_TUBE  = 0.5 * (OUTER_RADIUS - 0.5 * HOLE_DIAMETER)

if R_TUBE <= 0 or R_MAJOR <= R_TUBE:
    raise ValueError("Invalid radii: OUTER_RADIUS too small or HOLE_DIAMETER too big.")

if GROOVE_DEPTH > GROOVE_R:
    raise ValueError("GROOVE_DEPTH must be ≤ GROOVE_R.")

SINK = max(0.0, GROOVE_R - GROOVE_DEPTH)

# =========================
# ---- HELPER FUNCTIONS ----
# =========================

def ensure_units_mm():
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 0.001
    s.unit_settings.length_unit  = 'MILLIMETERS'

def get_output_dir():
    d = bpy.path.abspath(OUTPUT_DIR)
    os.makedirs(d, exist_ok=True)
    return d

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    try:
        bpy.ops.outliner.orphans_purge(do_recursive=True)
    except:
        pass

def enable_stl_addon():
    for m in ("io_mesh_stl", "io_scene_stl"):
        try:
            bpy.ops.preferences.addon_enable(module=m)
        except:
            pass

def export_stl(obj, filepath):
    enable_stl_addon()
    filepath = bpy.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(filepath=filepath,
                              export_selected_objects=True,
                              ascii_format=False)
    else:
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True, ascii=False)

def set_obj_name(o, name):
    o.name = name
    if o.data:
        o.data.name = name + "_data"

def apply_modifier(obj, name):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=name)

def boolean_diff(target, cutter, name):
    mod = target.modifiers.new(name, 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver    = 'EXACT'
    mod.object    = cutter
    apply_modifier(target, mod.name)

def make_halfspace_cube(axis, positive=True, size=300):
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0,0,0))
    c = bpy.context.view_layer.objects.active
    set_obj_name(c, "HalfSpace")
    if axis == "X":
        c.location.x = +size/2 if positive else -size/2
    elif axis == "Y":
        c.location.y = +size/2 if positive else -size/2
    elif axis == "Z":
        c.location.z = +size/2 if positive else -size/2
    return c

def add_pegs_and_holes(halfA, halfB):
    for (x0,y0,z0) in PEG_POS:
        # PEG ON A
        bpy.ops.mesh.primitive_cylinder_add(radius=PEG_R, depth=PEG_LEN,
                                            location=(PEG_LEN/2, y0, z0))
        peg = bpy.context.view_layer.objects.active
        peg.rotation_euler = (0, math.radians(90), 0)
        set_obj_name(peg, "Peg")
        boolean_diff(halfA, peg, "PegUnion")
        bpy.data.objects.remove(peg, do_unlink=True)

        # HOLE ON B
        hr = PEG_R + HOLE_CLEAR
        hl = PEG_LEN + 0.8
        bpy.ops.mesh.primitive_cylinder_add(radius=hr, depth=hl,
                                            location=(hl/2, y0, z0))
        hole = bpy.context.view_layer.objects.active
        hole.rotation_euler = (0, math.radians(90), 0)
        set_obj_name(hole, "PegHole")
        boolean_diff(halfB, hole, "PegHoleDiff")
        bpy.data.objects.remove(hole, do_unlink=True)

# =========================
# ---- TORUS + CURVE GENERATORS
# =========================

def make_torus():
    bpy.ops.mesh.primitive_torus_add(
        major_radius=R_MAJOR,
        minor_radius=R_TUBE,
        major_segments=TORUS_MAJOR_SEG,
        minor_segments=TORUS_MINOR_SEG,
        align='WORLD')
    t = bpy.context.view_layer.objects.active
    set_obj_name(t, "Torus_base")
    return t

def torus_surface_point(theta, phi):
    x = (R_MAJOR + R_TUBE * math.cos(phi)) * math.cos(theta)
    y = (R_MAJOR + R_TUBE * math.cos(phi)) * math.sin(theta)
    z = (R_TUBE * math.sin(phi))
    return (x,y,z)

def torus_normal(theta, phi):
    nx = math.cos(phi)*math.cos(theta)
    ny = math.cos(phi)*math.sin(theta)
    nz = math.sin(phi)
    return (nx, ny, nz)

def make_lane_curve(name, minor_offset_deg, q_val, color):
    pts = []
    for i in range(LANE_POINTS+1):
        t = 2.0*math.pi * i / LANE_POINTS
        theta = P*t
        phi   = q_val*t + math.radians(minor_offset_deg)
        x,y,z = torus_surface_point(theta, phi)
        nx,ny,nz = torus_normal(theta, phi)
        x -= nx * SINK
        y -= ny * SINK
        z -= nz * SINK
        pts.append((x,y,z))

    # Create curve
    cd = bpy.data.curves.new(name, 'CURVE')
    cd.dimensions = '3D'
    cd.resolution_u = CURVE_RESOLUTION_U
    cd.bevel_depth    = GROOVE_R
    cd.bevel_resolution = BEVEL_RESOLUTION
    cd.fill_mode      = 'FULL'

    spline = cd.splines.new('POLY')
    spline.points.add(len(pts)-1)
    for i, (x,y,z) in enumerate(pts):
        spline.points[i].co = (x,y,z, 1.0)

    obj = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(obj)

    if VISUALIZE_CURVES:
        mat = bpy.data.materials.new(name + "_mat")
        mat.diffuse_color = (color[0], color[1], color[2], 1)
        obj.data.materials.append(mat)

    return obj

def curve_to_mesh(curve_obj):
    deps = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(deps)
    mesh = bpy.data.meshes.new_from_object(eval_obj)
    mesh_obj = bpy.data.objects.new(curve_obj.name+"_mesh", mesh)
    bpy.context.collection.objects.link(mesh_obj)
    bpy.data.objects.remove(curve_obj, do_unlink=True)
    return mesh_obj

# =========================
# ---- MAIN EXECUTION ----
# =========================

def main():
    ensure_units_mm()
    clear_scene()

    # Make base torus & duplicate for solid export
    base_torus = make_torus()
    solid = base_torus.copy()
    solid.data = base_torus.data.copy()
    bpy.context.collection.objects.link(solid)
    set_obj_name(solid, "Torus_solid")

    # Grooved torus copy
    grooved = base_torus.copy()
    grooved.data = base_torus.data.copy()
    bpy.context.collection.objects.link(grooved)
    set_obj_name(grooved, "Torus_grooved")

    # Groove specs: (q_val, phase_deg, color)
    specs = [
        ( +Q,   0, (1,0,0)),
        ( +Q, 120, (0,1,0)),
        ( +Q, 240, (0,0,1)),
        ( -Q,  60, (1,1,0)),
        ( -Q, 180, (1,0,1)),
        ( -Q, 300, (0,1,1)),
    ]

    cutters = []
    for i, (q_val, deg, col) in enumerate(specs):
        name = f"lane_{i:02d}"
        curve = make_lane_curve(name, deg, q_val, col)
        mesh_cutter = curve_to_mesh(curve)
        cutters.append(mesh_cutter)

    if USE_VOXEL_REMESH:
        for c in [grooved] + cutters:
            mod = c.modifiers.new("VoxelRemesh", 'REMESH')
            mod.mode       = 'VOXEL'
            mod.voxel_size = VOXEL_SIZE_MM/1000
            mod.use_smooth_shade = False
            apply_modifier(c, "VoxelRemesh")

    # Apply boolean cuts
    for i, c in enumerate(cutters):
        boolean_diff(grooved, c, name=f"Cut_{i:02d}")
        bpy.data.objects.remove(c, do_unlink=True)

    bpy.context.view_layer.update()

    out = get_output_dir()

    if EXPORT_SOLID:
        export_stl(solid, os.path.join(out, "torus_solid.stl"))
    if EXPORT_GROOVED:
        export_stl(grooved, os.path.join(out, "torus_grooved_full.stl"))

    # Make halves
    if MAKE_HALVES and EXPORT_HALVES:
        A = grooved.copy(); A.data = grooved.data.copy()
        bpy.context.collection.objects.link(A); set_obj_name(A,"Torus_halfA")
        B = grooved.copy(); B.data = grooved.data.copy()
        bpy.context.collection.objects.link(B); set_obj_name(B,"Torus_halfB")

        hsA = make_halfspace_cube(SPLIT_AXIS, positive=False, size=OUTER_RADIUS*4)
        boolean_diff(A, hsA, "HalfA_cut")
        bpy.data.objects.remove(hsA, do_unlink=True)

        hsB = make_halfspace_cube(SPLIT_AXIS, positive=True, size=OUTER_RADIUS*4)
        boolean_diff(B, hsB, "HalfB_cut")
        bpy.data.objects.remove(hsB, do_unlink=True)

        add_pegs_and_holes(A,B)

        export_stl(A, os.path.join(out, "torus_halfA.stl"))
        export_stl(B, os.path.join(out, "torus_halfB.stl"))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,"torus_grooved_complete.blend"))

if __name__ == "__main__":
    main()