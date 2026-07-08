import bpy, math, os, colorsys
from mathutils import Vector, Quaternion, Matrix

# ============================================================
# USER CONTROLS (matching GUI-MagneticRingAdjuster.py)
# Note: Values are in cm (matching HalBach_Blender.py scale)
# ============================================================
NUM_MAGNETS = 12      # Number of magnets/cubes (default: 16, range: 2-64)
CUBE_SIZE_CM = 5    # Size of each cube in cm (5mm = 0.5cm)
TOROID_DEG = 0        # Additional toroidal rotation (default: 720, range: 0-1440)
POLOID_DEG = 30       # Additional poloidal rotation (default: 0, range: 0-720)
SHOW_CUBES = True     # Show cubes
SHOW_ARROWS = False   # Show arrows (optional visualization)

# ============================================================
# RING GEOMETRY (matching HalBach_Blender.py - values in cm)
# ============================================================
R_INNER = 9.0         # Inner radius of ring in cm (matching HalBach_Blender.py)
R_OUTER = 18.0        # Outer radius of ring in cm (matching HalBach_Blender.py)
R_HEIGHT = 3.0        # Ring height in cm (matching HalBach_Blender.py)
DIPOLE_RING_RADIUS = (R_INNER + R_OUTER) / 2  # 14.0 cm - where cubes are positioned
RADIUS = DIPOLE_RING_RADIUS  # Use ring radius for cube positioning
CREATE_RING = True        # Create ring with cube cutouts
EXPORT_STL = True        # Export STL when finished
OUTPUT_DIR = r"C:\workspace\projects\SwirlStringTheory\halbach_insert"

# ============================================================
# Clean scene
# ============================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ============================================================
# Dipole law (correct Halbach orientation from magneticCircle.py)
# Includes toroid/poloid rotations matching GUI-MagneticRingAdjuster.py
# ============================================================
def dipole_vector(phi, i, num_magnets, toroidal_degrees, poloidal_degrees, invert=False):
    """
    Calculate dipole orientation with optional toroid/poloid rotations.
    Matches the logic from GUI-MagneticRingAdjuster.py generate_ring function.
    """
    # Correct Halbach orientation formula (from magneticCircle.py)
    mx_base = math.cos(2 * phi)
    my_base = math.sin(2 * phi)
    
    # Poloidal tilt: varies linearly from arrow 0 to arrow N/2
    # When poloid=0: flat in xy plane (angle = 0°)
    # When poloid=90: arrow 0 points parallel to +z (90°), arrow N/2 points parallel to -z (-90°)
    if poloidal_degrees == 0:
        # Flat in xy plane
        mx = mx_base
        my = my_base
        mz = 0.0
    else:
        # Linear factor: +1 at i=0, -1 at i=N/2, +1 at i=N
        if i <= num_magnets / 2:
            # Linear from +1 to -1
            poloidal_factor = 1.0 - 2.0 * i / (num_magnets / 2)  # +1 to -1
        else:
            # Linear from -1 back to +1
            poloidal_factor = -1.0 + 2.0 * (i - num_magnets / 2) / (num_magnets / 2)  # -1 to +1
        
        # Convert poloid degrees to tilt angle
        tilt_angle_deg = poloidal_factor * poloidal_degrees
        tilt_angle_rad = math.radians(tilt_angle_deg)
        
        # Construct vector with correct tilt angle from xy plane
        xy_magnitude = math.sqrt(mx_base**2 + my_base**2)
        if xy_magnitude > 1e-10:
            # Scale xy components by cos(θ) and set z = sin(θ)
            scale_xy = math.cos(tilt_angle_rad)
            mx = mx_base * scale_xy
            my = my_base * scale_xy
            mz = math.sin(tilt_angle_rad)
        else:
            # Edge case: if xy components are zero, just set z
            mx = 0.0
            my = 0.0
            mz = math.sin(tilt_angle_rad)
    
    m = Vector((mx, my, (-1 if invert else 1) * mz))
    m = m.normalized() if m.length > 1e-10 else Vector((0, 0, 1 if mz > 0 else -1))
    
    # Apply optional toroidal rotation for visualization
    if toroidal_degrees != 0:
        toroidal_angle = math.radians(toroidal_degrees) * i / num_magnets
        # Rotate around z-axis (toroidal) - rotates in xy plane
        cos_t = math.cos(toroidal_angle)
        sin_t = math.sin(toroidal_angle)
        # Rotation matrix around z-axis
        rot_z = Matrix([
            [cos_t, -sin_t, 0],
            [sin_t,  cos_t, 0],
            [0,      0,     1]
        ])
        m = rot_z @ m
    
    m = m.normalized()  # Renormalize after rotations
    return m

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
    y_axis = Vector((0, 1, 0))
    y_axis_rot = Quaternion(y_axis, -math.pi / 2)  # -90° = 90° CW
    
    # Combine rotations: rotate around y first, then align with direction
    final_rot = base_rot @ y_axis_rot
    
    return final_rot

