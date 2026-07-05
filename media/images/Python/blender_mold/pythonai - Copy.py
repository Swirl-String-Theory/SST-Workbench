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
# Using golden ratio (phi) for proper Rodin coil proportions
OUTER_RADIUS   = 45.0  # R_OUT - outer radius of the torus
# HOLE_DIAMETER will be calculated from golden ratio

# Export toggles
EXPORT_SOLID  = False  # Export solid torus STL (also creates solid torus object)
EXPORT_GROOVED = True  # Export grooved torus STL

# Blender-only mode (skip STL exports, only save .blend file)
BLENDER_ONLY = False  # Set to True to only render in Blender without exporting STL files

# Grooved-only mode (skip solid torus creation, only export grooved STL)
# When True: faster execution, only creates and exports grooved torus
GROOVED_ONLY = True  # Set to True to skip solid torus and only export grooved STL


# Rodin groove parameterization
P = 5
Q = 12

# Groove sizing
WIRE_OD      = 1.00  # Insulated wire outer diameter (mm)
CLEARANCE    = 0.40  # Minimum radial clearance between layers (mm)
GROOVE_R     = 0.5 * (WIRE_OD + CLEARANCE)  # Cutter radius (half of wire+clearance)
GROOVE_DEPTH = 0.70  # Base groove depth (mm)

# Layer separation mode
# "deeper": Place CCW set deeper by Δh = WIRE_OD + CLEARANCE (simpler, slight impedance mismatch)
# "symmetric": Place both sets symmetrically around mid-radius (balanced impedances, if geometry permits)
LAYER_SEPARATION_MODE = "symmetric"  # Options: "deeper" or "symmetric"

# CCW groove depth factor (for outside visibility)
# Set to 0.75 to make CCW grooves visible from outside while maintaining separation
# Lower values = more visible from outside, higher values = more separation
CCW_DEPTH_FACTOR = 0.75  # Multiplier for GROOVE_DEPTH to set CCW sink depth

# Quick render mode (faster, lower quality, skips visualization objects)
QUICK_RENDER = False  # Set to True for faster rendering with reduced quality

# Visualize curve paths?
VISUALIZE_CURVES = True

# Mesh resolution (reduced in quick render mode)
if QUICK_RENDER:
    TORUS_MAJOR_SEG = 60   # Reduced from 180
    TORUS_MINOR_SEG = 40   # Reduced from 110
    LANE_POINTS     = 300  # Reduced from 900
    CURVE_RESOLUTION_U = 8  # Reduced from 16
    BEVEL_RESOLUTION   = 4  # Reduced from 8
    VISUALIZE_CURVES = False  # Disable visualization in quick render
    print("QUICK_RENDER mode: Using reduced mesh resolution and skipping visualization objects")
else:
    TORUS_MAJOR_SEG = 180
    TORUS_MINOR_SEG = 110
    LANE_POINTS     = 900
    CURVE_RESOLUTION_U = 16
    BEVEL_RESOLUTION   = 8

# Voxel remesh toggle
USE_VOXEL_REMESH = False
VOXEL_SIZE_MM    = 0.25


# 3D Printing base/platform
ADD_PRINT_BASE = False  # Add a ring-shaped base to prevent movement during printing
BASE_THICKNESS = 0.4   # Thickness of the base (mm)
BASE_MARGIN    = 0.5   # Extension around torus base (mm) - base extends this amount beyond outer radius
BASE_OFFSET    = 0.1   # Small gap between base and torus to allow easy removal (mm)

# Collection name base (will have timestamp appended for uniqueness)
COLLECTION_NAME_BASE = "Rodin_Torus"

# =========================
# ---- DERIVED QUANTITIES
# =========================

# Golden ratio
PHI = (1 + 5**0.5) / 2

# Calculate torus dimensions using golden ratio
# R_OUT = OUTER_RADIUS
# R_MAJOR = R_OUT / phi
# R_TUBE = R_OUT / (phi^2)
# HOLE_DIAMETER = 2 * (R_MAJOR - R_TUBE)
R_MAJOR = OUTER_RADIUS / PHI
R_TUBE  = OUTER_RADIUS / (PHI**2)
HOLE_DIAMETER = 2 * (R_MAJOR - R_TUBE)

print(f"Golden ratio (phi): {PHI:.6f}")
print(f"Torus geometry (golden ratio proportions):")
print(f"  OUTER_RADIUS: {OUTER_RADIUS:.3f} mm")
print(f"  R_MAJOR: {R_MAJOR:.3f} mm (OUTER_RADIUS / phi)")
print(f"  R_TUBE: {R_TUBE:.3f} mm (OUTER_RADIUS / phi^2)")
print(f"  HOLE_DIAMETER: {HOLE_DIAMETER:.3f} mm (calculated)")

if R_TUBE <= 0 or R_MAJOR <= R_TUBE:
    raise ValueError("Invalid radii: R_TUBE must be positive and R_MAJOR > R_TUBE")

if GROOVE_DEPTH > GROOVE_R:
    raise ValueError("GROOVE_DEPTH must be ≤ GROOVE_R.")

