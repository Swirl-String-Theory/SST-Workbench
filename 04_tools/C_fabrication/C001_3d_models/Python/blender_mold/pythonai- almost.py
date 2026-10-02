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
OUTPUT_DIR = r"C:\workspace\projects\SwirlStringTheory\images\Python\blender_mold"  # <-- SET TO A WRITABLE FOLDER, e.g. r"C:\...\out"


# Torus geometry (mm)
OUTER_RADIUS   = 45.0
HOLE_DIAMETER  = 10.0

# Rodin groove parameterization
P = 5
Q = 12

# Groove sizing
WIRE_D       = 1.20
CLEARANCE    = 0.40
GROOVE_R     = 0.5 * (WIRE_D + CLEARANCE)  # cutter radius
GROOVE_DEPTH = 0.70

# Surface constraint: keep curves on outer surface (0.0 = allow through hole, 1.0 = outer edge only)
# Higher values keep curves further from center hole
SURFACE_CONSTRAINT = 0.4  # Keep curves at least 40% away from center hole

# Visualize curve paths?
VISUALIZE_CURVES = True

# Split for quarters?
MAKE_QUARTERS = True
SPLIT_AXIS1   = "X"  # First split plane
SPLIT_AXIS2   = "Y"  # Second split plane (perpendicular to first)

# Pegs & holes (mm) - 2 pins and 2 holes per connection to prevent rotation
PEG_R      = 2.0
PEG_LEN    = 6.0
HOLE_CLEAR = 0.25
# Position pins/holes on radial planes (offset from center)
# For quarters, place them on the split planes
PEG_OFFSET = 12.0  # Distance from center along the split plane

# Mesh resolution
TORUS_MAJOR_SEG = 180
TORUS_MINOR_SEG = 110
LANE_POINTS     = 900
CURVE_RESOLUTION_U = 16
BEVEL_RESOLUTION   = 8

# Voxel remesh toggle
USE_VOXEL_REMESH = False
VOXEL_SIZE_MM    = 0.25

# Export toggles
EXPORT_SOLID    = True
EXPORT_GROOVED  = True
EXPORT_QUARTERS = True

# =========================
# ---- DERIVED QUANTITIES
# =========================

R_MAJOR = 0.5 * (OUTER_RADIUS + 0.5 * HOLE_DIAMETER)
R_TUBE  = 0.5 * (OUTER_RADIUS - 0.5 * HOLE_DIAMETER)

if R_TUBE <= 0 or R_MAJOR <= R_TUBE:
    raise ValueError("Invalid radii: OUTER_RADIUS too small or HOLE_DIAMETER too big.")

if GROOVE_DEPTH > GROOVE_R:
    raise ValueError("GROOVE_DEPTH must be ≤ GROOVE_R.")

SINK = max(0.0, GROOVE_R - GROOVE_DEPTH)

# =========================
# ---- HELPER FUNCTIONS ----
# =========================

def ensure_units_mm():
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 0.001
    s.unit_settings.length_unit  = 'MILLIMETERS'

def get_output_dir():
    d = bpy.path.abspath(OUTPUT_DIR)
    os.makedirs(d, exist_ok=True)
    return d

def clear_scene():
    """Clear all objects from the scene, handling Blender 5.0+ context requirements"""
    # Ensure we're in object mode and have the correct context
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Select all objects using a safer method
    for obj in bpy.context.scene.objects:
        obj.select_set(True)
    
    # Delete selected objects
    if bpy.context.selected_objects:
        bpy.ops.object.delete(use_global=False, confirm=False)
    
    # Clean up orphaned data
    try:
        bpy.ops.outliner.orphans_purge(do_recursive=True)
    except:
        pass
    
    # Also clear collections (except the default scene collection)
    for collection in bpy.data.collections:
        if collection.name != "Collection":  # Keep the default collection
            try:
                bpy.data.collections.remove(collection)
            except:
                pass

