import bpy
import bmesh
import math

# ------------------------------------------------------------
# Flat 3-lobed outline plate:
# no thick blades, no solidify, just the flat contour you indicated.
# ------------------------------------------------------------

CLEAR_SCENE = False
OBJECT_NAME = "ThreeBladeFlatOutline"
COLLECTION_NAME = "ThreeBladeFlatOutline"

# Overall size in mm
SCALE_MM = 32.0

# Outline resolution
OUTLINE_STEPS = 480

# Polar contour coefficients
# r(t) = SCALE_MM * (BASE + A3*cos(3t) + A6*cos(6t) + A9*cos(9t))
BASE = 1.00
A3 = 0.34
A6 = -0.11
A9 = 0.05

# Optional tiny thickness only if you need visibility in viewport/render.
# Set to 0.0 for mathematically flat face only.
TINY_THICKNESS = 0.0

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def ensure_collection(name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll

def radial_profile(t):
    return SCALE_MM * (
        BASE
        + A3 * math.cos(3.0 * t)
        + A6 * math.cos(6.0 * t)
        + A9 * math.cos(9.0 * t)
    )

def build_outline_points(n=240):
    pts = []
    for i in range(n):
        t = 2.0 * math.pi * i / n
        r = radial_profile(t)
        pts.append((r * math.cos(t), r * math.sin(t), 0.0))
    return pts

def build_mesh_object(name, points):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()
    verts = [bm.verts.new(p) for p in points]
    bm.faces.new(verts)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    return obj

def add_material(obj):
    mat = bpy.data.materials.new(name=f"{obj.name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.72, 0.72, 0.72, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.45
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def main():
    if CLEAR_SCENE:
        clear_scene()

    coll = ensure_collection(COLLECTION_NAME)
    points = build_outline_points(OUTLINE_STEPS)
    obj = build_mesh_object(OBJECT_NAME, points)
    coll.objects.link(obj)

    # unlink from scene master collection if needed
    for c in list(obj.users_collection):
        if c != coll:
            c.objects.unlink(obj)

    if TINY_THICKNESS > 0.0:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        solid = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
        solid.thickness = TINY_THICKNESS
        solid.offset = 0.0
        bpy.ops.object.modifier_apply(modifier=solid.name)
        obj.select_set(False)

    add_material(obj)

    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 0.001

    print("Created flat outline object:", OBJECT_NAME)

if __name__ == "__main__":
    main()
