import bpy
import os

# Adjust this path if needed
MODEL_PATH = os.path.join(os.path.dirname(bpy.data.filepath) if bpy.data.filepath else "", "triple_gear_from_uploaded_source_centered.stl")
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = "/absolute/path/to/triple_gear_from_uploaded_source_centered.stl"

# Clean default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Import STL
bpy.ops.wm.stl_import(filepath=MODEL_PATH)
obj = bpy.context.selected_objects[0]
obj.name = "TripleGearAssembly"

# Separate loose parts into 3 linked gears
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode='OBJECT')

parts = [o for o in bpy.context.selected_objects]
parts.sort(key=lambda o: o.name)

for i, part in enumerate(parts, start=1):
    part.name = f"Gear_{i}"
    bpy.context.view_layer.objects.active = part
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    part.data.use_auto_smooth = True if hasattr(part.data, "use_auto_smooth") else False

# Optional collection
coll = bpy.data.collections.new("TripleGear")
bpy.context.scene.collection.children.link(coll)
for part in parts:
    for c in part.users_collection:
        c.objects.unlink(part)
    coll.objects.link(part)

# Scene units: millimeters
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 0.001

print("Imported triple gear assembly and separated into 3 objects.")