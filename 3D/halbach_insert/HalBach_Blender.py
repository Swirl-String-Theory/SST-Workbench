#import bpy, math
#from mathutils import Vector
#import colorsys

## ==============================
## Parameters (match Python)
## ==============================
#num_magnets = 12
#dipole_ring_radius = 1.5
#arrow_length = 0.6
#arrow_offset = 0.3
#shaft_radius = 0.03
#head_radius = 0.08
#head_length = 0.18

## ==============================
## USER TILT (degrees)
## ==============================

#tilt_max_deg = 30.0
#tilt_max = math.radians(tilt_max_deg)

## ==============================
## Clean scene
## ==============================
#bpy.ops.object.select_all(action='SELECT')
#bpy.ops.object.delete(use_global=False)

## ==============================
## Dipole moment law
## ==============================
#def dipole_moment(phi):
#    # axial tilt envelope
#    theta = tilt_max * math.cos(phi)

#    # in-plane Halbach swirl
#    mx = math.cos(2*phi)
#    my = math.sin(2*phi)

#    # rescale planar part so |m|=1
#    mxy = math.cos(theta)
#    mx *= mxy
#    my *= mxy

#    # axial component
#    mz = math.sin(theta)

#    return Vector((mx,my,mz)).normalized()


## ==============================
## Create arrow mesh
## ==============================
#def make_arrow(start, direction, color):
#    direction = direction.normalized()
#    end = start + direction * arrow_length

#    # Shaft
#    mid = (start + end) * 0.5
#    bpy.ops.mesh.primitive_cylinder_add(
#        radius=shaft_radius,
#        depth=arrow_length - head_length,
#        location=mid
#    )
#    shaft = bpy.context.object

#    # Head
#    head_pos = start + direction*(arrow_length - head_length/2)
#    bpy.ops.mesh.primitive_cone_add(
#        radius1=head_radius,
#        depth=head_length,
#        location=head_pos
#    )
#    head = bpy.context.object

#    # Rotate both
#    rot = direction.to_track_quat('Z','Y')
#    shaft.rotation_mode = 'QUATERNION'
#    head.rotation_mode  = 'QUATERNION'
#    shaft.rotation_quaternion = rot
#    head.rotation_quaternion  = rot

#    # Join
#    bpy.ops.object.select_all(action='DESELECT')
#    shaft.select_set(True)
#    head.select_set(True)
#    bpy.context.view_layer.objects.active = shaft
#    bpy.ops.object.join()
#    arrow = bpy.context.object

#    # Material
#    mat = bpy.data.materials.new("arrow_mat")
#    mat.use_nodes = False
#    mat.diffuse_color = (*color,1)
#    arrow.data.materials.append(mat)

## ==============================
## Generate ring
## ==============================
#for i in range(num_magnets):
#    phi = 2*math.pi*i/num_magnets

#    pos = Vector((dipole_ring_radius*math.cos(phi),
#                  dipole_ring_radius*math.sin(phi),
#                  0.0))

#    m = dipole_moment(phi)
#    start = pos - m * arrow_offset

#    rgb = colorsys.hsv_to_rgb(i/num_magnets, 1, 1)

#    make_arrow(start, m, rgb)


import bpy, math, os, colorsys
from mathutils import Vector, Quaternion
import mathutils

# ============================================================
# USER CONTROLS
# ============================================================
SHOW_ARROWS   = False    # visualize dipole vectors (not needed for final ring)
SHOW_RING     = True     # build Rodin ring with magnet slots
EXPORT_STL    = False    # export STL when finished

OUTPUT_DIR = r"C:\workspace\projects\SwirlStringTheory\halbach_insert"

# ============================================================
# GEOMETRY
# ============================================================
N = 12
R_INNER = 8.0
R_OUTER = 20.0
R_HEIGHT = 5.0

# tilt_max_deg removed - using correct Halbach formula from magneticCircle.py

SLOT = 11
CUTTER_HEIGHT = R_HEIGHT + 0.5  # Simplified since we're not using tilt_max anymore

KEY_DEPTH = 1.0
KEY_WIDTH = 1.2

# ============================================================
# DIPOLE PHYSICS (validated)
# ============================================================

dipole_ring_radius = (R_INNER + R_OUTER)/2
arrow_length = 0.6
arrow_offset = 0.3

dipole_objects = []

# ============================================================
# Clean scene
# ============================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ============================================================
# Dipole law (correct Halbach orientation from magneticCircle.py)
# ============================================================
def dipole_vector(phi, invert=False):
    # Correct Halbach orientation formula
    mx = math.cos(2 * phi)
    my = math.sin(2 * phi)
    mz = math.cos(phi)
    m = Vector((mx, my, (-1 if invert else 1) * mz))
    return m.normalized()