# Calculate layer separation depth
# Required center-to-center separation: Δh = d_OD + c
LAYER_SEPARATION = WIRE_OD + CLEARANCE

# Base sink for outer layer (shallower grooves)
SINK_OUTER = max(0.0, GROOVE_R - GROOVE_DEPTH)

# Sink for inner layer (deeper grooves)
# CCW_DEPTH_FACTOR is used in both modes to control CCW groove depth for outside visibility
CCW_DEPTH_OFFSET = CCW_DEPTH_FACTOR * GROOVE_DEPTH

# Intermediate CCW groove depth (half of full CCW depth for stepped profile)
SINK_INTERMEDIATE = SINK_OUTER + 0.5 * CCW_DEPTH_OFFSET

if LAYER_SEPARATION_MODE == "symmetric":
    # Symmetric placement: outer layer at r0 - Δh/2, inner at r0 + Δh/2
    # This keeps mean radius matched for balanced impedances
    # But we still use CCW_DEPTH_FACTOR for the actual CCW groove depth
    SINK_INNER = SINK_OUTER + CCW_DEPTH_OFFSET
    print(f"Using symmetric layer separation (with CCW depth factor):")
    print(f"  Outer layer (CW) sink: {SINK_OUTER:.3f} mm")
    print(f"  CCW groove depths (3-step profile):")
    print(f"    Step 1 (surface): {SINK_OUTER:.3f} mm")
    print(f"    Step 2 (intermediate): {SINK_INTERMEDIATE:.3f} mm (0.5× depth)")
    print(f"    Step 3 (deep): {SINK_INNER:.3f} mm (full depth)")
    print(f"  CCW depth offset: {CCW_DEPTH_OFFSET:.3f} mm ({CCW_DEPTH_FACTOR} × {GROOVE_DEPTH:.2f} mm groove depth)")
    print(f"  Full separation would be: {LAYER_SEPARATION:.3f} mm (WIRE_OD={WIRE_OD:.2f} + CLEARANCE={CLEARANCE:.2f})")
    print(f"  Note: Using {CCW_DEPTH_FACTOR}× groove depth for better outside visibility")
else:
    # "deeper" mode: outer layer near surface, inner layer deeper
    # Use CCW_DEPTH_FACTOR to make CCW grooves visible from outside
    SINK_INNER = SINK_OUTER + CCW_DEPTH_OFFSET
    print(f"Using deeper layer separation (with visibility factor):")
    print(f"  Outer layer (CW) sink: {SINK_OUTER:.3f} mm")
    print(f"  CCW groove depths (3-step profile):")
    print(f"    Step 1 (surface): {SINK_OUTER:.3f} mm")
    print(f"    Step 2 (intermediate): {SINK_INTERMEDIATE:.3f} mm (0.5× depth)")
    print(f"    Step 3 (deep): {SINK_INNER:.3f} mm (full depth)")
    print(f"  CCW depth offset: {CCW_DEPTH_OFFSET:.3f} mm ({CCW_DEPTH_FACTOR} × {GROOVE_DEPTH:.2f} mm groove depth)")
    print(f"  Note: Using {CCW_DEPTH_FACTOR}× groove depth for better outside visibility")
    print(f"  Full separation would be: {LAYER_SEPARATION:.3f} mm (WIRE_OD={WIRE_OD:.2f} + CLEARANCE={CLEARANCE:.2f})")

# Validate that inner layer doesn't go too deep
if SINK_INNER > R_TUBE * 0.8:  # Don't go deeper than 80% of tube radius
    print(f"WARNING: Inner layer sink ({SINK_INNER:.3f} mm) is very deep relative to tube radius ({R_TUBE:.3f} mm)")
    print(f"  Consider using symmetric mode or reducing LAYER_SEPARATION")

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
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    try:
        bpy.ops.outliner.orphans_purge(do_recursive=True)
    except:
        pass

def get_or_create_collection(name):
    """Get existing collection or create a new one with the given name"""
    # Check if collection already exists
    if name in bpy.data.collections:
        collection = bpy.data.collections[name]
    else:
        # Create new collection
        collection = bpy.data.collections.new(name)
        # Link to scene collection
        bpy.context.scene.collection.children.link(collection)
    
    # Ensure collection is visible
    collection.hide_viewport = False
    collection.hide_render = False
    
    return collection

def link_to_collection(obj, collection):
    """Link object to collection, removing from all other collections first"""
    # Remove from all collections it's currently in
    for coll in bpy.data.collections:
        if obj.name in coll.objects:
            coll.objects.unlink(obj)
    
    # Also remove from scene collection
    if obj.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(obj)
    
    # Link to target collection only
    collection.objects.link(obj)

