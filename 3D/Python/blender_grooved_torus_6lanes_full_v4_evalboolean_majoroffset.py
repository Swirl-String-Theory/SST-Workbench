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
OUTPUT_DIR = r"."  # <-- SET TO A WRITABLE FOLDER, e.g. r"C:\...\out"

# Size constraint: keep within <= 90mm OD for 100mm build volume
OUTER_RADIUS_MM  = 45.0   # mm  (outer diameter = 90mm)
HOLE_DIAMETER_MM = 10.0   # mm  (center hole diameter)

# Lane (p,q) "Rodin-like" torus-knot parameters
P = 5
Q = 12

# Wire / groove sizing (mm)
WIRE_D_MM       = 1.20   # set 0.80 or 1.20
CLEARANCE_MM    = 0.40   # total diameter clearance (0.25–0.45 typical)
GROOVE_DEPTH_MM = 0.70   # visible depth, must be <= groove radius

# Lane quality
LANE_POINTS = 1100        # more points => smoother, better boolean
CUTTER_RADIAL_SEG = 14    # tube cross-section segments

# Torus quality
TORUS_MAJOR_SEG = 220
TORUS_MINOR_SEG = 140

# Boolean solver: 'EXACT' is recommended
BOOLEAN_SOLVER = 'EXACT'  # or 'FAST'

# Optional post-remesh to heal boolean artifacts (off by default)
POST_VOXEL_REMESH = False
VOXEL_SIZE_MM = 0.30

# Export toggles
EXPORT_SOLID = True
EXPORT_GROOVED = True


# =========================
# DERIVED GEOMETRY (mm)
# =========================
# From: R+r = OUTER_RADIUS and 2(R-r)=HOLE_DIAMETER
R_MAJOR = 0.5 * (OUTER_RADIUS_MM + 0.5 * HOLE_DIAMETER_MM)
R_TUBE  = 0.5 * (OUTER_RADIUS_MM - 0.5 * HOLE_DIAMETER_MM)

if R_TUBE <= 0 or R_MAJOR <= R_TUBE:
    raise ValueError("Invalid torus radii. Check OUTER_RADIUS_MM and HOLE_DIAMETER_MM.")

GROOVE_D = WIRE_D_MM + CLEARANCE_MM
GROOVE_R = 0.5 * GROOVE_D

if GROOVE_DEPTH_MM > GROOVE_R:
    raise ValueError("GROOVE_DEPTH_MM must be <= GROOVE_R (i.e., <= (WIRE_D+CLR)/2).")

# Sink (mm) so that resulting groove depth ~ GROOVE_DEPTH_MM
SINK = max(0.0, GROOVE_R - GROOVE_DEPTH_MM)

print(f"[v4] Torus: R_MAJOR={R_MAJOR:.3f} mm, R_TUBE={R_TUBE:.3f} mm")
print(f"[v4] Groove: WIRE_D={WIRE_D_MM:.3f} mm, CLR={CLEARANCE_MM:.3f} mm -> GROOVE_D={GROOVE_D:.3f} mm, GROOVE_R={GROOVE_R:.3f} mm, DEPTH={GROOVE_DEPTH_MM:.3f} mm => SINK={SINK:.3f} mm")

# =========================
# CONTEXT-SAFE HELPERS
# =========================
def ensure_units_mm():
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 0.001  # 1 Blender unit = 1 mm
    s.unit_settings.length_unit = 'MILLIMETERS'

def clear_scene_data_api():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    # optionally purge orphan meshes/curves
    for datablock in (bpy.data.meshes, bpy.data.curves):
        for b in list(datablock):
            if b.users == 0:
                datablock.remove(b)

def get_output_dir():
    d = bpy.path.abspath(OUTPUT_DIR) if OUTPUT_DIR else (bpy.path.abspath("//") or bpy.app.tempdir or ".")
    os.makedirs(d, exist_ok=True)
    return d

def enable_stl_addon():
    for m in ("io_mesh_stl", "io_scene_stl"):
        try:
            bpy.ops.preferences.addon_enable(module=m)
        except Exception:
            pass

def export_only_object_stl(obj, filepath):
    """Export ONLY the given object by hiding all others temporarily."""
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
    elif hasattr(bpy.ops.export_mesh, "stl"):
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True, ascii=False)
    else:
        for o in bpy.data.objects:
            o.hide_set(hide_state.get(o.name, False))
        raise RuntimeError("No STL export operator found.")

    for o in bpy.data.objects:
        o.hide_set(hide_state.get(o.name, False))

def apply_modifiers_eval(obj):
    """Apply all modifiers by replacing mesh data with evaluated mesh (context-safe)."""
    deps = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(deps)
    new_mesh = bpy.data.meshes.new_from_object(obj_eval)
    # Replace mesh data
    old_mesh = obj.data
    obj.data = new_mesh
    # Clear modifiers
    obj.modifiers.clear()
    # Cleanup old mesh if unused
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)

