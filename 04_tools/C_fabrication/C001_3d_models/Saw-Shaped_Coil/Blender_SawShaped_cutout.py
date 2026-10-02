import bpy  # pyright: ignore[reportMissingImports]
import math
from math import cos, sin, pi

# =========================================================
# PARAMETERS (match double-starshaped_coil40.py)
# =========================================================
S = 40
step_forward = 11
step_back = 9
n_segments = 40
R_path = 0.98
delta_e_deg = 30.0
p = 4  # pole pairs for mech_shift

# Phase A start slots; Phase B uses same starts with shifted angles
starts_A = [0, 13, 27]
# Which phase to show in Blender ("A" or "B")
PHASE = "A"

# Display scale (path at R_path=0.98 -> scale to this radius in Blender)
SCALE = 100.0
# Slight Z elevation for path preview only (0 = flat)
Z_AMP = 0.0

# --- Hockey puck (cylinder) ---
PUCK_RADIUS = SCALE * 1.08   # slightly beyond slot circle
PUCK_THICKNESS = 15.0        # mm

# --- Grooves (cut from top face for wire) ---
WIRE_DIAMETER = 1.2          # mm
GROOVE_WIDTH = 1.15 * WIRE_DIAMETER
GROOVE_DEPTH = 1.5 * WIRE_DIAMETER

# --- Pins at S-points (wire winds twice around each) ---
PIN_RADIUS = 2.0             # mm
PIN_HEIGHT = 8.0             # mm above puck top
ADD_PINS = False             # True = add winding pins; False = solid puck + grooves only (like ref)

# --- Center cutout: False = solid disk (like ref), True = ring with inner hole at coil path ---
ADD_CENTER_CUTOUT = False

# --- Optional: show path lines and slot markers ---
SHOW_PATH_LINES = False
SHOW_SLOT_MARKERS = False

# =========================================================
# COIL PATH (same logic as double-starshaped_coil40.py)
# =========================================================
alpha_mech = 2 * pi / S
angles_mech = [i * alpha_mech for i in range(S)]
mech_shift = math.radians(delta_e_deg / (p / 2.0))
angles_mech_B = [(a + mech_shift) % (2 * pi) for a in angles_mech]


def coil_path_indices(start_slot, n_seg=n_segments):
    idx = start_slot
    pts = [idx]
    for k in range(n_seg):
        if k % 2 == 0:
            idx = (idx + step_forward) % S
        else:
            idx = (idx - step_back) % S
        pts.append(idx)
    return pts


def path_xyz(indices, use_phase_B, scale=1.0, z_amp=0.0):
    angles = angles_mech_B if use_phase_B else angles_mech
    verts = []
    n = len(indices)
    for i, slot_idx in enumerate(indices):
        th = angles[slot_idx]
        t = i / max(n - 1, 1)  # 0..1 along path
        z = z_amp * t if z_amp else 0.0
        x = scale * R_path * cos(th)
        y = scale * R_path * sin(th)
        verts.append((x, y, z))
    return verts


# =========================================================
# CLEAN SCENE
# =========================================================
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

col = bpy.data.collections.new("S40_DoubleStar_Coil")
bpy.context.scene.collection.children.link(col)


def link(obj):
    col.objects.link(obj)
    bpy.context.scene.collection.objects.unlink(obj)


# =========================================================
# HOCKEY PUCK (cylinder)
# =========================================================
use_B = PHASE == "B"
phase_name = "Phase_B" if use_B else "Phase_A"
angles_for_slots = angles_mech_B if use_B else angles_mech
R_slots = 1.0

# Top face of puck (grooves and pins sit on this)
z_top = PUCK_THICKNESS / 2.0

bpy.ops.mesh.primitive_cylinder_add(
    radius=PUCK_RADIUS,
    depth=PUCK_THICKNESS,
    location=(0, 0, 0),
)
puck = bpy.context.object
puck.name = "HockeyPuck"
link(puck)