def ensure_collection_visible():
    """Ensure the default collection and view layer are visible (Blender 5.0+ compatible)"""
    # Ensure default collection is visible
    default_collection = bpy.context.scene.collection
    default_collection.hide_viewport = False
    default_collection.hide_render = False
    
    # Ensure view layer is active and visible
    view_layer = bpy.context.view_layer
    view_layer.use = True
    
    # Make sure all collections in view layer are visible
    # Note: LayerCollection in Blender 5.0+ only has hide_viewport, not hide_render
    def set_layer_collection_visible(layer_coll):
        layer_coll.hide_viewport = False
        # hide_render doesn't exist on LayerCollection in Blender 5.0+
        # Instead, we set exclude from render on the collection itself
        if hasattr(layer_coll, 'collection'):
            layer_coll.collection.hide_render = False
        for child in layer_coll.children:
            set_layer_collection_visible(child)
    
    set_layer_collection_visible(view_layer.layer_collection)
    
    # Also ensure all collections in the scene are visible
    for collection in bpy.data.collections:
        collection.hide_viewport = False
        collection.hide_render = False

def ensure_object_visible(obj):
    """Ensure an object is fully visible in viewport and render"""
    if obj is None:
        return
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_select = False
    # Ensure it's in the active collection
    if obj.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(obj)

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
    
    # Ensure object is in object mode
    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    try:
        # Use evaluated mesh to ensure we're working with current geometry
        deps = bpy.context.evaluated_depsgraph_get()
        bpy.context.view_layer.update()
        
        bpy.ops.object.modifier_apply(modifier=name)
        
        # Update mesh after applying
        obj.data.update()
        obj.data.validate()
        bpy.context.view_layer.update()
        
        return True
    except Exception as e:
        print(f"ERROR applying modifier '{name}': {e}")
        import traceback
        traceback.print_exc()
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

def find_lowest_z(obj):
    """Find the lowest Z coordinate of an object's vertices"""
    if obj.type != 'MESH' or not obj.data or len(obj.data.vertices) == 0:
        return 0.0
    
    # Get evaluated mesh to account for modifiers
    deps = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(deps)
    mesh = eval_obj.data
    
    if len(mesh.vertices) == 0:
        return 0.0
    
    # Get world matrix to transform vertices
    world_matrix = obj.matrix_world
    min_z = float('inf')
    
    for vertex in mesh.vertices:
        world_pos = world_matrix @ vertex.co
        min_z = min(min_z, world_pos.z)
    
    return min_z if min_z != float('inf') else 0.0

def create_print_base(obj, collection):
    """
    Create a ring-shaped base/platform connected to the lowest Z point of the object.
    The base extends 0.5cm around the torus base and has a hole in the center.
    The base has a small gap to allow easy removal after printing.
    """
    if not ADD_PRINT_BASE:
        return None
    
    print(f"\nCreating print base for {obj.name}...")
    
    # Find lowest Z point
    lowest_z = find_lowest_z(obj)
    print(f"  Lowest Z point: {lowest_z:.2f} mm")
    
    # Calculate base dimensions
    # Base extends BASE_MARGIN around the torus base
    # Inner radius: hole in center (R_MAJOR - R_TUBE)
    # Outer radius: OUTER_RADIUS + BASE_MARGIN
    inner_radius = R_MAJOR - 10  # Hole matches torus center hole
    outer_radius = R_MAJOR + 10  # Extends BASE_MARGIN beyond outer edge
    
    base_z = lowest_z - BASE_THICKNESS - BASE_OFFSET  # Position base below the lowest point
    
    print(f"  Base ring: inner radius={inner_radius:.2f} mm, outer radius={outer_radius:.2f} mm")
    
    # Create base as a torus (ring) using a cylinder with a hole
    # Method: Create outer cylinder, then subtract inner cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=outer_radius,
        depth=BASE_THICKNESS,
        location=(0, 0, base_z + BASE_THICKNESS/2),
        align='WORLD'
    )
    base_outer = bpy.context.view_layer.objects.active
    set_obj_name(base_outer, f"{obj.name}_PrintBase_Outer")
    link_to_collection(base_outer, collection)
    ensure_object_visible(base_outer)
    
    # Create inner cylinder to cut the hole
    bpy.ops.mesh.primitive_cylinder_add(
        radius=inner_radius,
        depth=BASE_THICKNESS + 1.0,  # Slightly taller to ensure clean cut
        location=(0, 0, base_z + BASE_THICKNESS/2),
        align='WORLD'
    )
    base_inner = bpy.context.view_layer.objects.active
    set_obj_name(base_inner, f"{obj.name}_PrintBase_Inner")
    link_to_collection(base_inner, collection)
    ensure_object_visible(base_inner)
    
    # Cut the hole using boolean difference
    base_outer.data.update()
    base_inner.data.update()
    bpy.context.view_layer.update()
    
    try:
        boolean_diff(base_outer, base_inner, name="BaseHole")
        base = base_outer  # The outer cylinder is now the ring
        bpy.data.objects.remove(base_inner, do_unlink=True)
        
        # Verify the ring has geometry
        base.data.update()
        if len(base.data.vertices) == 0:
            print(f"  ERROR: Base ring has no geometry after cutting hole!")
            bpy.data.objects.remove(base, do_unlink=True)
            return None
        
        print(f"  Base ring created: {len(base.data.vertices)} vertices, {len(base.data.polygons)} faces")
    except Exception as e:
        print(f"  WARNING: Could not cut hole in base: {e}")
        # If cutting fails, try to use the outer cylinder as-is
        base = base_outer
        try:
            bpy.data.objects.remove(base_inner, do_unlink=True)
        except:
            pass
    
    set_obj_name(base, f"{obj.name}_PrintBase")
    
    # Union the base with the object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    base.select_set(True)
    bpy.context.view_layer.update()
    
    # Use boolean union to connect base to object
    mod = obj.modifiers.new("BaseUnion", 'BOOLEAN')
    mod.operation = 'UNION'
    mod.solver = 'EXACT'
    mod.object = base
    bpy.context.view_layer.update()
    
    try:
        if apply_modifier(obj, "BaseUnion"):
            print(f"  Base successfully connected to {obj.name}")
            # Remove the separate base object since it's now part of the main object
            bpy.data.objects.remove(base, do_unlink=True)
            return None
        else:
            print(f"  WARNING: Could not union base to {obj.name}")
            # If union fails, keep base as separate object
            base.select_set(False)
            obj.select_set(False)
            return base
    except Exception as e:
        print(f"  WARNING: Could not union base to {obj.name}: {e}")
        print(f"  Keeping base as separate object for manual connection")
        # If union fails, keep base as separate object
        base.select_set(False)
        obj.select_set(False)
        return base