def add_boolean_difference(target, cutter, name="Cut"):
    mod = target.modifiers.new(name=name, type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = BOOLEAN_SOLVER
    mod.object = cutter

def add_voxel_remesh(obj, voxel_mm):
    mod = obj.modifiers.new(name="PostVoxel", type='REMESH')
    mod.mode = 'VOXEL'
    mod.voxel_size = voxel_mm / 1000.0  # 1 BU = 1mm -> 1mm = 0.001m
    mod.use_smooth_shade = False


# =========================
# GEOMETRY: TORUS + LANES
# =========================
def make_torus_bmesh(name):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_torus(
        bm,
        major_segments=TORUS_MAJOR_SEG,
        minor_segments=TORUS_MINOR_SEG,
        major_radius=R_MAJOR,
        minor_radius=R_TUBE
    )
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def torus_surface_point(theta, phi):
    c = math.cos(phi); s = math.sin(phi)
    ct = math.cos(theta); st = math.sin(theta)
    x = (R_MAJOR + R_TUBE * c) * ct
    y = (R_MAJOR + R_TUBE * c) * st
    z = (R_TUBE * s)
    return Vector((x, y, z))

def torus_normal(theta, phi):
    ct = math.cos(theta); st = math.sin(theta)
    c  = math.cos(phi);   s  = math.sin(phi)
    return Vector((c * ct, c * st, s))  # unit

def make_lane_polyline(theta0_rad, q_val):
    pts = []
    for i in range(LANE_POINTS + 1):
        t = 2.0 * math.pi * i / LANE_POINTS
        theta = P * t + theta0_rad
        phi   = q_val * t  # NOTE: major-offset phases; no minor offset
        p = torus_surface_point(theta, phi)
        n = torus_normal(theta, phi)
        p = p - SINK * n
        pts.append(p)
    return pts

def make_tube_cutter_from_polyline(name, pts):
    # Build a mesh tube by sweeping circular rings along the polyline
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    # Precompute a base circle in local XY
    ring = []
    for k in range(CUTTER_RADIAL_SEG):
        a = 2.0 * math.pi * k / CUTTER_RADIAL_SEG
        ring.append(Vector((0.0, math.cos(a) * GROOVE_R, math.sin(a) * GROOVE_R)))

    prev_verts = None
    for i in range(len(pts)):
        p = pts[i]
        # Tangent
        if i == 0:
            tvec = (pts[i+1] - pts[i]).normalized()
        elif i == len(pts) - 1:
            tvec = (pts[i] - pts[i-1]).normalized()
        else:
            tvec = (pts[i+1] - pts[i-1]).normalized()

        # Build an orthonormal frame (tvec, n1, n2)
        # Choose a stable reference not parallel to tvec
        ref = Vector((0,0,1))
        if abs(tvec.dot(ref)) > 0.9:
            ref = Vector((0,1,0))
        n1 = tvec.cross(ref).normalized()
        n2 = tvec.cross(n1).normalized()

        # Create ring verts
        this_verts = []
        for rv in ring:
            v = p + n1 * rv.y + n2 * rv.z
            this_verts.append(bm.verts.new(v))
        bm.verts.ensure_lookup_table()

        # Connect to previous ring
        if prev_verts is not None:
            for k in range(CUTTER_RADIAL_SEG):
                a = prev_verts[k]
                b = prev_verts[(k+1) % CUTTER_RADIAL_SEG]
                c = this_verts[(k+1) % CUTTER_RADIAL_SEG]
                d = this_verts[k]
                bm.faces.new((a, b, c, d))
        prev_verts = this_verts

    # Cap ends (optional)
    try:
        bm.faces.new(prev_verts)
    except Exception:
        pass

    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.hide_render = True
    return obj

def combine_meshes(objs, name):
    bm = bmesh.new()
    for o in objs:
        me = o.data
        bm.from_mesh(me)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


# =========================
# MAIN
# =========================
def main():
    ensure_units_mm()
    clear_scene_data_api()

    torus = make_torus_bmesh("GroovedTorus_full")

    solid = torus.copy()
    solid.data = torus.data.copy()
    bpy.context.collection.objects.link(solid)
    solid.name = "SolidTorus_full"

    # 6 lanes:
    #   Group A (3-phase): theta0 = 0, 120, 240 with +Q
    #   Group B (mirrored, interleaved): theta0 = 60, 180, 300 with -Q
    lane_specs = [
        ( math.radians(  0), +Q),
        ( math.radians(120), +Q),
        ( math.radians(240), +Q),
        ( math.radians( 60), -Q),
        ( math.radians(180), -Q),
        ( math.radians(300), -Q),
    ]

    cutters = []
    for i,(theta0,qv) in enumerate(lane_specs, start=1):
        pts = make_lane_polyline(theta0, qv)
        cutters.append(make_tube_cutter_from_polyline(f"LaneCutter_{i:02d}_theta{int(round(math.degrees(theta0)))}_Q{qv:+d}", pts))

    cutter_all = combine_meshes(cutters, "GrooveCutters_ALL")
    # delete individual cutters
    for o in cutters:
        bpy.data.objects.remove(o, do_unlink=True)

    # Boolean modifier once, then apply via evaluated mesh
    add_boolean_difference(torus, cutter_all, name="CutGrooves")
    apply_modifiers_eval(torus)

    # Optional post-remesh to heal small boolean cracks
    if POST_VOXEL_REMESH:
        add_voxel_remesh(torus, VOXEL_SIZE_MM)
        apply_modifiers_eval(torus)

    # Delete cutter
    bpy.data.objects.remove(cutter_all, do_unlink=True)

    # Update depsgraph
    bpy.context.view_layer.update()

    out_dir = get_output_dir()
    print("[v4] Output:", out_dir)

    if EXPORT_SOLID:
        export_only_object_stl(solid, os.path.join(out_dir, "rodin_torus_solid.stl"))
        print("[v4] Exported rodin_torus_solid.stl")

    if EXPORT_GROOVED:
        export_only_object_stl(torus, os.path.join(out_dir, "rodin_torus_grooved_6lane.stl"))
        print("[v4] Exported rodin_torus_grooved_6lane.stl")

    blend_path = os.path.join(out_dir, "rodin_torus_grooved_6lane.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("[v4] Saved", blend_path)
    print("[v4] Final objects:", [o.name for o in bpy.data.objects])

if __name__ == "__main__":
    main()