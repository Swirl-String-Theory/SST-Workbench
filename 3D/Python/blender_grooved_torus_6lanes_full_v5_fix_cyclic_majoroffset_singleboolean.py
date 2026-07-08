# Blender 5.x script (v5): Full torus with 6 *continuous* carved grooves (3-phase + 3 mirrored)
# Fixes the two issues you described:
#   - "Broken somewhere" grooves: caused by non-cyclic curve tubes and duplicate end-point caps
#   - "Only 4 out of 6": caused by using only minor (phi) offsets; we now offset in MAJOR angle (theta0)
#
# Core changes vs your pasted script:
#   1) Curves are made cyclic (spline.use_cyclic_u = True) and we DO NOT add the duplicate endpoint.
#   2) Lane phasing is done by MAJOR-angle offsets theta0_deg, with Q sign giving handedness.
#   3) All 6 cutters are combined into ONE mesh, then ONE boolean difference is applied.
#   4) Boolean is applied via evaluated mesh (depsgraph), avoiding fragile ops-context issues.
#
# OUTPUT:
#   - torus_grooved_full.stl
#   - torus_grooved_complete.blend
#
# Run: Blender -> Scripting -> Open -> set OUTPUT_DIR -> Run Script

import bpy, os, math
from mathutils import Vector

# =========================
# USER PARAMETERS
# =========================
OUTPUT_DIR = r"C:\\workspace\\projects\\SwirlStringTheory\\images\\Python\\out"

# Torus geometry (mm)
OUTER_RADIUS_MM   = 45.0   # 90mm OD
HOLE_DIAMETER_MM  = 10.0   # small center hole

# "Rodin-like" torus-knot parameters
P = 5
Q = 12

# Groove sizing (mm)
WIRE_D_MM       = 1.20
CLEARANCE_MM    = 0.40
GROOVE_DEPTH_MM = 0.70

# Mesh resolution / quality
TORUS_MAJOR_SEG = 220
TORUS_MINOR_SEG = 140
LANE_POINTS     = 1400   # increase to reduce faceting and boolean stress
CURVE_RESOLUTION_U = 24
BEVEL_RESOLUTION   = 10

# Debug visualization of CURVE paths (curves are deleted after conversion anyway)
VISUALIZE_CURVES = False

# Optional healing (usually not needed if cyclic+single boolean)
POST_VOXEL_REMESH = False
VOXEL_SIZE_MM     = 0.30

# Exports
EXPORT_GROOVED = True

# =========================
# ---- DERIVED QUANTITIES
# =========================
R_MAJOR = 0.5 * (OUTER_RADIUS_MM + 0.5 * HOLE_DIAMETER_MM)
R_TUBE  = 0.5 * (OUTER_RADIUS_MM - 0.5 * HOLE_DIAMETER_MM)

if R_TUBE <= 0 or R_MAJOR <= R_TUBE:
    raise ValueError("Invalid radii: OUTER_RADIUS_MM too small or HOLE_DIAMETER_MM too big.")

GROOVE_R = 0.5 * (WIRE_D_MM + CLEARANCE_MM)  # cutter radius
if GROOVE_DEPTH_MM > GROOVE_R:
    raise ValueError("GROOVE_DEPTH_MM must be <= GROOVE_R.")

SINK = max(0.0, GROOVE_R - GROOVE_DEPTH_MM)

print(f"[v5] R_MAJOR={R_MAJOR:.3f} mm, R_TUBE={R_TUBE:.3f} mm")
print(f"[v5] GROOVE_R={GROOVE_R:.3f} mm, DEPTH={GROOVE_DEPTH_MM:.3f} mm => SINK={SINK:.3f} mm")

# =========================
# ---- HELPERS (robust)
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

def clear_scene_api():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for datablock in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for b in list(datablock):
            if b.users == 0:
                datablock.remove(b)

def enable_stl_addon():
    for m in ("io_mesh_stl", "io_scene_stl"):
        try:
            bpy.ops.preferences.addon_enable(module=m)
        except:
            pass

def export_only_object_stl(obj, filepath):
    enable_stl_addon()
    filepath = bpy.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    hide_state = {}
    for o in bpy.data.objects:
        hide_state[o.name] = o.hide_get()
        o.hide_set(o != obj)

    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if hasattr(bpy.ops.wm, "stl_export"):
        props = bpy.ops.wm.stl_export.get_rna_type().properties.keys()
        kwargs = dict(filepath=filepath)
        if "ascii_format" in props: kwargs["ascii_format"] = False
        if "apply_modifiers" in props: kwargs["apply_modifiers"] = True
        if "export_selected_objects" in props:
            kwargs["export_selected_objects"] = True
        elif "use_selection" in props:
            kwargs["use_selection"] = True
        bpy.ops.wm.stl_export(**kwargs)
    else:
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True, ascii=False)

    for o in bpy.data.objects:
        o.hide_set(hide_state.get(o.name, False))

