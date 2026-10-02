import bpy
import os
import math
from datetime import datetime
from mathutils import Vector

# =========================
# PARAMETERS (mm)
# =========================
OUTPUT_DIR = r"C:\workspace\projects\SwirlStringTheory\rodin_coil\starship"  # STL export folder

N_VINS = 12

BASE_RADIUS = 73.0
BASE_THICKNESS = 6.0
CENTER_HOLE_RADIUS = 50.0

# === FIXED VIN RADII ===
VIN_INNER_RADIUS = 65.0   # start vlak onder buitenrand
VIN_OUTER_RADIUS = 70.0   # net aan buitenrand

VIN_HEIGHT = 54.0         # lager is beter voor winding
VIN_WIDTH_FACTOR = 0.25   # slanker
VIN_TILT_DEG = 8          # subtiele geleiding
# === EXTRA GUSSET (inner triangle for stiffness) ===
GUSSET_INNER_RADIUS = 60.0     # hoe ver naar binnen
GUSSET_WIDTH_SCALE = 1      # 0..1 t.o.v. hoofd-driehoek
GUSSET_HEIGHT_SCALE = 1    # lager dan hoofd guide


# =========================
# CLEAN SCENE
# =========================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# =========================
# BASE PLATE
# =========================
bpy.ops.mesh.primitive_cylinder_add(
    vertices=128,
    radius=BASE_RADIUS,
    depth=BASE_THICKNESS,
    location=(0, 0, 0)
)
base = bpy.context.object
base.name = "BasePlate"

# =========================
# CENTER HOLE
# =========================
bpy.ops.mesh.primitive_cylinder_add(
    vertices=64,
    radius=CENTER_HOLE_RADIUS,
    depth=BASE_THICKNESS + 2,
    location=(0, 0, 0)
)
hole = bpy.context.object

bool_mod = base.modifiers.new(type="BOOLEAN", name="CenterHole")
bool_mod.operation = 'DIFFERENCE'
bool_mod.object = hole
bpy.context.view_layer.objects.active = base
bpy.ops.object.modifier_apply(modifier=bool_mod.name)
bpy.data.objects.remove(hole, do_unlink=True)

# =========================
# CREATE SINGLE VIN
# =========================
# =========================
# TRIANGULAR GUIDES (12x)
# =========================
GUIDE_COUNT = 36
APEX_ANGLE_DEG = 45.0

R_IN = 64.0
R_OUT = 70.0
HEIGHT = 50.0
# Phase heights (mm): 1,4,7.. / 2,5,8.. / 3,6,9.. so each phase is identifiable
HEIGHT_PHASE_0 = 50.0   # indices 0, 3, 6, ...
HEIGHT_PHASE_1 = 54.0   # indices 1, 4, 7, ...
HEIGHT_PHASE_2 = 58.0   # indices 2, 5, 8, ...
# Guide base Z: 1 mm below bottom of base plate (plate bottom = -BASE_THICKNESS/2)
GUIDE_BASE_Z = -BASE_THICKNESS/2 - 1.0


def get_output_dir():
    d = bpy.path.abspath(OUTPUT_DIR)
    os.makedirs(d, exist_ok=True)
    return d


def export_stl(obj, filepath):
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


angle_step = 2 * math.pi / GUIDE_COUNT
half_apex = math.radians(APEX_ANGLE_DEG / 2)
L = R_OUT - R_IN
base_half_width = L * math.tan(half_apex)

guides = []

for i in range(GUIDE_COUNT):
    phi = i * angle_step

    # -------------------------
    # MAIN GUIDE (outer triangle)
    # -------------------------
    apex = Vector((
        R_OUT * math.cos(phi),
        R_OUT * math.sin(phi),
        GUIDE_BASE_Z
    ))

    base_center = Vector((
        R_IN * math.cos(phi),
        R_IN * math.sin(phi),
        GUIDE_BASE_Z
    ))

    t = Vector((-math.sin(phi), math.cos(phi), 0))

    base_left  = base_center + t * base_half_width
    base_right = base_center - t * base_half_width

    verts = [apex, base_left, base_right]
    faces = [(0, 1, 2)]

    mesh = bpy.data.meshes.new(f"GuideMesh_{i}")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(f"Guide_{i}", mesh)
    bpy.context.collection.objects.link(obj)

    phase_height = [HEIGHT_PHASE_0, HEIGHT_PHASE_1, HEIGHT_PHASE_2][i % 3]

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, phase_height)}
    )
    bpy.ops.object.mode_set(mode='OBJECT')

    guides.append(obj)

    # -------------------------
    # GUSSET (inner stiffener)
    # -------------------------
    gus_apex = Vector((
        GUSSET_INNER_RADIUS * math.cos(phi),
        GUSSET_INNER_RADIUS * math.sin(phi),
        GUIDE_BASE_Z
    ))

    gus_half = base_half_width * GUSSET_WIDTH_SCALE

    gus_left  = base_center + t * gus_half
    gus_right = base_center - t * gus_half

    gus_verts = [gus_apex, gus_left, gus_right]
    gus_faces = [(0, 1, 2)]

    gus_mesh = bpy.data.meshes.new(f"GussetMesh_{i}")
    gus_mesh.from_pydata(gus_verts, [], gus_faces)
    gus_mesh.update()

    gus = bpy.data.objects.new(f"Gusset_{i}", gus_mesh)
    bpy.context.collection.objects.link(gus)

    bpy.context.view_layer.objects.active = gus
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, phase_height * GUSSET_HEIGHT_SCALE)}
    )
    bpy.ops.object.mode_set(mode='OBJECT')

    guides.append(gus)


# =========================
# JOIN ALL (base + guides)
# =========================
base.select_set(True)
for g in guides:
    g.select_set(True)
bpy.context.view_layer.objects.active = base
bpy.ops.object.join()

base.name = "36_Vin_Starship_Winding_Jig"

# =========================
# EXPORT STL to starship folder
# =========================
out_dir = get_output_dir()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"starship_winding_jig_36vin_{timestamp}.stl"
filepath = os.path.join(out_dir, filename)
try:
    export_stl(base, filepath)
    vcount = len(base.data.vertices)
    fcount = len(base.data.polygons)
    print(f"  Exported: {filename} ({vcount} vertices, {fcount} faces)")
except Exception as e:
    print(f"  ERROR exporting STL: {e}")
    import traceback
    traceback.print_exc()

print("✔ 36-vin starship winding jig generated")