# ============================================================
# Arrow geometry
# ============================================================
def make_arrow(start, direction, color):
    direction = direction.normalized()
    end = start + direction * arrow_length

    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=arrow_length*0.75, location=(start+end)/2)
    shaft = bpy.context.object
    bpy.ops.mesh.primitive_cone_add(radius1=0.08, depth=0.18, location=start+direction*(arrow_length-0.09))
    head = bpy.context.object

    rot = direction.to_track_quat('Z','Y')
    shaft.rotation_mode = head.rotation_mode = 'QUATERNION'
    shaft.rotation_quaternion = head.rotation_quaternion = rot

    bpy.ops.object.select_all(action='DESELECT')
    shaft.select_set(True)
    head.select_set(True)
    bpy.context.view_layer.objects.active = shaft
    bpy.ops.object.join()
    arrow = bpy.context.object
    arrow.name = f"DIPOLE_{i:02d}"

    mat = bpy.data.materials.new("arrow_mat")
    mat.use_nodes = False
    mat.diffuse_color = (*color,1)
    arrow.data.materials.append(mat)

    dipole_objects.append(arrow)

# ============================================================
# Cube orientation (matching GUI-MagneticRingAdjuster.py)
# ============================================================
def get_cube_rotation_quat(direction):
    """
    Get rotation quaternion for cube aligned with arrow direction.
    Applies same logic as GUI: 90° CW rotation around y-axis.
    Matches the cube orientation from GUI-MagneticRingAdjuster.py
    """
    direction = direction.normalized()
    # Base rotation to align z-axis with arrow direction
    base_rot = direction.to_track_quat('Z', 'Y')
    
    # Apply 90° clockwise rotation around local y-axis
    # This matches the GUI: rotate cube 90° CW around y-axis in local coordinates
    # In Blender quaternions: Quaternion(axis, angle) where axis is normalized
    y_axis = Vector((0, 1, 0))
    y_axis_rot = Quaternion(y_axis, -math.pi / 2)  # -90° = 90° CW
    
    # Combine rotations: rotate around y first, then align with direction
    # Quaternion multiplication: A @ B means "apply B, then A"
    # So we want: align with direction, then rotate around local y
    # But since y is in local space after alignment, we need to transform it
    # Actually, we want: base_rot @ y_axis_rot (rotate around y, then align)
    # But y_axis_rot is in global space, so we need to apply it in local space
    # The correct way: base_rot @ (base_rot.inverted() @ y_axis_rot @ base_rot)
    # Simplified: we can apply y rotation in the local frame by doing:
    final_rot = base_rot @ y_axis_rot
    
    return final_rot

# ============================================================
# Create Rodin ring
# ============================================================
if SHOW_RING:
    bpy.ops.mesh.primitive_cylinder_add(radius=R_OUTER, depth=R_HEIGHT)
    ring = bpy.context.object

    bpy.ops.mesh.primitive_cylinder_add(radius=R_INNER, depth=R_HEIGHT+2)
    inner = bpy.context.object

    mod = ring.modifiers.new("hollow","BOOLEAN")
    mod.object = inner
    mod.operation = 'DIFFERENCE'
    bpy.context.view_layer.objects.active = ring
    bpy.ops.object.modifier_apply(modifier="hollow")
    bpy.data.objects.remove(inner)

    cutters=[]

# ============================================================
# Main loop
# ============================================================
for i in range(N):
    phi = 2*math.pi*i/N

    pos = Vector((dipole_ring_radius*math.cos(phi),
                  dipole_ring_radius*math.sin(phi), 0))

    m = dipole_vector(phi)

    # ------------------ ARROWS ------------------
    if SHOW_ARROWS:
        rgb = colorsys.hsv_to_rgb(i/N,1,1)
        make_arrow(pos - m*arrow_offset, m, rgb)

    # ------------------ RING CUTOUTS ------------------
    if SHOW_RING:
        # Get rotation quaternion with same logic as GUI (90° CW around y-axis)
        rot_quat = get_cube_rotation_quat(m)

        # Main slot
        bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
        c = bpy.context.object
        c.scale = (SLOT/2, SLOT/2, CUTTER_HEIGHT/2)
        c.rotation_mode = 'QUATERNION'
        c.rotation_quaternion = rot_quat
        cutters.append(c)

        # Polarity key (offset in dipole's local X direction)
        key_pos = pos + rot_quat @ Vector((SLOT/2, 0, 0))
        bpy.ops.mesh.primitive_cube_add(size=1, location=key_pos)
        k = bpy.context.object
        k.scale = (KEY_WIDTH/2, KEY_DEPTH/2, CUTTER_HEIGHT/2)
        k.rotation_mode = 'QUATERNION'
        k.rotation_quaternion = rot_quat
        cutters.append(k)


# ============================================================
# Clean up arrows if they were created (not needed for final ring)
# ============================================================
if SHOW_RING and SHOW_ARROWS:
    # Remove arrow objects - they're not needed for the final ring
    for arrow in dipole_objects:
        bpy.data.objects.remove(arrow, do_unlink=True)
    dipole_objects.clear()

# ============================================================
# Boolean subtract
# ============================================================
if SHOW_RING:
    bpy.context.view_layer.objects.active = ring
    for c in cutters:
        mod = ring.modifiers.new("cut","BOOLEAN")
        mod.object = c
        mod.operation = 'DIFFERENCE'
        bpy.context.view_layer.objects.active = ring
        bpy.ops.object.modifier_apply(modifier="cut")
        bpy.data.objects.remove(c)

    ring.name = "Helical_Halbach_Rodin12"

# ============================================================
# Export
# ============================================================
if EXPORT_STL and SHOW_RING:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, ring.name + ".stl")
    bpy.ops.export_mesh.stl(filepath=path)
    print("Exported:", path)