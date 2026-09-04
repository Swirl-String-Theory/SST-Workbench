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
# Slight Z elevation along path (0 = flat, 0.5 = match first image)
Z_AMP = 0.5

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
# MATERIAL (blue for Phase B, blue-ish for A to match image)
# =========================================================
mat = bpy.data.materials.new(name="PhaseB_Blue")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
# Phase B blue
bsdf.inputs["Base Color"].default_value = (0.24, 0.41, 0.98, 1.0)
bsdf.inputs["Emission Color"].default_value = (0.24, 0.41, 0.98, 1.0)
bsdf.inputs["Emission Strength"].default_value = 0.15

# =========================================================
# BUILD MESH: one poly line per start slot
# =========================================================
use_B = PHASE == "B"
phase_name = "Phase_B" if use_B else "Phase_A"

for i_start, s0 in enumerate(starts_A):
    indices = coil_path_indices(s0)
    verts = path_xyz(indices, use_phase_B=use_B, scale=SCALE, z_amp=Z_AMP)
    edges = [(j, j + 1) for j in range(len(verts) - 1)]

    mesh = bpy.data.meshes.new(name=f"{phase_name}_{i_start}")
    mesh.from_pydata(verts, edges, [])
    mesh.update()

    obj = bpy.data.objects.new(f"{phase_name}_path_{i_start}", mesh)
    obj.data.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    link(obj)

# =========================================================
# SLOT MARKERS (optional: small spheres at slot positions)
# =========================================================
R_slots = 1.0
angles_for_slots = angles_mech_B if use_B else angles_mech
for s in range(S):
    th = angles_for_slots[s]
    x = SCALE * R_slots * cos(th)
    y = SCALE * R_slots * sin(th)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04 * SCALE, location=(x, y, 0))
    slot_obj = bpy.context.object
    slot_obj.name = f"Slot_{s:02d}"
    link(slot_obj)

print(f"✅ S40 double-star coil ({phase_name}) built: step +{step_forward}, −{step_back}")