def create_collections():
    """Create organized collections for the script output"""
    # Main collection for all script-generated objects
    main_collection = bpy.data.collections.new("Rodin_Torus")
    bpy.context.scene.collection.children.link(main_collection)
    
    # Sub-collections for organization
    collections = {
        'main': main_collection,
        'torus': bpy.data.collections.new("Torus"),
        'curves': bpy.data.collections.new("Curves"),
        'cutters': bpy.data.collections.new("Cutters"),
        'quarters': bpy.data.collections.new("Quarters"),
    }
    
    # Link sub-collections to main collection
    for key in ['torus', 'curves', 'cutters', 'quarters']:
        main_collection.children.link(collections[key])
    
    return collections

def link_to_collection(obj, collection, remove_from_default=True):
    """Link object to collection and optionally remove from default collection"""
    collection.objects.link(obj)
    if remove_from_default and obj.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(obj)

def enable_stl_addon():
    for m in ("io_mesh_stl", "io_scene_stl"):
        try:
            bpy.ops.preferences.addon_enable(module=m)
        except:
            pass

def export_stl(obj, filepath):
    enable_stl_addon()
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

def set_obj_name(o, name):
    o.name = name
    if o.data:
        o.data.name = name + "_data"

def apply_modifier(obj, name):
    """Apply modifier with Blender 5.0+ compatibility"""
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.context.view_layer.update()
    
    # Check if modifier exists
    if name not in obj.modifiers:
        print(f"WARNING: Modifier '{name}' not found on {obj.name}")
        return False
    
    try:
        bpy.ops.object.modifier_apply(modifier=name)
        return True
    except Exception as e:
        print(f"ERROR applying modifier '{name}': {e}")
        return False

def boolean_diff(target, cutter, name):
    # Ensure both objects are in the same collection and visible
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    
    # Ensure cutter is visible and selectable
    cutter.hide_viewport = False
    cutter.hide_render = False
    cutter.select_set(False)  # Don't select cutter, only target
    
    # Update view layer to ensure geometry is current
    bpy.context.view_layer.update()
    
    mod = target.modifiers.new(name, 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver    = 'EXACT'
    mod.object    = cutter
    
    # Update again after setting modifier
    bpy.context.view_layer.update()
    
    try:
        apply_modifier(target, mod.name)
    except Exception as e:
        print(f"WARNING: Boolean operation {name} failed with EXACT solver: {e}")
        print(f"  Trying FAST solver as fallback...")
        # Try with FAST solver as fallback
        mod.solver = 'FAST'
        bpy.context.view_layer.update()
        apply_modifier(target, mod.name)

def make_halfspace_cube(axis, positive=True, size=300):
    """Create a cube that acts as a half-space cutter for splitting"""
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0,0,0))
    c = bpy.context.view_layer.objects.active
    set_obj_name(c, "HalfSpace")
    if axis == "X":
        c.location.x = +size/2 if positive else -size/2
    elif axis == "Y":
        c.location.y = +size/2 if positive else -size/2
    elif axis == "Z":
        c.location.z = +size/2 if positive else -size/2
    return c

def make_quarterspace_intersection(axis1, positive1, axis2, positive2, size=300):
    """
    Create a quarter-space by intersecting two half-spaces.
    This represents the region we want to KEEP (not cut away).
    """
    # Create a large cube
    bpy.ops.mesh.primitive_cube_add(size=size*2, location=(0,0,0))
    quarter_space = bpy.context.view_layer.objects.active
    set_obj_name(quarter_space, "QuarterSpace")
    
    # Cut away the opposite of what we want to keep
    # We want to keep: axis1==positive1 AND axis2==positive2
    # So we cut away: axis1==not positive1 OR axis2==not positive2
    
    # Cut away first opposite half-space
    hs1 = make_halfspace_cube(axis1, not positive1, size=size*2)
    boolean_diff(quarter_space, hs1, "QuarterCut1")
    bpy.data.objects.remove(hs1, do_unlink=True)
    
    # Cut away second opposite half-space
    hs2 = make_halfspace_cube(axis2, not positive2, size=size*2)
    boolean_diff(quarter_space, hs2, "QuarterCut2")
    bpy.data.objects.remove(hs2, do_unlink=True)
    
    return quarter_space