# ============================================================
# Create cube with colored faces
# ============================================================
def create_colored_cube(location, direction, size, color_hue, as_cutter=False):
    """
    Create a cube with colored material.
    Matches the visualization from GUI-MagneticRingAdjuster.py
    If as_cutter=True, creates a larger cube for boolean cutting (extends through ring)
    """
    # Create cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cube = bpy.context.object
    
    # Apply rotation with 90° CW around y-axis first
    rot_quat = get_cube_rotation_quat(direction)
    cube.rotation_mode = 'QUATERNION'
    cube.rotation_quaternion = rot_quat
    
    if as_cutter:
        # For cutters, we need to ensure the cube extends through the ring
        # The ring is centered at z=0 with height R_HEIGHT, so it spans -R_HEIGHT/2 to +R_HEIGHT/2
        # When a cube is rotated, its diagonal (space diagonal = side * sqrt(3)) determines max extent
        # To ensure the rotated cube extends through the ring height plus margin:
        # diagonal = cutter_size * sqrt(3) >= R_HEIGHT + margin
        # cutter_size >= (R_HEIGHT + margin) / sqrt(3)
        cutter_margin = 0.0  # Extra margin in cm to ensure clean cuts (increased from 1.0)
        min_cutter_size = (R_HEIGHT + cutter_margin) / math.sqrt(3)
        # Use the larger of the cube size or the minimum required size, with additional safety factor
        cutter_size = max(size * 1.0, min_cutter_size)  # 20% larger than cube size for safety
        # Scale all dimensions equally - the rotation will ensure it cuts through
        cube.scale = (cutter_size, cutter_size*2, cutter_size )
    else:
        cube.scale = (size, size*1.2, size)
    
    if not as_cutter:
        # Colored material for sides (based on position in ring)
        mat_color = bpy.data.materials.new(name=f"Cube_Color_{color_hue:.2f}")
        mat_color.use_nodes = False
        rgb = colorsys.hsv_to_rgb(color_hue, 1, 1)
        mat_color.diffuse_color = (*rgb, 1)
        cube.data.materials.append(mat_color)
        cube.name = f"CUBE_{int(color_hue * NUM_MAGNETS):02d}"
    else:
        cube.name = f"CUTTER_{int(color_hue * NUM_MAGNETS):02d}"
    
    return cube

# ============================================================
# Create arrow (optional visualization)
# ============================================================
def create_arrow(location, direction, color_hue, arrow_length=0.6):
    """
    Create an arrow pointing in the dipole direction.
    """
    direction = direction.normalized()
    start = location - direction * 0.3  # Offset like in GUI
    end = start + direction * arrow_length
    
    # Create shaft
    mid = (start + end) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=arrow_length*0.75, location=mid)
    shaft = bpy.context.object
    
    # Create head
    head_pos = start + direction * (arrow_length - 0.09)
    bpy.ops.mesh.primitive_cone_add(radius1=0.08, depth=0.18, location=head_pos)
    head = bpy.context.object
    
    # Rotate both
    rot = direction.to_track_quat('Z', 'Y')
    shaft.rotation_mode = head.rotation_mode = 'QUATERNION'
    shaft.rotation_quaternion = head.rotation_quaternion = rot
    
    # Join
    bpy.ops.object.select_all(action='DESELECT')
    shaft.select_set(True)
    head.select_set(True)
    bpy.context.view_layer.objects.active = shaft
    bpy.ops.object.join()
    arrow = bpy.context.object
    
    # Material
    mat = bpy.data.materials.new(f"Arrow_{color_hue:.2f}")
    mat.use_nodes = False
    rgb = colorsys.hsv_to_rgb(color_hue, 1, 1)
    mat.diffuse_color = (*rgb, 1)
    arrow.data.materials.append(mat)
    
    arrow.name = f"ARROW_{int(color_hue * NUM_MAGNETS):02d}"
    return arrow

# ============================================================
# Create ring (if enabled)
# ============================================================
ring = None
cutters = []

if CREATE_RING:
    # Create outer cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius=R_OUTER, depth=R_HEIGHT)
    ring = bpy.context.object
    
    # Create inner cylinder for hollowing
    bpy.ops.mesh.primitive_cylinder_add(radius=R_INNER, depth=R_HEIGHT + 2)
    inner = bpy.context.object
    
    # Boolean difference to make ring hollow
    mod = ring.modifiers.new("hollow", "BOOLEAN")
    mod.object = inner
    mod.operation = 'DIFFERENCE'
    bpy.context.view_layer.objects.active = ring
    bpy.ops.object.modifier_apply(modifier="hollow")
    bpy.data.objects.remove(inner)

# ============================================================
# Main loop - create cubes in circle
# ============================================================
visualization_objects = []  # Store cubes and arrows for cleanup before export

