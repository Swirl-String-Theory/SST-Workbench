"""
Blender script: printable 3-component Hopf-link model based on
Schleimer & Segerman, "Triple gear" (2013).

What this script builds:
- The maximally-thick 3-component Hopf-link arrangement from the paper
  (smooth tori, no exact gear teeth).
- Slightly reduced tube radius to introduce print clearance.
- One joined export-ready collection plus optional STL export.

Usage in Blender:
1. File -> New -> General
2. Scripting workspace
3. Open this file and Run Script
4. Optional: set EXPORT_STL = True and EDIT export path below.

Notes:
- The paper gives the exact linked torus geometry (r, theta, phi, thickness),
  but the gear-tooth flanks were produced ad hoc in CAD and are not fully
  specified numerically in the article. So this script reconstructs the
  printable linked base geometry, not the exact functional geared teeth.
"""

import bpy
import math
from mathutils import Vector

# -----------------------------
# Parameters from the paper
# -----------------------------
R_CORE_UNIT = 1.0          # core-circle radius in paper units
R_OFFSET_UNIT = 0.4950197  # center offset from origin
PHI = 0.0
THETA = -0.8560281
TUBE_TOUCH_UNIT = 0.3228837

# -----------------------------
# Print scaling / clearance
# -----------------------------
CORE_RADIUS_MM = 30.0      # 1 paper unit -> 30 mm
CLEARANCE_MM = 0.60        # target nearest-gap between linked parts

# Derived tube radius after adding clearance.
TUBE_RADIUS_MM = TUBE_TOUCH_UNIT * CORE_RADIUS_MM - 0.5 * CLEARANCE_MM

# Mesh quality
MAJOR_SEGMENTS = 192
MINOR_SEGMENTS = 64
SMOOTH_SHADE = True
JOIN_OBJECTS = False       # keep as 3 linked bodies
EXPORT_STL = False
EXPORT_PATH = r"/tmp/triple_gear_hopf_link_smooth.stl"


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def rot_z(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return ((c, -s, 0.0),
            (s,  c, 0.0),
            (0.0, 0.0, 1.0))


def mat_vec_mul(M, v):
    return Vector((
        M[0][0]*v.x + M[0][1]*v.y + M[0][2]*v.z,
        M[1][0]*v.x + M[1][1]*v.y + M[1][2]*v.z,
        M[2][0]*v.x + M[2][1]*v.y + M[2][2]*v.z,
    ))


def basis_vectors(angle):
    U0 = Vector((math.cos(PHI), math.sin(PHI), 0.0))
    V0 = Vector((-math.sin(PHI)*math.sin(THETA),
                 math.cos(PHI)*math.sin(THETA),
                 math.cos(THETA)))
    M = rot_z(angle)
    U = mat_vec_mul(M, U0)
    V = mat_vec_mul(M, V0)
    N = U.cross(V).normalized()
    C = mat_vec_mul(M, Vector((R_OFFSET_UNIT, 0.0, 0.0))) * CORE_RADIUS_MM
    return C, U, V, N


def create_torus(name, center, axis):
    # Blender torus is aligned to local +Z. Rotate +Z -> axis.
    z_axis = Vector((0.0, 0.0, 1.0))
    quat = z_axis.rotation_difference(axis.normalized())
    bpy.ops.mesh.primitive_torus_add(
        major_radius=R_CORE_UNIT * CORE_RADIUS_MM,
        minor_radius=TUBE_RADIUS_MM,
        major_segments=MAJOR_SEGMENTS,
        minor_segments=MINOR_SEGMENTS,
        location=center,
        rotation=quat.to_euler(),
        align='WORLD'
    )
    obj = bpy.context.active_object
    obj.name = name
    if SMOOTH_SHADE:
        bpy.ops.object.shade_smooth()
        if hasattr(obj.data, 'use_auto_smooth'):
            obj.data.use_auto_smooth = True
    return obj


def add_basic_material(obj, rgba):
    mat = bpy.data.materials.new(name=f"Mat_{obj.name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs[0].default_value = rgba
        bsdf.inputs[7].default_value = 0.35  # roughness
    obj.data.materials.append(mat)


clear_scene()

objs = []
colors = [
    (0.82, 0.25, 0.22, 1.0),
    (0.22, 0.55, 0.85, 1.0),
    (0.28, 0.72, 0.38, 1.0),
]

for k in range(3):
    ang = 2.0 * math.pi * k / 3.0
    center, U, V, axis = basis_vectors(ang)
    obj = create_torus(f"HopfTorus_{k+1}", center, axis)
    add_basic_material(obj, colors[k])
    objs.append(obj)

# Place on build plate with a tiny lift.
for obj in objs:
    obj.location.z += TUBE_RADIUS_MM + 0.2

# Optional join into one multi-body object (usually unnecessary).
if JOIN_OBJECTS:
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()

# Add a simple ground plane for viewport reference.
bpy.ops.mesh.primitive_plane_add(size=220, location=(0, 0, 0))
plane = bpy.context.active_object
plane.name = "BuildPlate"

# Export STL if desired.
if EXPORT_STL:
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs:
        obj.select_set(True)
    bpy.ops.export_mesh.stl(filepath=EXPORT_PATH, use_selection=True, ascii=False)
    print(f"Exported STL to: {EXPORT_PATH}")

print("Done: smooth printable 3-component Hopf-link model created.")
print(f"Core radius = {CORE_RADIUS_MM:.3f} mm")
print(f"Tube radius = {TUBE_RADIUS_MM:.3f} mm")
print(f"Nominal clearance = {CLEARANCE_MM:.3f} mm")