def add_pegs_and_holes_quarters(quarter1, quarter2, connection_axis, offset1, offset2):
    """
    Add 2 pins on quarter1 and 2 holes on quarter2 to prevent rotation.
    Pins/holes are placed on the connection plane (where two quarters meet).
    
    Args:
        quarter1: Quarter that gets pins (extruded outward)
        quarter2: Quarter that gets holes (recessed inward)
        connection_axis: The axis perpendicular to the connection plane ("X", "Y", or "Z")
                       This is the axis along which the quarters are split
        offset1, offset2: Two offset positions along the connection plane for the two pins
    """
    # Determine pin orientation and positions based on connection axis
    # Pins extend from quarter1 toward the connection plane (at connection_axis = 0)
    peg_center_offset = PEG_LEN / 2
    
    # Position pins on the outer edge of the torus, not near the center
    # Use the torus outer radius to position pins away from center
    pin_radial_offset = R_MAJOR + R_TUBE * 0.7  # Position on outer edge of torus
    
    if connection_axis == "X":
        # Connection plane is Y-Z (at X=0), pins go along X axis
        pin_rot = (0, math.radians(90), 0)
        # Pin positions: pins extend from quarter toward X=0 plane
        # Position them on the outer edge of the torus
        pin_positions = [
            (peg_center_offset, pin_radial_offset + offset1, offset2),      # Pin 1
            (peg_center_offset, -pin_radial_offset - offset1, -offset2),    # Pin 2
        ]
    elif connection_axis == "Y":
        # Connection plane is X-Z (at Y=0), pins go along Y axis
        pin_rot = (math.radians(90), 0, 0)
        pin_positions = [
            (pin_radial_offset + offset1, peg_center_offset, offset2),      # Pin 1
            (-pin_radial_offset - offset1, peg_center_offset, -offset2),    # Pin 2
        ]
    else:  # Z
        # Connection plane is X-Y (at Z=0), pins go along Z axis
        pin_rot = (0, 0, 0)
        pin_positions = [
            (pin_radial_offset + offset1, offset2, peg_center_offset),      # Pin 1
            (-pin_radial_offset - offset1, -offset2, peg_center_offset),    # Pin 2
        ]
    
    for (x0, y0, z0) in pin_positions:
        # PEG ON quarter1 (extruded from quarter toward connection plane)
        peg_loc = (x0, y0, z0)
        
        bpy.ops.mesh.primitive_cylinder_add(radius=PEG_R, depth=PEG_LEN, location=peg_loc)
        peg = bpy.context.view_layer.objects.active
        peg.rotation_euler = pin_rot
        set_obj_name(peg, "Peg")
        boolean_diff(quarter1, peg, "PegUnion")
        bpy.data.objects.remove(peg, do_unlink=True)

        # HOLE ON quarter2 (recessed inward from connection plane)
        hr = PEG_R + HOLE_CLEAR
        hl = PEG_LEN + 0.8
        hole_center_offset = hl / 2
        
        # Position holes to match peg positions
        if connection_axis == "X":
            hole_loc = (hole_center_offset, y0, z0)  # Same Y, Z as peg
        elif connection_axis == "Y":
            hole_loc = (x0, hole_center_offset, z0)  # Same X, Z as peg
        else:  # Z
            hole_loc = (x0, y0, hole_center_offset)  # Same X, Y as peg
        
        bpy.ops.mesh.primitive_cylinder_add(radius=hr, depth=hl, location=hole_loc)
        hole = bpy.context.view_layer.objects.active
        hole.rotation_euler = pin_rot
        set_obj_name(hole, "PegHole")
        boolean_diff(quarter2, hole, "PegHoleDiff")
        bpy.data.objects.remove(hole, do_unlink=True)