for i in range(NUM_MAGNETS):
    phi = 2 * math.pi * i / NUM_MAGNETS
    
    # Position on circle
    pos = Vector((
        RADIUS * math.cos(phi),
        RADIUS * math.sin(phi),
        0.0
    ))
    
    # Get dipole orientation with toroid/poloid rotations
    m = dipole_vector(phi, i, NUM_MAGNETS, TOROID_DEG, POLOID_DEG)
    
    # Color based on position in ring (matching GUI)
    color_hue = i / NUM_MAGNETS
    
    # Create visualization cube
    if SHOW_CUBES:
        cube = create_colored_cube(pos, m, CUBE_SIZE_CM, color_hue, as_cutter=False)
        visualization_objects.append(cube)
    
    # Create arrow (optional)
    if SHOW_ARROWS:
        arrow_length = CUBE_SIZE_CM * 2.0  # Match GUI proportions
        arrow = create_arrow(pos, m, color_hue, arrow_length)
        visualization_objects.append(arrow)
    
    # Create cutter cube for ring (if ring is enabled)
    if CREATE_RING:
        cutter = create_colored_cube(pos, m, CUBE_SIZE_CM, color_hue, as_cutter=True)
        cutters.append(cutter)

# ============================================================
# Boolean subtract cubes from ring
# ============================================================
if CREATE_RING and ring and cutters:
    print(f"Starting boolean operations: {len(cutters)} cutters to apply")
    
    # Ensure ring is active and convert to mesh
    bpy.ops.object.select_all(action='DESELECT')
    ring.select_set(True)
    bpy.context.view_layer.objects.active = ring
    # Convert to mesh and apply all transforms
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print(f"Ring converted to mesh, transforms applied")
    
    # Apply transforms to each cutter and perform boolean operation
    for i, cutter in enumerate(cutters):
        print(f"Processing cutter {i+1}/{len(cutters)}: {cutter.name}")
        
        # Select and make cutter active
        bpy.ops.object.select_all(action='DESELECT')
        cutter.select_set(True)
        bpy.context.view_layer.objects.active = cutter
        # Convert to mesh and apply all transforms
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        # Now do the boolean operation on the ring
        bpy.ops.object.select_all(action='DESELECT')
        ring.select_set(True)
        bpy.context.view_layer.objects.active = ring
        
        # Add boolean modifier
        mod = ring.modifiers.new(name=f"cut_{i}", type="BOOLEAN")
        mod.object = cutter
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'  # Use EXACT solver for better reliability with complex geometry
        
        # Apply the modifier
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
            print(f"  Boolean operation {i+1} applied successfully")
        except Exception as e:
            print(f"  WARNING: Boolean operation {i+1} failed: {e}")
            # Try with FAST solver as fallback
            mod.solver = 'FAST'
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                print(f"  Boolean operation {i+1} applied with FAST solver")
            except Exception as e2:
                print(f"  ERROR: Boolean operation {i+1} failed with both solvers: {e2}")
        
        # Remove the cutter object
        bpy.data.objects.remove(cutter)
    
    ring.name = f"Halbach_Ring_{NUM_MAGNETS}"
    print(f"Boolean operations complete. Ring name: {ring.name}")

# ============================================================
# Export STL (if enabled)
# ============================================================
if EXPORT_STL and CREATE_RING and ring:
    # Hide or remove visualization objects before export
    for obj in visualization_objects:
        obj.hide_set(True)  # Hide from viewport
        obj.hide_render = True  # Hide from render
    
    # Select only the ring for export
    bpy.ops.object.select_all(action='DESELECT')
    ring.select_set(True)
    bpy.context.view_layer.objects.active = ring
    
    # Generate unique filename with key parameters
    # Format: HalbachRing_N{num}_Ri{inner}_Ro{outer}_H{height}_Cube{cube}_T{toroid}_P{poloid}.stl
    filename = (f"HalbachRing_N{NUM_MAGNETS}_Ri{R_INNER:.1f}_Ro{R_OUTER:.1f}_"
                f"H{R_HEIGHT:.1f}_Cube{CUBE_SIZE_CM:.1f}_T{TOROID_DEG}_P{POLOID_DEG}.stl")
    # Replace dots in numbers with 'p' to avoid filesystem issues
    filename = filename.replace('.', 'p')
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    bpy.ops.export_mesh.stl(filepath=path, use_selection=True)  # Only export selected (ring)
    print(f"Exported: {path}")
    
    # Restore visualization objects visibility
    for obj in visualization_objects:
        obj.hide_set(False)
        obj.hide_render = False

print(f"Created {NUM_MAGNETS} items in a circle")
print(f"  Cube Circle Radius: {RADIUS} cm")
print(f"  Cube Size: {CUBE_SIZE_CM} cm ({CUBE_SIZE_CM * 10}mm)")
print(f"  Ring Inner Radius: {R_INNER} cm")
print(f"  Ring Outer Radius: {R_OUTER} cm")
print(f"  Ring Height: {R_HEIGHT} cm")
print(f"  Toroid: {TOROID_DEG}°")
print(f"  Poloid: {POLOID_DEG}°")
print(f"  Show Cubes: {SHOW_CUBES}")
print(f"  Show Arrows: {SHOW_ARROWS}")
print(f"  Create Ring: {CREATE_RING}")