def apply_all_modifiers_eval(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(deps)
    new_mesh = bpy.data.meshes.new_from_object(obj_eval)
    old_mesh = obj.data
    obj.data = new_mesh
    obj.modifiers.clear()
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)

def join_meshes_api(objs, name="Joined"):
    import bmesh
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    joined = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(joined)
    return joined

# =========================
# ---- TORUS + CURVE GENERATORS
# =========================
def make_torus(name="Torus"):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=R_MAJOR,
        minor_radius=R_TUBE,
        major_segments=TORUS_MAJOR_SEG,
        minor_segments=TORUS_MINOR_SEG,
        align='WORLD',
        location=(0,0,0),
        rotation=(0,0,0)
    )
    t = bpy.context.view_layer.objects.active
    t.name = name
    t.data.name = name + "_mesh"
    return t

def torus_surface_point(theta, phi):
    x = (R_MAJOR + R_TUBE * math.cos(phi)) * math.cos(theta)
    y = (R_MAJOR + R_TUBE * math.cos(phi)) * math.sin(theta)
    z = (R_TUBE * math.sin(phi))
    return Vector((x,y,z))

def torus_normal(theta, phi):
    nx = math.cos(phi)*math.cos(theta)
    ny = math.cos(phi)*math.sin(theta)
    nz = math.sin(phi)
    return Vector((nx, ny, nz))

def make_lane_curve(name, theta0_deg, q_val, color=(1,1,1)):
    pts = []
    theta0 = math.radians(theta0_deg)

    for i in range(LANE_POINTS):
        t = 2.0*math.pi * i / LANE_POINTS
        theta = P*t + theta0
        phi   = q_val*t
        p = torus_surface_point(theta, phi)
        n = torus_normal(theta, phi)
        p = p - n * SINK
        pts.append(p)

    cd = bpy.data.curves.new(name, 'CURVE')
    cd.dimensions = '3D'
    cd.resolution_u = CURVE_RESOLUTION_U
    cd.bevel_depth = GROOVE_R
    cd.bevel_resolution = BEVEL_RESOLUTION
    cd.fill_mode = 'FULL'

    spline = cd.splines.new('POLY')
    spline.points.add(len(pts)-1)
    for i, p in enumerate(pts):
        spline.points[i].co = (p.x, p.y, p.z, 1.0)
    spline.use_cyclic_u = True  # KEY FIX

    obj = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(obj)

    if VISUALIZE_CURVES:
        mat = bpy.data.materials.new(name + "_mat")
        mat.diffuse_color = (color[0], color[1], color[2], 1.0)
        obj.data.materials.append(mat)

    return obj

def curve_to_mesh(curve_obj, out_name):
    deps = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(deps)
    mesh = bpy.data.meshes.new_from_object(eval_obj)
    mesh_obj = bpy.data.objects.new(out_name, mesh)
    bpy.context.collection.objects.link(mesh_obj)
    bpy.data.objects.remove(curve_obj, do_unlink=True)
    return mesh_obj

# =========================
# ---- MAIN EXECUTION
# =========================
def main():
    ensure_units_mm()
    clear_scene_api()

    grooved = make_torus("Torus_grooved")

    specs = [
        (  0, +Q, (1,0,0)),
        (120, +Q, (0,1,0)),
        (240, +Q, (0,0,1)),
        ( 60, -Q, (1,1,0)),
        (180, -Q, (1,0,1)),
        (300, -Q, (0,1,1)),
    ]

    cutters = []
    for i, (theta0_deg, q_val, col) in enumerate(specs):
        c = make_lane_curve(f"lane_curve_{i:02d}", theta0_deg, q_val, col)
        m = curve_to_mesh(c, f"lane_cutter_{i:02d}")
        cutters.append(m)

    cutter_all = join_meshes_api(cutters, "GrooveCutters_ALL")

    for o in cutters:
        bpy.data.objects.remove(o, do_unlink=True)

    mod = grooved.modifiers.new("CutGrooves", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter_all

    apply_all_modifiers_eval(grooved)

    if POST_VOXEL_REMESH:
        rem = grooved.modifiers.new("PostVoxel", 'REMESH')
        rem.mode = 'VOXEL'
        rem.voxel_size = VOXEL_SIZE_MM/1000.0
        rem.use_smooth_shade = False
        apply_all_modifiers_eval(grooved)

    bpy.data.objects.remove(cutter_all, do_unlink=True)

    bpy.context.view_layer.update()

    out = get_output_dir()

    if EXPORT_GROOVED:
        export_only_object_stl(grooved, os.path.join(out, "torus_grooved_full.stl"))
        print("[v5] Exported torus_grooved_full.stl")

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "torus_grooved_complete.blend"))
    print("[v5] Saved torus_grooved_complete.blend")
    print("[v5] Final objects:", [o.name for o in bpy.data.objects])

if __name__ == "__main__":
    main()