# =========================
# ---- TORUS + CURVE GENERATORS
# =========================

def make_torus():
    bpy.ops.mesh.primitive_torus_add(
        major_radius=R_MAJOR,
        minor_radius=R_TUBE,
        major_segments=TORUS_MAJOR_SEG,
        minor_segments=TORUS_MINOR_SEG,
        align='WORLD')
    t = bpy.context.view_layer.objects.active
    set_obj_name(t, "Torus_base")
    return t

def torus_surface_point(theta, phi):
    x = (R_MAJOR + R_TUBE * math.cos(phi)) * math.cos(theta)
    y = (R_MAJOR + R_TUBE * math.cos(phi)) * math.sin(theta)
    z = (R_TUBE * math.sin(phi))
    return (x,y,z)

def torus_normal(theta, phi):
    nx = math.cos(phi)*math.cos(theta)
    ny = math.cos(phi)*math.sin(theta)
    nz = math.sin(phi)
    return (nx, ny, nz)

def make_lane_curve(name, minor_offset_deg, q_val, color):
    """
    Generate Rodin coil lane curve matching the Python visualization approach.
    Phase shifts are applied to BOTH theta and phi (major and minor angles),
    similar to how rodin_coil.py does it.
    
    Constrained to stay on the outer surface of the torus to avoid convergence
    in the center hole.
    """
    pts = []
    theta_shift = math.radians(minor_offset_deg)  # Phase shift in radians
    
    # Calculate minimum effective radius to keep curves away from center hole
    # SURFACE_CONSTRAINT: 0.0 = allow through hole, 1.0 = outer edge only
    min_radius_from_center = R_MAJOR - R_TUBE * (1.0 - SURFACE_CONSTRAINT)
    min_effective_radius = min_radius_from_center
    
    for i in range(LANE_POINTS+1):
        t = 2.0*math.pi * i / LANE_POINTS
        # Apply phase shift to BOTH theta and phi (matching Python script approach)
        theta = P*t + theta_shift
        phi = q_val*t + theta_shift
        
        # Calculate effective radius at this point
        cos_phi = math.cos(phi)
        effective_radius = R_MAJOR + R_TUBE * cos_phi
        
        # If effective radius is too small (approaching center hole), adjust phi
        # This keeps curves on the outer surface and prevents convergence in center
        if effective_radius < min_effective_radius:
            # Calculate minimum required cos(phi) to stay above minimum radius
            min_cos_phi = (min_effective_radius - R_MAJOR) / R_TUBE
            min_cos_phi = max(-1.0, min(1.0, min_cos_phi))  # Clamp to valid range
            
            # If current cos(phi) is less than minimum, clamp it
            # This keeps the curve on the outer surface
            if cos_phi < min_cos_phi:
                # Adjust phi to give us the minimum cos value
                # Preserve the sign of phi to maintain curve direction
                phi = math.acos(min_cos_phi) if math.sin(phi) >= 0 else -math.acos(min_cos_phi)
        
        x,y,z = torus_surface_point(theta, phi)
        nx,ny,nz = torus_normal(theta, phi)
        x -= nx * SINK
        y -= ny * SINK
        z -= nz * SINK
        pts.append((x,y,z))

    # Create curve
    cd = bpy.data.curves.new(name, 'CURVE')
    cd.dimensions = '3D'
    cd.resolution_u = CURVE_RESOLUTION_U
    
    # Set bevel for Blender 5.0+ compatibility
    if hasattr(cd, 'bevel_mode'):
        cd.bevel_mode = 'ROUND'  # Enable round bevel
    cd.bevel_depth = GROOVE_R
    cd.bevel_resolution = BEVEL_RESOLUTION
    cd.fill_mode = 'FULL'

    spline = cd.splines.new('POLY')
    # For POLY splines, we need one less point if cyclic
    num_points = len(pts) if len(pts) > 0 else 1
    if num_points < 2:
        print(f"WARNING: {name} has insufficient points: {num_points}")
        return None
    
    spline.points.add(num_points - 1)
    for i, (x,y,z) in enumerate(pts[:-1] if len(pts) > 1 else pts):  # Exclude last point if cyclic
        spline.points[i].co = (x,y,z, 1.0)
    
    # Set spline as cyclic to close the curve
    spline.use_cyclic_u = True
    
    # Verify curve has points
    if len(spline.points) == 0:
        print(f"ERROR: {name} spline has no points after creation!")
        return None

    obj = bpy.data.objects.new(name, cd)
    # Will be linked to appropriate collection in main()
    
    # Ensure curve is visible
    obj.hide_viewport = False
    obj.hide_render = False

    if VISUALIZE_CURVES:
        mat = bpy.data.materials.new(name + "_mat")
        mat.diffuse_color = (color[0], color[1], color[2], 1)
        obj.data.materials.append(mat)

    return obj