# =========================
# ---- TORUS + CURVE GENERATORS
# =========================

def make_torus(collection):
    """
    Create a torus and link it to the specified collection.
    Note: bpy.ops automatically adds to active collection, so we'll move it.
    """
    # Temporarily set the target collection as active so new objects go there
    # But we'll still use link_to_collection to ensure it's only in one place
    bpy.ops.mesh.primitive_torus_add(
        major_radius=R_MAJOR,
        minor_radius=R_TUBE,
        major_segments=TORUS_MAJOR_SEG,
        minor_segments=TORUS_MINOR_SEG,
        align='WORLD')
    t = bpy.context.view_layer.objects.active
    set_obj_name(t, "Torus_base")
    # Ensure it's only in our collection (remove from any other collections)
    link_to_collection(t, collection)
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

def make_lane_curve(name, minor_offset_deg, q_val, color, sink_depth):
    """
    Generate Rodin coil lane curve matching the Python visualization approach.
    Phase shifts are applied to BOTH theta and phi (major and minor angles),
    similar to how rodin_coil.py does it.
    
    Args:
        name: Curve name
        minor_offset_deg: Phase offset in degrees
        q_val: Q value (+Q for CW, -Q for CCW)
        color: Color tuple for visualization
        sink_depth: Depth to sink into torus surface (mm) - determines groove layer depth
    """
    pts = []
    theta_shift = math.radians(minor_offset_deg)  # Phase shift in radians
    
    # Generate points for the Rodin pattern
    # For a closed Rodin coil, we need to complete P full turns (P=5)
    # We generate LANE_POINTS points for a closed curve
    # The curve will be cyclic, so the last point connects back to the first
    for i in range(LANE_POINTS):
        # Parameter t goes from 0 to 2*pi for one complete parameter loop
        # This gives us P full turns around the major axis (since theta = P*t)
        t = 2.0*math.pi * i / LANE_POINTS
        # Apply phase shift to BOTH theta and phi (matching Python script approach)
        theta = P*t + theta_shift
        phi   = q_val*t + theta_shift
        
        # Calculate point on torus surface
        x,y,z = torus_surface_point(theta, phi)
        
        # Calculate normal and sink into surface for groove depth
        # Different sink depths for CW vs CCW sets provide layer separation
        nx,ny,nz = torus_normal(theta, phi)
        x -= nx * sink_depth
        y -= ny * sink_depth
        z -= nz * sink_depth
        
        # Verify point is valid (not at origin and not NaN)
        if math.isnan(x) or math.isnan(y) or math.isnan(z):
            print(f"ERROR: {name} point {i} has NaN values!")
            return None
        
        if abs(x) < 0.001 and abs(y) < 0.001 and abs(z) < 0.001:
            print(f"WARNING: {name} point {i} is at origin (0,0,0) - theta={theta:.3f}, phi={phi:.3f}")
        
        pts.append((x,y,z))
    
    # Verify we have valid points
    if len(pts) == 0:
        print(f"ERROR: {name} has no points!")
        return None
    
    # Verify first point is not at origin
    first_pt = pts[0]
    if abs(first_pt[0]) < 0.001 and abs(first_pt[1]) < 0.001 and abs(first_pt[2]) < 0.001:
        print(f"ERROR: {name} first point is at origin (0,0,0) - curve generation failed!")
        print(f"  First point theta={P*0 + theta_shift:.3f}, phi={q_val*0 + theta_shift:.3f}")
        return None
    
    # Verify last point is not at origin
    last_pt = pts[-1]
    if abs(last_pt[0]) < 0.001 and abs(last_pt[1]) < 0.001 and abs(last_pt[2]) < 0.001:
        print(f"ERROR: {name} last point is at origin (0,0,0) - curve generation failed!")
        return None

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
    # For cyclic POLY splines, we include all points
    # Blender will automatically connect the last point back to the first
    num_points = len(pts)
    if num_points < 2:
        print(f"WARNING: {name} has insufficient points: {num_points}")
        return None
    
    # Add points (num_points - 1 because spline.points already has 1 point)
    spline.points.add(num_points - 1)
    
    # Set all points
    for i, (x,y,z) in enumerate(pts):
        spline.points[i].co = (x,y,z, 1.0)
    
    # Set spline as cyclic to close the curve
    # This will connect the last point back to the first
    spline.use_cyclic_u = True
    
    # Verify points are set correctly
    first_pt = tuple(spline.points[0].co[:3])
    last_pt = tuple(spline.points[-1].co[:3])
    
    # Debug output
    print(f"  {name}: first point = {first_pt}, last point = {last_pt}")
    
    # Check if any point is at origin
    for i, pt in enumerate(spline.points):
        pt_co = tuple(pt.co[:3])
        if abs(pt_co[0]) < 0.001 and abs(pt_co[1]) < 0.001 and abs(pt_co[2]) < 0.001:
            print(f"WARNING: {name} point {i} is at origin (0,0,0)")
    
    # Verify curve has valid geometry
    if first_pt == (0,0,0) or last_pt == (0,0,0):
        print(f"ERROR: {name} has point at origin (0,0,0) - curve may be invalid!")
        return None
    
    # Verify curve has points
    if len(spline.points) == 0:
        print(f"ERROR: {name} spline has no points after creation!")
        return None

    obj = bpy.data.objects.new(name, cd)
    # Will be linked to collection in main()
    
    # Ensure curve is at origin and visible
    obj.location = (0, 0, 0)  # Explicitly set location
    obj.hide_viewport = False
    obj.hide_render = False
    
    # Update view layer to ensure curve is evaluated
    bpy.context.view_layer.update()
    
    # Final verification - check evaluated curve points
    deps = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(deps)
    if eval_obj and eval_obj.data:
        # Check if evaluated curve has valid points
        eval_spline = eval_obj.data.splines[0] if len(eval_obj.data.splines) > 0 else None
        if eval_spline:
            eval_first = tuple(eval_spline.points[0].co[:3]) if len(eval_spline.points) > 0 else None
            if eval_first and abs(eval_first[0]) < 0.001 and abs(eval_first[1]) < 0.001 and abs(eval_first[2]) < 0.001:
                print(f"ERROR: {name} evaluated curve has first point at origin!")

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
    # Object will be linked to collection in main()
    
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
    ensure_collection_visible()
    
    # Create a unique collection name with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    collection_name = f"{COLLECTION_NAME_BASE}_{timestamp}"
    
    # Create the named collection for all objects
    collection = get_or_create_collection(collection_name)
    print(f"Using collection: {collection.name}")
    print(f"Using timestamp for files: {timestamp}")

    # Make base torus & duplicate for solid export (skip in quick render or grooved-only mode)
    if QUICK_RENDER or GROOVED_ONLY:
        # In quick render or grooved-only mode, skip base_torus and solid - create grooved directly
        if QUICK_RENDER:
            print("QUICK_RENDER: Creating grooved torus directly (skipping base and solid)")
        else:
            print("GROOVED_ONLY: Creating grooved torus directly (skipping solid torus)")
        grooved_obj = make_torus(collection)
        set_obj_name(grooved_obj, "Torus_grooved")
        ensure_object_visible(grooved_obj)
        grooved = grooved_obj
        base_torus = None
        solid = None
    else:
        base_torus = make_torus(collection)
        ensure_object_visible(base_torus)
        
        # Only create solid if we're exporting it
        if EXPORT_SOLID:
            solid = base_torus.copy()
            solid.data = base_torus.data.copy()
            # Note: .copy() automatically adds to active collection, so we need to move it
            # link_to_collection will remove it from all collections and add to our collection only
            link_to_collection(solid, collection)
            set_obj_name(solid, "Torus_solid")
            ensure_object_visible(solid)
        else:
            solid = None

        # Grooved torus copy
        grooved = base_torus.copy()
        grooved.data = base_torus.data.copy()
        # Note: .copy() automatically adds to active collection, so we need to move it
        # link_to_collection will remove it from all collections and add to our collection only
        link_to_collection(grooved, collection)
        set_obj_name(grooved, "Torus_grooved")
        ensure_object_visible(grooved)

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
    ccw_cutters = []  # Track CCW cutters for surface visibility pass
    curve_objects = []  # Keep curves for visualization
    
    for i, (q_val, deg, col) in enumerate(specs):
        name = f"lane_{i:02d}"
        # Determine sink depth based on direction (CW vs CCW)
        # +Q (positive) = clockwise = outer layer (shallower)
        # -Q (negative) = counter-clockwise = inner layer (deeper)
        if q_val > 0:
            sink_depth = SINK_OUTER
            layer_name = "CW (outer)"
            is_ccw = False
        else:
            sink_depth = SINK_INNER
            layer_name = "CCW (inner)"
            is_ccw = True
        
        print(f"Creating curve {name} with q_val={q_val}, phase={deg}°, {layer_name} layer, sink={sink_depth:.3f}mm")
        curve = make_lane_curve(name, deg, q_val, col, sink_depth)
        
        if curve is None:
            print(f"ERROR: Failed to create curve {name}, skipping...")
            continue
        
        # Link curve to collection
        link_to_collection(curve, collection)
        
        # Keep curve visible if visualization is enabled
        if VISUALIZE_CURVES:
            curve_objects.append(curve)
            curve.hide_viewport = False
            curve.hide_render = False
        
        # Convert to mesh for boolean operation
        mesh_cutter = curve_to_mesh(curve)
        
        if mesh_cutter is None:
            print(f"ERROR: Failed to convert curve {name} to mesh, skipping...")
            continue
        
        # Link cutter to collection
        link_to_collection(mesh_cutter, collection)
        
        # Ensure mesh is valid and has geometry
        if len(mesh_cutter.data.vertices) == 0:
            print(f"ERROR: Cutter {name} has no vertices after conversion!")
            continue
        
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
        
        # Track CCW cutters for surface visibility pass
        if is_ccw:
            ccw_cutters.append((i, q_val, deg, col, mesh_cutter))
        
        cutters.append(mesh_cutter)
    
    print(f"\nCreated {len(cutters)} cutters total")
    
    # Validate all cutters before proceeding
    valid_cutters = []
    for i, c in enumerate(cutters):
        if c is None:
            print(f"WARNING: Cutter {i} is None, skipping")
            continue
        c.data.update()
        if len(c.data.vertices) == 0:
            print(f"WARNING: Cutter {i} ({c.name}) has no vertices, skipping")
            continue
        if len(c.data.polygons) == 0:
            print(f"WARNING: Cutter {i} ({c.name}) has no faces, skipping")
            continue
        valid_cutters.append(c)
        print(f"  Valid cutter {i}: {c.name} - {len(c.data.vertices)} vertices, {len(c.data.polygons)} faces")
    
    if len(valid_cutters) != len(cutters):
        print(f"WARNING: Only {len(valid_cutters)}/{len(cutters)} cutters are valid!")
    
    cutters = valid_cutters
    print(f"Using {len(cutters)} valid cutters for boolean operations")

    if USE_VOXEL_REMESH:
        for c in [grooved] + cutters:
            mod = c.modifiers.new("VoxelRemesh", 'REMESH')
            mod.mode       = 'VOXEL'
            mod.voxel_size = VOXEL_SIZE_MM/1000
            mod.use_smooth_shade = False
            apply_modifier(c, "VoxelRemesh")

    # Apply boolean cuts
    print(f"\nApplying boolean cuts to grooved torus...")
    print(f"Starting with {len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces")
    
    for i, c in enumerate(cutters):
        print(f"\n  Cut {i+1}/{len(cutters)}: {c.name}")
        
        # Ensure cutter is valid
        c.data.update()
        if len(c.data.vertices) == 0:
            print(f"    ERROR: Cutter {c.name} has no vertices, skipping!")
            continue
        
        # Ensure grooved torus is valid before cut
        grooved.data.update()
        grooved.data.validate()
        bpy.context.view_layer.update()
        
        print(f"    Before cut: {len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces")
        print(f"    Cutter: {len(c.data.vertices)} vertices, {len(c.data.polygons)} faces")
        
        try:
            boolean_diff(grooved, c, name=f"Cut_{i:02d}")
            
            # Force update and validation after boolean
            grooved.data.update()
            grooved.data.validate()
            bpy.context.view_layer.update()
            
            # Verify grooved torus still has geometry
            if len(grooved.data.vertices) == 0:
                print(f"    ERROR: Grooved torus became empty after cut {i+1}!")
            else:
                print(f"    Success - after cut: {len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces")
        except Exception as e:
            print(f"    ERROR applying cut {i+1}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Only remove cutter if not visualizing
            if not VISUALIZE_CURVES:
                bpy.data.objects.remove(c, do_unlink=True)
            else:
                # Keep cutters visible for debugging, but hide them
                c.hide_viewport = True
                c.hide_render = True

    # Apply surface-level cuts for CCW lanes to make them visible from outside
    # Then deepen them with the deeper cutters
    if len(ccw_cutters) > 0:
        print(f"\nProcessing CCW lanes for outside visibility and proper depth...")
        print(f"  Step 1: Creating {len(ccw_cutters)} surface cutters at sink={SINK_OUTER:.3f}mm")
        
        ccw_surface_cutters = []
        for orig_idx, q_val, deg, col, orig_cutter in ccw_cutters:
            name = f"lane_{orig_idx:02d}_surface"
            print(f"  Creating surface cutter: {name} (CCW, phase={deg}°)")
            
            # Create surface-level curve (same path, but at surface depth)
            curve = make_lane_curve(name, deg, q_val, col, SINK_OUTER)
            
            if curve is None:
                print(f"    ERROR: Failed to create surface curve {name}, skipping...")
                continue
            
            link_to_collection(curve, collection)
            
            # Convert to mesh
            mesh_cutter = curve_to_mesh(curve)
            
            if mesh_cutter is None or len(mesh_cutter.data.vertices) == 0:
                print(f"    ERROR: Surface cutter {name} has no geometry, skipping...")
                continue
            
            # Validate cutter
            mesh_cutter.data.update()
            if len(mesh_cutter.data.polygons) == 0:
                print(f"    ERROR: Surface cutter {name} has no faces, skipping...")
                continue
            
            link_to_collection(mesh_cutter, collection)
            ccw_surface_cutters.append((orig_idx, mesh_cutter))
            print(f"    Created: {len(mesh_cutter.data.vertices)} vertices, {len(mesh_cutter.data.polygons)} faces")
        
        # Step 1: Apply surface-level boolean cuts for CCW lanes (makes them visible)
        if len(ccw_surface_cutters) > 0:
            print(f"\n  Step 1: Applying surface-level cuts for CCW visibility ({len(ccw_surface_cutters)} cutters)...")
            for i, (orig_idx, c) in enumerate(ccw_surface_cutters):
                print(f"    Surface cut {i+1}/{len(ccw_surface_cutters)}: {c.name}")
                
                c.data.update()
                grooved.data.update()
                grooved.data.validate()
                bpy.context.view_layer.update()
                
                try:
                    boolean_diff(grooved, c, name=f"CCW_SurfaceCut_{i:02d}")
                    
                    grooved.data.update()
                    grooved.data.validate()
                    bpy.context.view_layer.update()
                    
                    if len(grooved.data.vertices) == 0:
                        print(f"      ERROR: Grooved torus became empty after surface cut {i+1}!")
                    else:
                        print(f"      Success - {len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces")
                except Exception as e:
                    print(f"      ERROR: {e}")
                finally:
                    if not VISUALIZE_CURVES:
                        bpy.data.objects.remove(c, do_unlink=True)
                    else:
                        c.hide_viewport = True
                        c.hide_render = True
        
        # Step 2: Create and apply intermediate CCW cutters (half depth)
        print(f"\n  Step 2: Creating intermediate CCW grooves (sink={SINK_INTERMEDIATE:.3f}mm, 0.5× depth)...")
        ccw_intermediate_cutters = []
        
        for i, (orig_idx, q_val, deg, col, orig_cutter) in enumerate(ccw_cutters):
            name = f"lane_{orig_idx:02d}_intermediate"
            print(f"    Creating intermediate cutter: {name} (CCW, phase={deg}°, sink={SINK_INTERMEDIATE:.3f}mm)")
            
            # Create intermediate depth curve (half of full CCW depth)
            curve = make_lane_curve(name, deg, q_val, col, SINK_INTERMEDIATE)
            
            if curve is None:
                print(f"      ERROR: Failed to create intermediate curve {name}, skipping...")
                continue
            
            link_to_collection(curve, collection)
            
            # Convert to mesh
            mesh_cutter = curve_to_mesh(curve)
            
            if mesh_cutter is None or len(mesh_cutter.data.vertices) == 0:
                print(f"      ERROR: Intermediate cutter {name} has no geometry, skipping...")
                continue
            
            mesh_cutter.data.update()
            if len(mesh_cutter.data.polygons) == 0:
                print(f"      ERROR: Intermediate cutter {name} has no faces, skipping...")
                continue
            
            link_to_collection(mesh_cutter, collection)
            ccw_intermediate_cutters.append(mesh_cutter)
            print(f"      Created: {len(mesh_cutter.data.vertices)} vertices, {len(mesh_cutter.data.polygons)} faces")
        
        # Apply the intermediate cutters
        if len(ccw_intermediate_cutters) > 0:
            print(f"\n    Applying intermediate cuts ({len(ccw_intermediate_cutters)} cutters)...")
            for i, c in enumerate(ccw_intermediate_cutters):
                print(f"      Intermediate cut {i+1}/{len(ccw_intermediate_cutters)}: {c.name}")
                
                c.data.update()
                grooved.data.update()
                grooved.data.validate()
                bpy.context.view_layer.update()
                
                print(f"        Before: {len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces")
                print(f"        Cutter: {len(c.data.vertices)} vertices, {len(c.data.polygons)} faces")
                
                try:
                    boolean_diff(grooved, c, name=f"CCW_Intermediate_{i:02d}")
                    
                    grooved.data.update()
                    grooved.data.validate()
                    bpy.context.view_layer.update()
                    
                    if len(grooved.data.vertices) == 0:
                        print(f"        ERROR: Grooved torus became empty after intermediate cut {i+1}!")
                    else:
                        print(f"        Success - after: {len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces")
                except Exception as e:
                    print(f"        ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    if not VISUALIZE_CURVES:
                        bpy.data.objects.remove(c, do_unlink=True)
                    else:
                        c.hide_viewport = True
                        c.hide_render = True
        
        # Step 3: Recreate and apply deeper CCW cutters to deepen the grooves from outside
        print(f"\n  Step 3: Deepening CCW grooves with deeper cutters (sink={SINK_INNER:.3f}mm)...")
        ccw_deep_cutters = []
        
        for i, (orig_idx, q_val, deg, col, orig_cutter) in enumerate(ccw_cutters):
            name = f"lane_{orig_idx:02d}_deepen"
            print(f"    Creating deeper cutter: {name} (CCW, phase={deg}°, sink={SINK_INNER:.3f}mm)")
            
            # Recreate the deeper curve (same as original CCW cutter)
            curve = make_lane_curve(name, deg, q_val, col, SINK_INNER)
            
            if curve is None:
                print(f"      ERROR: Failed to create deeper curve {name}, skipping...")
                continue
            
            link_to_collection(curve, collection)
            
            # Convert to mesh
            mesh_cutter = curve_to_mesh(curve)
            
            if mesh_cutter is None or len(mesh_cutter.data.vertices) == 0:
                print(f"      ERROR: Deeper cutter {name} has no geometry, skipping...")
                continue
            
            mesh_cutter.data.update()
            if len(mesh_cutter.data.polygons) == 0:
                print(f"      ERROR: Deeper cutter {name} has no faces, skipping...")
                continue
            
            link_to_collection(mesh_cutter, collection)
            ccw_deep_cutters.append(mesh_cutter)
            print(f"      Created: {len(mesh_cutter.data.vertices)} vertices, {len(mesh_cutter.data.polygons)} faces")
        
        # Apply the deeper cutters to deepen the grooves
        if len(ccw_deep_cutters) > 0:
            print(f"\n    Applying deeper cuts ({len(ccw_deep_cutters)} cutters)...")
            for i, c in enumerate(ccw_deep_cutters):
                print(f"      Deepening cut {i+1}/{len(ccw_deep_cutters)}: {c.name}")
                
                c.data.update()
                grooved.data.update()
                grooved.data.validate()
                bpy.context.view_layer.update()
                
                print(f"        Before: {len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces")
                print(f"        Cutter: {len(c.data.vertices)} vertices, {len(c.data.polygons)} faces")
                
                try:
                    boolean_diff(grooved, c, name=f"CCW_Deepen_{i:02d}")
                    
                    grooved.data.update()
                    grooved.data.validate()
                    bpy.context.view_layer.update()
                    
                    if len(grooved.data.vertices) == 0:
                        print(f"        ERROR: Grooved torus became empty after deepening cut {i+1}!")
                    else:
                        print(f"        Success - after: {len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces")
                except Exception as e:
                    print(f"        ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    if not VISUALIZE_CURVES:
                        bpy.data.objects.remove(c, do_unlink=True)
                    else:
                        c.hide_viewport = True
                        c.hide_render = True

    # Ensure grooved torus is visible and valid
    ensure_object_visible(grooved)
    grooved.select_set(False)
    bpy.context.view_layer.update()
    
    # Final validation
    grooved.data.update()
    if len(grooved.data.vertices) == 0:
        print("ERROR: Grooved torus has no vertices after all cuts!")
    else:
        print(f"Grooved torus final: {len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces")

    out = get_output_dir()

    # Add print bases to exported objects (skip in quick render)
    if ADD_PRINT_BASE and not QUICK_RENDER:
        print("\nAdding print bases to exported objects...")
        if EXPORT_GROOVED:
            create_print_base(grooved, collection)
        if EXPORT_SOLID and solid:
            create_print_base(solid, collection)
    elif ADD_PRINT_BASE and QUICK_RENDER:
        print("\nQUICK_RENDER: Skipping print base creation")

    # Export STL files (skip if BLENDER_ONLY is True)
    if not BLENDER_ONLY:
        if EXPORT_SOLID and solid:
            solid_filename = f"torus_solid_{timestamp}.stl"
            export_stl(solid, os.path.join(out, solid_filename))
            print(f"Exported: {solid_filename}")
        
        if EXPORT_GROOVED:
            grooved_filename = f"torus_grooved_full_{timestamp}.stl"
            export_stl(grooved, os.path.join(out, grooved_filename))
            print(f"Exported: {grooved_filename}")
    else:
        print("\nBLENDER_ONLY mode: Skipping STL exports (only saving .blend file)")

    # Final visibility check - ensure all objects are visible
    print("\nFinal visibility check...")
    all_objects = []
    if not (QUICK_RENDER or GROOVED_ONLY) and solid:
        all_objects.append(solid)
    all_objects.append(grooved)
    
    for obj in all_objects:
        if obj and obj.name in bpy.data.objects:
            ensure_object_visible(obj)
            obj.select_set(False)
            vertex_count = len(obj.data.vertices) if obj.data and hasattr(obj.data, 'vertices') else 0
            face_count = len(obj.data.polygons) if obj.data and hasattr(obj.data, 'polygons') else 0
            print(f"  {obj.name}: visible, {vertex_count} vertices, {face_count} faces")
    
    bpy.context.view_layer.update()
    
    blend_filename = f"torus_grooved_complete_{timestamp}.blend"
    blend_filepath = os.path.join(out, blend_filename)
    bpy.ops.wm.save_as_mainfile(filepath=blend_filepath)
    print(f"\nScene saved to: {blend_filename}")
    print(f"\nAll files use timestamp: {timestamp}")

if __name__ == "__main__":
    main()