# =========================================================
# CENTER CUTOUT (optional: puck → ring, inner edge at coil path)
# =========================================================
if ADD_CENTER_CUTOUT:
    INNER_RADIUS = SCALE * R_path  # edge of coil path
    bpy.ops.mesh.primitive_cylinder_add(
        radius=INNER_RADIUS,
        depth=PUCK_THICKNESS + 2.0,
        location=(0, 0, 0),
    )
    center_cut = bpy.context.object
    center_cut.name = "CenterCutout"
    link(center_cut)
    mod = puck.modifiers.new(name="CenterHole", type="BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = center_cut
    bpy.context.view_layer.objects.active = puck
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(center_cut, do_unlink=True)

# =========================================================
# GROOVE CUTTERS (one box per path segment, flat on top view)
# =========================================================
# Path vertices in XY at z=0; we cut at z_top
def groove_cutter_verts(p1, p2, z_center, groove_w, groove_d):
    """p1, p2 = (x,y). Box: length = segment length, width = groove_w, depth = groove_d."""
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    dx, dy = x2 - x1, y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    # Avoid degenerate boxes (causes boolean crash)
    length = max(length, 0.5)
    angle = math.atan2(dy, dx)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    bpy.ops.mesh.primitive_cube_add(size=1)
    cut = bpy.context.object
    cut.scale = (length, groove_w, groove_d + 0.2)
    cut.location = (cx, cy, z_center)
    cut.rotation_euler[2] = angle
    return cut

cutters = []
for i_start, s0 in enumerate(starts_A):
    indices = coil_path_indices(s0)
    verts = path_xyz(indices, use_phase_B=use_B, scale=SCALE, z_amp=0.0)
    for j in range(len(verts) - 1):
        p1, p2 = (verts[j][0], verts[j][1]), (verts[j + 1][0], verts[j + 1][1])
        z_center = z_top - GROOVE_DEPTH / 2.0
        cut = groove_cutter_verts(p1, p2, z_center, GROOVE_WIDTH, GROOVE_DEPTH)
        cut.name = f"Groove_{i_start}_{j:02d}"
        link(cut)
        cutters.append(cut)

# Apply scale on cutters so boolean gets real geometry (avoids solver bugs)
for cut in cutters:
    bpy.ops.object.select_all(action="DESELECT")
    cut.select_set(True)
    bpy.context.view_layer.objects.active = cut
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Single boolean: join all groove cutters into one, then subtract once (avoids crash from 100+ applies)
bpy.ops.object.select_all(action="DESELECT")
for cut in cutters:
    cut.select_set(True)
bpy.context.view_layer.objects.active = cutters[0]
bpy.ops.object.join()
grooves_union = bpy.context.object
grooves_union.name = "GroovesUnion"

mod = puck.modifiers.new(name="GroovesCut", type="BOOLEAN")
mod.operation = "DIFFERENCE"
mod.object = grooves_union
bpy.context.view_layer.objects.active = puck
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(grooves_union, do_unlink=True)

# =========================================================
# PINS at S-points (optional: 40 slots – wire winds twice around each)
# =========================================================
if ADD_PINS:
    pin_z_center = z_top + PIN_HEIGHT / 2.0
    for s in range(S):
        th = angles_for_slots[s]
        x = SCALE * R_slots * cos(th)
        y = SCALE * R_slots * sin(th)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=PIN_RADIUS,
            depth=PIN_HEIGHT,
            location=(x, y, pin_z_center),
        )
        pin = bpy.context.object
        pin.name = f"Pin_S{s:02d}"
        link(pin)

# =========================================================
# Solid puck: smooth shading + grey material (like reference)
# =========================================================
bpy.context.view_layer.objects.active = puck
bpy.ops.object.select_all(action="DESELECT")
puck.select_set(True)
bpy.ops.object.shade_smooth()
puck_mat = bpy.data.materials.new(name="Puck_Grey")
puck_mat.use_nodes = True
bsdf = puck_mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.78, 0.78, 0.78, 1.0)
if puck.data.materials:
    puck.data.materials[0] = puck_mat
else:
    puck.data.materials.append(puck_mat)

# =========================================================
# Optional: path lines and slot markers (for reference)
# =========================================================
if SHOW_PATH_LINES:
    mat = bpy.data.materials.new(name="PhaseB_Blue")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.24, 0.41, 0.98, 1.0)
    bsdf.inputs["Emission Color"].default_value = (0.24, 0.41, 0.98, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 0.15
    for i_start, s0 in enumerate(starts_A):
        indices = coil_path_indices(s0)
        verts = path_xyz(indices, use_phase_B=use_B, scale=SCALE, z_amp=Z_AMP)
        verts = [(v[0], v[1], v[2] + z_top) for v in verts]
        edges = [(j, j + 1) for j in range(len(verts) - 1)]
        mesh = bpy.data.meshes.new(name=f"{phase_name}_line_{i_start}")
        mesh.from_pydata(verts, edges, [])
        mesh.update()
        obj = bpy.data.objects.new(f"{phase_name}_path_{i_start}", mesh)
        obj.data.materials.append(mat)
        bpy.context.collection.objects.link(obj)
        link(obj)

if SHOW_SLOT_MARKERS:
    for s in range(S):
        th = angles_for_slots[s]
        x = SCALE * R_slots * cos(th)
        y = SCALE * R_slots * sin(th)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04 * SCALE, location=(x, y, z_top))
        slot_obj = bpy.context.object
        slot_obj.name = f"Slot_{s:02d}"
        link(slot_obj)

msg = f"✅ Hockey puck + grooves ({phase_name}, step +{step_forward}, −{step_back})"
if ADD_PINS:
    msg += "; 40 pins (wind 2× per S-point)"
if ADD_CENTER_CUTOUT:
    msg += "; center cutout (ring)"
print(msg)