def curve_to_mesh(curve_obj):
    """
    Convert curve to mesh for boolean operations.
    If VISUALIZE_CURVES is True, the original curve is kept for visualization.
    """
    if curve_obj is None or curve_obj.data is None:
        print(f"ERROR: Invalid curve object")
        return None
    
    # Ensure curve is visible and evaluated
    curve_obj.hide_viewport = False
    bpy.context.view_layer.update()
    
    deps = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(deps)
    
    if eval_obj is None:
        print(f"ERROR: Could not evaluate curve {curve_obj.name}")
        return None
    
    mesh = bpy.data.meshes.new_from_object(eval_obj)
    
    # Ensure mesh is valid and has proper normals
    mesh.update()
    mesh.validate()
    
    # Check if mesh has geometry
    if len(mesh.vertices) == 0:
        print(f"WARNING: Curve {curve_obj.name} produced empty mesh!")
        print(f"  Curve type: {type(curve_obj.data)}, bevel_depth: {curve_obj.data.bevel_depth}")
        # Try to force update
        bpy.context.view_layer.update()
        eval_obj = curve_obj.evaluated_get(deps)
        mesh = bpy.data.meshes.new_from_object(eval_obj)
        mesh.update()
        
        if len(mesh.vertices) == 0:
            print(f"  Still empty after retry, returning None")
            return None
    
    if len(mesh.vertices) > 0:
        # Fix normals to ensure proper boolean operation
        bmesh_obj = bmesh.new()
        bmesh_obj.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bmesh_obj, faces=bmesh_obj.faces)
        bmesh_obj.to_mesh(mesh)
        bmesh_obj.free()
    
    mesh_obj = bpy.data.objects.new(curve_obj.name+"_mesh", mesh)
    # Will be linked to appropriate collection in main()
    
    # Only remove curve if not visualizing
    if not VISUALIZE_CURVES:
        bpy.data.objects.remove(curve_obj, do_unlink=True)
    
    return mesh_obj

# =========================
# ---- MAIN EXECUTION ----
# =========================

