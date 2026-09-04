import bpy
import math
from math import cos, sin, pi

# =========================================================
# USER INPUT VARIABLES
# =========================================================

# --- Topology ---
S = 40                  # number of slots
STEP = 14               # step family to cut (+11)

# --- Wire & build ---
WIRE_DIAMETER = 1.2     # mm
PUCK_THICKNESS = 15.0   # mm

# --- Groove geometry ---
GROOVE_WIDTH_FACTOR = 1.1
GROOVE_DEPTH_FACTOR = 1.5

# --- Rim fins (sharp folding edges) ---
FIN_THICKNESS = 0.7     # mm (sharp)
FIN_RADIAL_LENGTH = 6.0 # mm

# --- Overall size ---
PUCK_RADIUS = 70.0      # mm
#INNER_CLEAR_RADIUS = 0.45 * PUCK_RADIUS
#OUTER_CLEAR_RADIUS = 0.92 * PUCK_RADIUS
GROOVE_RADIUS = PUCK_RADIUS +50 + FIN_RADIAL_LENGTH + 0.3*WIRE_DIAMETER


# --- Optional rotation (for Star B later) ---
ANGULAR_OFFSET = 0.0    # radians

# =========================================================
# DERIVED
# =========================================================
GROOVE_WIDTH = GROOVE_WIDTH_FACTOR * WIRE_DIAMETER
GROOVE_DEPTH = GROOVE_DEPTH_FACTOR * WIRE_DIAMETER

# =========================================================
# CLEAN SCENE
# =========================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

col = bpy.data.collections.new("S40_HockeyPuck_Mold")
bpy.context.scene.collection.children.link(col)

def link(obj):
    col.objects.link(obj)
    bpy.context.scene.collection.objects.unlink(obj)

# =========================================================
# BASE PUCK
# =========================================================
bpy.ops.mesh.primitive_cylinder_add(
    radius=PUCK_RADIUS,
    depth=PUCK_THICKNESS,
    location=(0, 0, 0)
)
puck = bpy.context.object
puck.name = "Base_Puck"
link(puck)


# =========================================================
# GROOVE CUTTERS (negative space for wire)
# =========================================================
cutters = []

def add_groove_cutter(i_start, i_end, name):
    th1 = 2*pi*i_start/S + ANGULAR_OFFSET
    th2 = 2*pi*i_end/S + ANGULAR_OFFSET

    #    x1, y1 = INNER_CLEAR_RADIUS*cos(th1), INNER_CLEAR_RADIUS*sin(th1)
    #    x2, y2 = OUTER_CLEAR_RADIUS*cos(th2), OUTER_CLEAR_RADIUS*sin(th2)

    PIN_BASE_RADIUS = PUCK_RADIUS + 15  + FIN_RADIAL_LENGTH/2


    x1, y1 = PIN_BASE_RADIUS*cos(th1), PIN_BASE_RADIUS*sin(th1)
    x2, y2 = PIN_BASE_RADIUS*cos(th2), PIN_BASE_RADIUS*sin(th2)



    dx, dy = x2-x1, y2-y1
    length = math.sqrt(dx*dx + dy*dy)
    angle = math.atan2(dy, dx)

    bpy.ops.mesh.primitive_cube_add(size=1)
    cut = bpy.context.object
    cut.name = name

    cut.scale = (
        length/2,
        GROOVE_WIDTH/2,
        PUCK_THICKNESS
    )

    cut.location = (
        (x1+x2)/2,
        (y1+y2)/2,
        0.0
    )

    cut.rotation_euler[2] = angle

    link(cut)
    cutters.append(cut)

for i in range(S):
    add_groove_cutter(i, (i + STEP) % S, f"Groove_{i:02d}")

# =========================================================
# BOOLEAN SUBTRACTION
# =========================================================

for cut in cutters:
    mod = puck.modifiers.new(name="GrooveCut", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cut
    bpy.context.view_layer.objects.active = puck
    bpy.ops.object.modifier_apply(modifier=mod.name)

# =========================================================
# CLEANUP
# =========================================================
for obj in cutters:
    bpy.data.objects.remove(obj, do_unlink=True)

print("✅ Final S40 (+11) hockey-puck winding mold generated")