def main():
    ensure_units_mm()
    clear_scene()
    
    # Create organized collections
    collections = create_collections()

    # Make base torus & duplicate for solid export
    base_torus = make_torus()
    link_to_collection(base_torus, collections['torus'])
    
    solid = base_torus.copy()
    solid.data = base_torus.data.copy()
    link_to_collection(solid, collections['torus'])
    set_obj_name(solid, "Torus_solid")

    # Grooved torus copy
    grooved = base_torus.copy()
    grooved.data = base_torus.data.copy()
    link_to_collection(grooved, collections['torus'])
    set_obj_name(grooved, "Torus_grooved")

    # Groove specs: (q_val, phase_deg, color)
    # Matching rodin_coil.py: same phase offsets (0°, 120°, 240°) for both sets
    # First set: +Q (clockwise), Second set: -Q (counter-clockwise)
    specs = [
        ( +Q,   0, (1,0,0)),    # Phase 1, clockwise
        ( +Q, 120, (0,1,0)),    # Phase 2, clockwise
        ( +Q, 240, (0,0,1)),    # Phase 3, clockwise
        ( -Q,   0, (1,1,0)),    # Phase 1, counter-clockwise
        ( -Q, 120, (1,0,1)),    # Phase 2, counter-clockwise
        ( -Q, 240, (0,1,1)),    # Phase 3, counter-clockwise
    ]

    cutters = []
    curve_objects = []  # Keep curves for visualization
    
    for i, (q_val, deg, col) in enumerate(specs):
        name = f"lane_{i+1:02d}"  # Number lanes 1-6 instead of 0-5
        print(f"Creating curve {name} with q_val={q_val}, phase={deg}°")
        curve = make_lane_curve(name, deg, q_val, col)
        
        if curve is None:
            print(f"ERROR: Failed to create curve {name}, skipping...")
            continue
        
        # Link curve to curves collection
        link_to_collection(curve, collections['curves'])
        
        # Keep curve visible if visualization is enabled
        if VISUALIZE_CURVES:
            curve_objects.append(curve)
            curve.hide_viewport = False
            curve.hide_render = False
        
        # Convert to mesh for boolean operation
        mesh_cutter = curve_to_mesh(curve)
        
        if mesh_cutter is not None:
            # Link cutter to cutters collection
            link_to_collection(mesh_cutter, collections['cutters'])
        
        # Ensure mesh is valid and has geometry
        if len(mesh_cutter.data.vertices) == 0:
            print(f"ERROR: Cutter {name} has no vertices after conversion!")
            continue
        else:
            # Use polygons instead of faces for Blender 3.0+ compatibility
            num_faces = len(mesh_cutter.data.polygons)
            print(f"  Created mesh with {len(mesh_cutter.data.vertices)} vertices, {num_faces} faces")
            # Ensure mesh is manifold and properly formed
            mesh_cutter.data.update()
            bpy.context.view_layer.objects.active = mesh_cutter
            mesh_cutter.select_set(True)
            
            # For negative Q (counter-clockwise), we may need to ensure normals point outward
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            # Make normals consistent (pointing outward for boolean difference)
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Ensure the mesh is properly positioned and visible
            mesh_cutter.hide_viewport = False
            mesh_cutter.hide_render = False
        
        cutters.append(mesh_cutter)
    
    print(f"Created {len(cutters)} cutters total")

    if USE_VOXEL_REMESH:
        for c in [grooved] + cutters:
            mod = c.modifiers.new("VoxelRemesh", 'REMESH')
            mod.mode       = 'VOXEL'
            mod.voxel_size = VOXEL_SIZE_MM/1000
            mod.use_smooth_shade = False
            apply_modifier(c, "VoxelRemesh")

    # Apply boolean cuts
    print(f"Applying boolean cuts to grooved torus...")
    for i, c in enumerate(cutters):
        print(f"  Applying cut {i+1}/{len(cutters)}: {c.name}")
        try:
            boolean_diff(grooved, c, name=f"Cut_{i:02d}")
            print(f"    Success")
        except Exception as e:
            print(f"    ERROR: {e}")
        finally:
            # Only remove cutter if not visualizing
            if not VISUALIZE_CURVES:
                bpy.data.objects.remove(c, do_unlink=True)
            else:
                # Keep cutters visible for debugging, but hide them
                c.hide_viewport = True
                c.hide_render = True

    bpy.context.view_layer.update()

    out = get_output_dir()

    if EXPORT_SOLID:
        export_stl(solid, os.path.join(out, "torus_solid.stl"))
    if EXPORT_GROOVED:
        export_stl(grooved, os.path.join(out, "torus_grooved_full.stl"))

    # Make quarters
    if MAKE_QUARTERS and EXPORT_QUARTERS:
        # Create 4 quarters by splitting along two perpendicular planes
        # Quarter A: +X, +Y
        # Quarter B: -X, +Y  
        # Quarter C: -X, -Y
        # Quarter D: +X, -Y
        
        quarters = {}
        quarter_names = ['A', 'B', 'C', 'D']
        quarter_configs = [
            (True, True),   # A: +X, +Y
            (False, True),  # B: -X, +Y
            (False, False), # C: -X, -Y
            (True, False), # D: +X, -Y
        ]
        
        for name, (pos1, pos2) in zip(quarter_names, quarter_configs):
            q = grooved.copy()
            q.data = grooved.data.copy()
            link_to_collection(q, collections['quarters'])
            set_obj_name(q, f"Torus_quarter{name}")
            quarters[name] = q
            
            # Create quarter-space that represents what we want to KEEP
            # Then use INTERSECTION to keep only the part that overlaps
            quarter_space = make_quarterspace_intersection(SPLIT_AXIS1, pos1, SPLIT_AXIS2, pos2, size=OUTER_RADIUS*6)
            
            # Use INTERSECTION to keep only the part of the torus in this quarter
            mod = q.modifiers.new(f"Quarter{name}_intersect", 'BOOLEAN')
            mod.operation = 'INTERSECT'
            mod.solver = 'EXACT'
            mod.object = quarter_space
            bpy.context.view_layer.update()
            apply_modifier(q, mod.name)
            
            bpy.data.objects.remove(quarter_space, do_unlink=True)
            bpy.context.view_layer.update()
        
        # Add pins and holes to connect quarters
        # Determine connection axes based on split axes
        if SPLIT_AXIS1 == "X" and SPLIT_AXIS2 == "Y":
            # Quarters split along X and Y, connections are:
            # A-B and C-D: along X=0 plane (Y-Z plane), pins along X
            # B-C and D-A: along Y=0 plane (X-Z plane), pins along Y
            add_pegs_and_holes_quarters(quarters['A'], quarters['B'], "X", PEG_OFFSET, PEG_OFFSET*0.6)
            add_pegs_and_holes_quarters(quarters['B'], quarters['C'], "Y", PEG_OFFSET, PEG_OFFSET*0.6)
            add_pegs_and_holes_quarters(quarters['C'], quarters['D'], "X", PEG_OFFSET, PEG_OFFSET*0.6)
            add_pegs_and_holes_quarters(quarters['D'], quarters['A'], "Y", PEG_OFFSET, PEG_OFFSET*0.6)
        elif SPLIT_AXIS1 == "X" and SPLIT_AXIS2 == "Z":
            # Split along X and Z
            add_pegs_and_holes_quarters(quarters['A'], quarters['B'], "X", PEG_OFFSET, PEG_OFFSET*0.6)
            add_pegs_and_holes_quarters(quarters['B'], quarters['C'], "Z", PEG_OFFSET, PEG_OFFSET*0.6)
            add_pegs_and_holes_quarters(quarters['C'], quarters['D'], "X", PEG_OFFSET, PEG_OFFSET*0.6)
            add_pegs_and_holes_quarters(quarters['D'], quarters['A'], "Z", PEG_OFFSET, PEG_OFFSET*0.6)
        else:  # Y and Z
            # Split along Y and Z
            add_pegs_and_holes_quarters(quarters['A'], quarters['B'], "Y", PEG_OFFSET, PEG_OFFSET*0.6)
            add_pegs_and_holes_quarters(quarters['B'], quarters['C'], "Z", PEG_OFFSET, PEG_OFFSET*0.6)
            add_pegs_and_holes_quarters(quarters['C'], quarters['D'], "Y", PEG_OFFSET, PEG_OFFSET*0.6)
            add_pegs_and_holes_quarters(quarters['D'], quarters['A'], "Z", PEG_OFFSET, PEG_OFFSET*0.6)
        
        # Export all quarters
        for name in quarter_names:
            export_stl(quarters[name], os.path.join(out, f"torus_quarter{name}.stl"))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,"torus_grooved_complete.blend"))

if __name__ == "__main__":
    main()