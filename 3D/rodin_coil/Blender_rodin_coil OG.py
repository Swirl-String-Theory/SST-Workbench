import bpy, os, math
import bmesh
from mathutils import Vector

# =========================
# USER PARAMETERS
# =========================
OUTPUT_DIR = r"C:\workspace\projects\SwirlStringTheory\rodin_coil"  # <-- SET TO A WRITABLE FOLDER, e.g. r"C:\...\out"


# Torus geometry (mm)
# Using golden ratio (phi) for proper Rodin coil proportions
OUTER_RADIUS   = 49.0  # R_OUT - outer radius of the torus
# HOLE_DIAMETER will be calculated from golden ratio

# Rodin groove parameterization
P = 5
Q = 12

# Groove sizing
WIRE_OD      = 1.10  # Insulated wire outer diameter (mm)
CLEARANCE    = 0.50  # Minimum radial clearance between layers (mm)
GROOVE_R     = 0.5 * (WIRE_OD + CLEARANCE)  # Cutter radius (half of wire+clearance)
GROOVE_DEPTH = 0.75  # Base groove depth (mm) — must be ≤ GROOVE_R

# How many depth passes to use for each set
# Note: In quick render mode, these are automatically reduced for speed
CW_PASSES_BASE  = 2          # Base value - usually 1 is fine
CCW_PASSES_BASE = 5         # Base value - set this to 1,2,3,4,... to control deepening

# Depth schedule mode:
# "linear" = evenly spaced depths from surface->deep
# "three_step" = matches your old (surface, half, full) behavior when CCW_PASSES_BASE=3
DEPTH_SCHEDULE_MODE = "linear"   # or "three_step"

# Layer separation mode
# "deeper": Place CCW set deeper by Δh = WIRE_OD + CLEARANCE (simpler, slight impedance mismatch)
# "symmetric": Place both sets symmetrically around mid-radius (balanced impedances, if geometry permits)
LAYER_SEPARATION_MODE = "symmetric"  # Options: "deeper" or "symmetric"

# CCW groove depth factor (for outside visibility)
# Set to 0.75 to make CCW grooves visible from outside while maintaining separation
# Lower values = more visible from outside, higher values = more separation
CCW_DEPTH_FACTOR = 2.40  # Multiplier for GROOVE_DEPTH to set CCW sink depth (higher = deeper)

# CW groove depth factor (for CW deepening passes)
# Controls how deep CW grooves go across multiple passes
CW_DEPTH_FACTOR = 1.20  # Multiplier for GROOVE_DEPTH to set CW deep sink (higher = deeper)

# Maximum groove sink as fraction of tube radius (0..1). Grooves are clamped so they never
# cut through the torus wall. Increase for deeper grooves (e.g. 0.85–0.9); leave margin
# so sink + GROOVE_R stays below R_TUBE.
MAX_GROOVE_SINK_FRACTION = 0.80  # 0.80 = safe; up to ~0.95 if tube is thick

# Swap CW and CCW: if True, passes and depth factors are swapped (only this switch to change)
SWAP_CW_CCW = False  # Set True to use CCW as primary (swap passes and depth factors)
if SWAP_CW_CCW:
    CW_PASSES_BASE, CCW_PASSES_BASE = CCW_PASSES_BASE, CW_PASSES_BASE
    CW_DEPTH_FACTOR, CCW_DEPTH_FACTOR = CCW_DEPTH_FACTOR, CW_DEPTH_FACTOR
WIND_LABEL = "ccw" if SWAP_CW_CCW else "cw"  # Used in export filenames

# Quick render mode (faster, lower quality, skips visualization objects)
QUICK_RENDER = False  # Set to True for faster rendering with reduced quality
ULTRA_QUICK_RENDER = False  # Set to True for even more aggressive reduction (minimal quality, maximum speed)

# Visualize curve paths?
VISUALIZE_CURVES = False
ADD_BREAKOFF_LEGS = False


# Mesh resolution (reduced in quick render mode)
if ULTRA_QUICK_RENDER:
    # Ultra quick render settings - reduced but reasonable quality
    TORUS_MAJOR_SEG = 60   # Reduced from 180 (increased from 20)
    TORUS_MINOR_SEG = 40   # Reduced from 110 (increased from 12)
    LANE_POINTS     = 300  # Reduced from 900 (increased from 100)
    CURVE_RESOLUTION_U = 6  # Reduced from 16 (increased from 2)
    BEVEL_RESOLUTION   = 3  # Reduced from 8 (increased from 1)
    VISUALIZE_CURVES = False  # Disable visualization in quick render
    print("ULTRA_QUICK_RENDER mode: Using reduced mesh resolution (increased for better quality)")
    print(f"  TORUS_MAJOR_SEG: {TORUS_MAJOR_SEG} (normal: 180)")
    print(f"  TORUS_MINOR_SEG: {TORUS_MINOR_SEG} (normal: 110)")
    print(f"  LANE_POINTS: {LANE_POINTS} (normal: 900)")
    print(f"  CURVE_RESOLUTION_U: {CURVE_RESOLUTION_U} (normal: 16)")
    print(f"  BEVEL_RESOLUTION: {BEVEL_RESOLUTION} (normal: 8)")
elif QUICK_RENDER:
    # Quick render settings - balanced quality and speed
    TORUS_MAJOR_SEG = 90   # Reduced from 180 (increased from 30 for better quality)
    TORUS_MINOR_SEG = 60   # Reduced from 110 (increased from 20 for better quality)
    LANE_POINTS     = 450  # Reduced from 900 (increased from 150 for better quality)
    CURVE_RESOLUTION_U = 8  # Reduced from 16 (increased from 4 for better quality)
    BEVEL_RESOLUTION   = 4  # Reduced from 8 (increased from 2 for better quality)
    VISUALIZE_CURVES = False  # Disable visualization in quick render
    print("QUICK_RENDER mode: Using balanced mesh resolution (increased for better quality)")
    print(f"  TORUS_MAJOR_SEG: {TORUS_MAJOR_SEG} (normal: 180)")
    print(f"  TORUS_MINOR_SEG: {TORUS_MINOR_SEG} (normal: 110)")
    print(f"  LANE_POINTS: {LANE_POINTS} (normal: 900)")
    print(f"  CURVE_RESOLUTION_U: {CURVE_RESOLUTION_U} (normal: 16)")
    print(f"  BEVEL_RESOLUTION: {BEVEL_RESOLUTION} (normal: 8)")
else:
    TORUS_MAJOR_SEG = 180
    TORUS_MINOR_SEG = 110
    LANE_POINTS     = 900
    CURVE_RESOLUTION_U = 16
    BEVEL_RESOLUTION   = 8

# Adjust depth passes for quick render modes (reduces processing time)
# This is a MAJOR speedup - fewer passes = fewer boolean operations
if ULTRA_QUICK_RENDER:
    # Ultra quick: only surface pass (fastest, minimal grooves)
    CW_PASSES = 1
    CCW_PASSES = 1
    print(f"  Ultra quick: Reduced passes: CW_PASSES={CW_PASSES}, CCW_PASSES={CCW_PASSES} (normal: CW={CW_PASSES_BASE}, CCW={CCW_PASSES_BASE})")
    print(f"  This means only surface-level grooves will be created (no deepening passes)")
elif QUICK_RENDER:
    # Quick render: minimal passes (1 for CW, 1 for CCW - just surface level)
    # This skips all the deepening passes which are the real bottleneck
    CW_PASSES = 1
    CCW_PASSES = 1
    print(f"  Quick render: Reduced passes: CW_PASSES={CW_PASSES}, CCW_PASSES={CCW_PASSES} (normal: CW={CW_PASSES_BASE}, CCW={CCW_PASSES_BASE})")
    print(f"  This means only surface-level grooves will be created (no deepening passes)")
else:
    # Normal render: use base values
    CW_PASSES = CW_PASSES_BASE
    CCW_PASSES = CCW_PASSES_BASE

# =========================
# BREAK-OFF LEGS (PRINT SUPPORT)
# =========================

LEG_HEIGHT = 2.0        # mm (lift above build plate)
LEG_RADIUS = 0.6        # mm (plate contact radius)
LEG_NECK_RADIUS = 0.4   # mm (weak point near torus)
LEG_COUNT = 72           # number of legs
LEG_INSET = 0.3         # mm inset into torus for good union
LEG_RADIAL_OFFSETS = [
    +1.5,
    +0.9,
    +0.3,
    -0.3,
    -0.9,
    -1.5,
]


# Voxel remesh toggle
USE_VOXEL_REMESH = False
VOXEL_SIZE_MM    = 0.25

# 3D Printing base/platform for pieces
ADD_PRINT_BASE = False  # Add a square base to each piece
BASE_THICKNESS = 2.0   # Thickness of the base (mm)
BASE_MARGIN    = 5.0   # Extra margin around torus (mm)
BASE_OFFSET    = 0.1   # Small gap between base and torus to allow easy removal (mm)

# Circular toroidal base (overlaps torus in toroidal direction, parallel to R)
ADD_CIRCULAR_TOROIDAL_BASE = False  # Add a circular base overlapping torus in toroidal direction
CIRCULAR_BASE_THICKNESS = 1.0  # Thickness of circular base (mm)
CIRCULAR_BASE_RADIUS = None    # If None, uses OUTER_RADIUS + 2.0mm margin
CIRCULAR_BASE_OVERLAP = 0.5    # How much the base overlaps into the torus (mm) - positive = overlaps upward

# Collection name base (will have timestamp appended for uniqueness)
COLLECTION_NAME_BASE = "Rodin_Torus_4Pieces"

# Output mode: "full" = only full Torus_grooved, "pieces" = only 4 pieces, "both" = both
OUTPUT_MODE = "full"  # Options: "full", "pieces", or "both"

# =========================
# LOCKING SYSTEM PARAMETERS
# =========================

ENABLE_TORUS_LOCKS = True

LOCK_LENGTH   = 8.0    # mm (toroidal direction)
LOCK_DEPTH    = 3.0    # mm (radial direction)
LOCK_HEIGHT   = 4.0    # mm (Z direction)

LOCK_CLEARANCE = 0.25  # mm (FDM tolerance)
LOCK_Z_OFFSET  = 0.0   # mm (vertical offset of lock center)

LOCK_COUNT_PER_SEAM = 2  # number of locks per seam

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

if R_TUBE <= 0:
    raise ValueError("Invalid radii: R_TUBE must be positive")

if GROOVE_DEPTH > GROOVE_R:
    raise ValueError("GROOVE_DEPTH must be ≤ GROOVE_R.")

# Calculate layer separation depth
# Required center-to-center separation: Δh = d_OD + c
LAYER_SEPARATION = WIRE_OD + CLEARANCE

# Base sink for outer layer (shallower grooves)
SINK_OUTER = max(0.0, GROOVE_R - GROOVE_DEPTH)

# Maximum allowed sink so grooves never cut through the torus wall.
# Groove center is sunk by sink; bevel radius GROOVE_R extends inward, so we need sink + GROOVE_R < R_TUBE.
MAX_SINK = min(MAX_GROOVE_SINK_FRACTION * R_TUBE, max(0.0, R_TUBE - GROOVE_R))

# Sink for inner layer (deeper grooves)
# CCW_DEPTH_FACTOR is used in both modes to control CCW groove depth for outside visibility
CCW_DEPTH_OFFSET = CCW_DEPTH_FACTOR * GROOVE_DEPTH

# Intermediate CCW groove depth (half of full CCW depth for stepped profile)
SINK_INTERMEDIATE_RAW = SINK_OUTER + 0.5 * CCW_DEPTH_OFFSET

if LAYER_SEPARATION_MODE == "symmetric":
    # Symmetric placement: outer layer at r0 - Δh/2, inner at r0 + Δh/2
    # This keeps mean radius matched for balanced impedances
    # But we still use CCW_DEPTH_FACTOR for the actual CCW groove depth
    SINK_INNER = min(SINK_OUTER + CCW_DEPTH_OFFSET, MAX_SINK)
    SINK_INTERMEDIATE = min(SINK_INTERMEDIATE_RAW, SINK_INNER)
    print(f"Using symmetric layer separation (with CCW depth factor):")
    print(f"  Outer layer (CW) sink: {SINK_OUTER:.3f} mm")
    print(f"  CCW groove depths (3-step profile):")
    print(f"    Step 1 (surface): {SINK_OUTER:.3f} mm")
    print(f"    Step 2 (intermediate): {SINK_INTERMEDIATE:.3f} mm (0.5× depth)")
    print(f"    Step 3 (deep): {SINK_INNER:.3f} mm (full depth)")
    print(f"  CCW depth offset: {CCW_DEPTH_OFFSET:.3f} mm ({CCW_DEPTH_FACTOR} × {GROOVE_DEPTH:.2f} mm groove depth)")
    print(f"  Max sink (keeps torus intact): {MAX_SINK:.3f} mm ({MAX_GROOVE_SINK_FRACTION}× R_TUBE, cap R_TUBE-GROOVE_R)")
    print(f"  Full separation would be: {LAYER_SEPARATION:.3f} mm (WIRE_OD={WIRE_OD:.2f} + CLEARANCE={CLEARANCE:.2f})")
    print(f"  Note: Using {CCW_DEPTH_FACTOR}× groove depth for better outside visibility")
else:
    # "deeper" mode: outer layer near surface, inner layer deeper
    # Use CCW_DEPTH_FACTOR to make CCW grooves visible from outside
    SINK_INNER = min(SINK_OUTER + CCW_DEPTH_OFFSET, MAX_SINK)
    SINK_INTERMEDIATE = min(SINK_INTERMEDIATE_RAW, SINK_INNER)
    print(f"Using deeper layer separation (with visibility factor):")
    print(f"  Outer layer (CW) sink: {SINK_OUTER:.3f} mm")
    print(f"  CCW groove depths (3-step profile):")
    print(f"    Step 1 (surface): {SINK_OUTER:.3f} mm")
    print(f"    Step 2 (intermediate): {SINK_INTERMEDIATE:.3f} mm (0.5× depth)")
    print(f"    Step 3 (deep): {SINK_INNER:.3f} mm (full depth)")
    print(f"  CCW depth offset: {CCW_DEPTH_OFFSET:.3f} mm ({CCW_DEPTH_FACTOR} × {GROOVE_DEPTH:.2f} mm groove depth)")
    print(f"  Max sink (keeps torus intact): {MAX_SINK:.3f} mm ({MAX_GROOVE_SINK_FRACTION}× R_TUBE, cap R_TUBE-GROOVE_R)")
    print(f"  Note: Using {CCW_DEPTH_FACTOR}× groove depth for better outside visibility")
    print(f"  Full separation would be: {LAYER_SEPARATION:.3f} mm (WIRE_OD={WIRE_OD:.2f} + CLEARANCE={CLEARANCE:.2f})")

if SINK_OUTER + CCW_DEPTH_OFFSET > MAX_SINK:
    print(f"  (CCW sink clamped from {SINK_OUTER + CCW_DEPTH_OFFSET:.3f} mm to {MAX_SINK:.3f} mm to preserve torus)")

# Calculate CW deep sink endpoint for deepening passes (same max so torus always renders)
SINK_CW_DEEP = min(SINK_OUTER + CW_DEPTH_FACTOR * GROOVE_DEPTH, MAX_SINK)

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

def repair_mesh(obj, remove_doubles_dist=0.0001, fill_holes=True, make_manifold=True):
    """
    Comprehensive mesh repair function to fix holes, non-manifold geometry, and other issues.
    This is critical for 3D printing - ensures the mesh is solid and manifold.
    """
    if obj.type != 'MESH' or not obj.data:
        return False
    
    print(f"  Repairing mesh for {obj.name}...")
    
    # Ensure object is in object mode
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # Work with bmesh for better control
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    # Store initial stats
    verts_before = len(bm.verts)
    edges_before = len(bm.edges)
    faces_before = len(bm.faces)
    
    # 1. Remove doubles (duplicate vertices)
    try:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=remove_doubles_dist)
        print(f"    Removed duplicate vertices")
    except Exception as e:
        print(f"    WARNING: Could not remove doubles: {e}")
    
    # 2. Fill holes
    if fill_holes:
        try:
            # Find boundary edges (edges with only one face)
            boundary_edges = [e for e in bm.edges if len(e.link_faces) == 1]
            if boundary_edges:
                # Group into loops
                loops = _edge_loops_from_edges(boundary_edges)
                holes_filled = 0
                for loop_edges in loops:
                    try:
                        # Try holes_fill first (better for planar holes)
                        bmesh.ops.holes_fill(bm, edges=loop_edges, sides=0)
                        holes_filled += 1
                    except Exception:
                        try:
                            # Fallback to edgenet_fill
                            bmesh.ops.edgenet_fill(bm, edges=loop_edges)
                            holes_filled += 1
                        except Exception:
                            pass
                if holes_filled > 0:
                    print(f"    Filled {holes_filled} hole(s)")
        except Exception as e:
            print(f"    WARNING: Could not fill holes: {e}")
    
    # 3. Fix non-manifold edges
    try:
        # Find non-manifold edges (edges with more than 2 faces)
        non_manifold_edges = [e for e in bm.edges if len(e.link_faces) > 2]
        if non_manifold_edges:
            # Try to dissolve these edges
            bmesh.ops.dissolve_edges(bm, edges=non_manifold_edges, use_verts=True)
            print(f"    Fixed {len(non_manifold_edges)} non-manifold edge(s)")
    except Exception as e:
        print(f"    WARNING: Could not fix non-manifold edges: {e}")
    
    # 4. Recalculate face normals
    try:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        print(f"    Recalculated face normals")
    except Exception as e:
        print(f"    WARNING: Could not recalculate normals: {e}")
    
    # 5. Make manifold (remove isolated vertices/edges)
    if make_manifold:
        try:
            # Remove isolated vertices
            isolated_verts = [v for v in bm.verts if len(v.link_edges) == 0]
            if isolated_verts:
                bmesh.ops.delete(bm, geom=isolated_verts, context='VERTS')
                print(f"    Removed {len(isolated_verts)} isolated vertex/vertices")
            
            # Remove isolated edges
            isolated_edges = [e for e in bm.edges if len(e.link_faces) == 0]
            if isolated_edges:
                bmesh.ops.delete(bm, geom=isolated_edges, context='EDGES')
                print(f"    Removed {len(isolated_edges)} isolated edge(s)")
        except Exception as e:
            print(f"    WARNING: Could not make manifold: {e}")
    
    # Write back to mesh
    bm.to_mesh(obj.data)
    bm.free()
    
    # Update and validate
    obj.data.update()
    obj.data.validate()
    bpy.context.view_layer.update()
    
    # Final stats
    verts_after = len(obj.data.vertices)
    edges_after = len(obj.data.edges)
    faces_after = len(obj.data.polygons)
    
    print(f"    Mesh repair complete: {verts_before}→{verts_after} verts, {edges_before}→{edges_after} edges, {faces_before}→{faces_after} faces")
    
    return True

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
    
    # Ensure target (grooved torus) is visible
    target.hide_viewport = False
    target.hide_render = False
    
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

def boolean_intersect(target, cutter, name):
    """Boolean intersection operation"""
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    
    cutter.hide_viewport = False
    cutter.hide_render = False
    cutter.select_set(False)
    
    bpy.context.view_layer.update()
    
    mod = target.modifiers.new(name, 'BOOLEAN')
    mod.operation = 'INTERSECT'
    mod.solver    = 'EXACT'
    mod.object    = cutter
    
    bpy.context.view_layer.update()
    
    try:
        apply_modifier(target, mod.name)
    except Exception as e:
        print(f"WARNING: Boolean intersection {name} failed with EXACT solver: {e}")
        print(f"  Trying FAST solver as fallback...")
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

def create_cutting_plane(name, location, rotation, size, collection):
    """Create a large plane for cutting the torus"""
    # Create a large cube that will be used as a cutting plane
    # Size should be large enough to cut through the entire torus
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    plane = bpy.context.view_layer.objects.active
    set_obj_name(plane, name)
    
    # Apply rotation
    plane.rotation_euler = rotation
    
    link_to_collection(plane, collection)
    ensure_object_visible(plane)
    
    return plane

def create_square_base(obj, piece_idx, collection):
    """
    Create a square base/platform for a piece.
    The base is positioned at the lowest Z point and sized to fit with other pieces.
    """
    if not ADD_PRINT_BASE:
        return None
    
    print(f"\nCreating square base for piece {piece_idx}...")
    
    # Find lowest Z point
    lowest_z = find_lowest_z(obj)
    print(f"  Lowest Z point: {lowest_z:.2f} mm")
    
    # Calculate base dimensions
    # Each piece gets a square base that's half the full size
    # Full square size should cover the torus diameter plus margin
    full_size = 2 * (OUTER_RADIUS + BASE_MARGIN)
    half_size = full_size / 2.0
    
    # Calculate position based on piece index
    # Piece 1: X >= 0, Y >= 0 (first quadrant) -> center at (half_size/2, half_size/2)
    # Piece 2: X < 0, Y >= 0 (second quadrant) -> center at (-half_size/2, half_size/2)
    # Piece 3: X < 0, Y < 0 (third quadrant) -> center at (-half_size/2, -half_size/2)
    # Piece 4: X >= 0, Y < 0 (fourth quadrant) -> center at (half_size/2, -half_size/2)
    
    positions = [
        (half_size/2, half_size/2),    # Piece 1: +X, +Y
        (-half_size/2, half_size/2),   # Piece 2: -X, +Y
        (-half_size/2, -half_size/2),  # Piece 3: -X, -Y
        (half_size/2, -half_size/2),  # Piece 4: +X, -Y
    ]
    
    center_x, center_y = positions[piece_idx - 1]
    base_z = lowest_z - BASE_THICKNESS - BASE_OFFSET
    
    # Create square base as a cube
    bpy.ops.mesh.primitive_cube_add(
        size=half_size,
        location=(center_x, center_y, base_z + BASE_THICKNESS/2),
        align='WORLD'
    )
    base = bpy.context.view_layer.objects.active
    set_obj_name(base, f"{obj.name}_SquareBase")
    link_to_collection(base, collection)
    ensure_object_visible(base)
    
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
            print(f"  Square base successfully connected to {obj.name}")
            # Remove the separate base object since it's now part of the main object
            bpy.data.objects.remove(base, do_unlink=True)
            # Repair mesh after union operation
            repair_mesh(obj, remove_doubles_dist=0.0001, fill_holes=True, make_manifold=True)
            return None
        else:
            print(f"  WARNING: Could not union base to {obj.name}")
            base.select_set(False)
            obj.select_set(False)
            return base
    except Exception as e:
        print(f"  WARNING: Could not union base to {obj.name}: {e}")
        print(f"  Keeping base as separate object for manual connection")
        base.select_set(False)
        obj.select_set(False)
        return base

def create_circular_toroidal_base(obj, collection):
    """
    Create a circular base that overlaps the torus in the toroidal direction (parallel to R).
    The base is a 1mm thick circular disk positioned at the lowest Z point of the torus.
    This serves as a 3D printing support base.
    """
    if not ADD_CIRCULAR_TOROIDAL_BASE:
        return None
    
    print(f"\nCreating circular toroidal base for {obj.name}...")
    
    # Find lowest Z point
    lowest_z = find_lowest_z(obj)
    print(f"  Lowest Z point: {lowest_z:.2f} mm")
    
    # Calculate base radius
    if CIRCULAR_BASE_RADIUS is None:
        base_radius = OUTER_RADIUS + 2.0  # Default: 2mm margin beyond outer radius
    else:
        base_radius = CIRCULAR_BASE_RADIUS
    
    print(f"  Base radius: {base_radius:.2f} mm")
    print(f"  Base thickness: {CIRCULAR_BASE_THICKNESS:.2f} mm")
    print(f"  Overlap into torus: {CIRCULAR_BASE_OVERLAP:.2f} mm")
    
    # Position the base so it overlaps the torus by CIRCULAR_BASE_OVERLAP
    # The base center Z is positioned so the top of the base is at lowest_z + CIRCULAR_BASE_OVERLAP
    base_center_z = lowest_z + CIRCULAR_BASE_OVERLAP - CIRCULAR_BASE_THICKNESS / 2.0
    
    # Create circular base as a cylinder (disk)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=base_radius,
        depth=CIRCULAR_BASE_THICKNESS,
        location=(0, 0, base_center_z),
        align='WORLD'
    )
    base = bpy.context.view_layer.objects.active
    set_obj_name(base, f"{obj.name}_CircularToroidalBase")
    link_to_collection(base, collection)
    ensure_object_visible(base)
    
    # Union the base with the object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    base.select_set(True)
    bpy.context.view_layer.update()
    
    # Use boolean union to connect base to object
    mod = obj.modifiers.new("CircularBaseUnion", 'BOOLEAN')
    mod.operation = 'UNION'
    mod.solver = 'EXACT'
    mod.object = base
    bpy.context.view_layer.update()
    
    try:
        if apply_modifier(obj, "CircularBaseUnion"):
            print(f"  Circular toroidal base successfully connected to {obj.name}")
            # Remove the separate base object since it's now part of the main object
            bpy.data.objects.remove(base, do_unlink=True)
            # Repair mesh after union operation
            repair_mesh(obj, remove_doubles_dist=0.0001, fill_holes=True, make_manifold=True)
            return None
        else:
            print(f"  WARNING: Could not union circular base to {obj.name}")
            base.select_set(False)
            obj.select_set(False)
            return base
    except Exception as e:
        print(f"  WARNING: Could not union circular base to {obj.name}: {e}")
        print(f"  Keeping base as separate object for manual connection")
        base.select_set(False)
        obj.select_set(False)
        return base

def make_rect_lock(name, length, depth, height):
    """Create a rectangular lock geometry"""
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    set_obj_name(o, name)
    o.scale = (length/2, depth/2, height/2)
    bpy.ops.object.transform_apply(scale=True)
    return o

def add_breakoff_legs(obj, collection):
    """
    Adds small sacrificial legs under the torus to lift it off the build plate.
    Legs are designed to snap off cleanly after printing.
    """
    if not ADD_BREAKOFF_LEGS:
        return

    print("Adding break-off legs...")

    # Find lowest Z of torus
    lowest_z = find_lowest_z(obj)

    for i in range(LEG_COUNT):
        angle = 2 * math.pi * i / LEG_COUNT

        # Position legs evenly around torus
        x = (R_MAJOR+.3) * math.cos(angle)
        y = (R_MAJOR+.3) * math.sin(angle)

        # Create leg (two-cylinder shape: foot + neck)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=LEG_RADIUS,
            depth=LEG_HEIGHT,
            location=(x, y, lowest_z - LEG_HEIGHT/2)
        )
        foot = bpy.context.object
        set_obj_name(foot, f"BreakLeg_{i}")
        link_to_collection(foot, collection)

        bpy.ops.mesh.primitive_cylinder_add(
            radius=LEG_NECK_RADIUS,
            depth=LEG_INSET,
            location=(x, y, lowest_z + LEG_INSET/2)
        )
        neck = bpy.context.object
        set_obj_name(neck, f"BreakLegNeck_{i}")
        link_to_collection(neck, collection)

        # Union foot + neck
        mod = foot.modifiers.new("UnionNeck", 'BOOLEAN')
        mod.operation = 'UNION'
        mod.object = neck
        bpy.context.view_layer.update()
        apply_modifier(foot, "UnionNeck")
        bpy.data.objects.remove(neck, do_unlink=True)

        # Union leg to torus
        mod2 = obj.modifiers.new(f"LegUnion_{i}", 'BOOLEAN')
        mod2.operation = 'UNION'
        mod2.object = foot
        bpy.context.view_layer.update()
        apply_modifier(obj, mod2.name)

        bpy.data.objects.remove(foot, do_unlink=True)

    print("Break-off legs added.")

def add_leg_ring(obj, collection, radius_offset, angle_offset, tag):
    lowest_z = find_lowest_z(obj)

    for i in range(LEG_COUNT):
        angle = 2 * math.pi * i / LEG_COUNT + angle_offset

        x = (R_MAJOR + radius_offset) * math.cos(angle)
        y = (R_MAJOR + radius_offset) * math.sin(angle)

        # Foot
        bpy.ops.mesh.primitive_cylinder_add(
            radius=LEG_RADIUS,
            depth=LEG_HEIGHT,
            location=(x, y, lowest_z - LEG_HEIGHT/2)
        )
        foot = bpy.context.object
        set_obj_name(foot, f"BreakLeg_{tag}_{i}")
        link_to_collection(foot, collection)

        # Neck
        bpy.ops.mesh.primitive_cylinder_add(
            radius=LEG_NECK_RADIUS,
            depth=LEG_INSET,
            location=(x, y, lowest_z + LEG_INSET/2)
        )
        neck = bpy.context.object
        set_obj_name(neck, f"BreakLegNeck_{tag}_{i}")
        link_to_collection(neck, collection)

        # Union foot + neck
        mod = foot.modifiers.new("UnionNeck", 'BOOLEAN')
        mod.operation = 'UNION'
        mod.object = neck
        bpy.context.view_layer.update()
        apply_modifier(foot, "UnionNeck")
        bpy.data.objects.remove(neck, do_unlink=True)

        # Union to torus
        mod2 = obj.modifiers.new(f"LegUnion_{tag}_{i}", 'BOOLEAN')
        mod2.operation = 'UNION'
        mod2.object = foot
        bpy.context.view_layer.update()
        apply_modifier(obj, mod2.name)

        bpy.data.objects.remove(foot, do_unlink=True)

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

def make_depth_schedule(surface_sink, deep_sink, passes, mode="linear"):
    """
    Returns a list of sink depths (mm) from surface_sink to deep_sink (inclusive).
    """
    passes = max(1, int(passes))
    if passes == 1:
        return [deep_sink]

    if mode == "three_step" and passes == 3:
        mid = 0.5 * (surface_sink + deep_sink)
        return [surface_sink, mid, deep_sink]

    # default: linear interpolation including endpoints
    out = []
    for k in range(passes):
        a = k / (passes - 1)
        out.append((1 - a) * surface_sink + a * deep_sink)
    return out

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


def _keep_largest_island(bm):
    """Remove tiny loose islands (can occur when grooves intersect the cut plane)."""
    visited = set()
    islands = []

    for f in bm.faces:
        if f in visited:
            continue
        stack = [f]
        visited.add(f)
        faces = []
        area = 0.0

        while stack:
            cur = stack.pop()
            faces.append(cur)
            area += cur.calc_area()
            for e in cur.edges:
                for nf in e.link_faces:
                    if nf not in visited:
                        visited.add(nf)
                        stack.append(nf)

        islands.append((area, faces))

    if len(islands) <= 1:
        return

    islands.sort(key=lambda x: x[0], reverse=True)
    to_delete = [f for _, faces in islands[1:] for f in faces]
    if to_delete:
        bmesh.ops.delete(bm, geom=to_delete, context='FACES')

    loose_verts = [v for v in bm.verts if not v.link_faces]
    if loose_verts:
        bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')


def _edges_on_plane_boundary(bm, plane_co, plane_no, eps=1e-5):
    """Boundary edges (1 linked face) whose vertices lie on the cut plane."""
    n = plane_no.normalized()
    edges = []
    for e in bm.edges:
        if len(e.link_faces) != 1:
            continue
        v0, v1 = e.verts
        d0 = (v0.co - plane_co).dot(n)
        d1 = (v1.co - plane_co).dot(n)
        if abs(d0) <= eps and abs(d1) <= eps:
            edges.append(e)
    return edges


def _edge_loops_from_edges(edges):
    """Group edges into connected components (loops)."""
    if not edges:
        return []
    edges_set = set(edges)
    loops = []

    while edges_set:
        seed = edges_set.pop()
        stack = [seed]
        group = {seed}

        while stack:
            e = stack.pop()
            for v in e.verts:
                for ne in v.link_edges:
                    if ne in edges_set:
                        edges_set.remove(ne)
                        stack.append(ne)
                        group.add(ne)

        loops.append(list(group))

    return loops


def _fill_plane_caps(bm, plane_co, plane_no, eps=1e-5):
    """
    Fill the open cut created by bisect by finding boundary edges on the plane
    and filling each connected loop.
    """
    boundary_edges = _edges_on_plane_boundary(bm, plane_co, plane_no, eps=eps)
    if not boundary_edges:
        return

    loops = _edge_loops_from_edges(boundary_edges)
    for loop_edges in loops:
        # holes_fill is usually the best for planar caps
        try:
            bmesh.ops.holes_fill(bm, edges=loop_edges, sides=0)
        except Exception:
            # fallback if holes_fill chokes on a loop
            try:
                bmesh.ops.edgenet_fill(bm, edges=loop_edges)
            except Exception:
                pass


def bisect_keep_half(obj, plane_co, plane_no, keep_positive=True, fill=True, eps=1e-5, remove_doubles_dist=0.0001):
    """
    Cut obj by plane and KEEP one side.
    + signed distance => positive side along plane_no.

    keep_positive=True  -> keep positive half-space, delete negative
    keep_positive=False -> keep negative half-space, delete positive
    """
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    plane_no = plane_no.normalized()

    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]

    # NOTE: Blender 5.x bisect_plane does NOT support use_fill
    bmesh.ops.bisect_plane(
        bm,
        geom=geom,
        plane_co=plane_co,
        plane_no=plane_no,
        clear_inner=keep_positive,       # removes negative side
        clear_outer=not keep_positive,   # removes positive side
        dist=eps,                        # tolerance for plane classification
    )

    if fill:
        _fill_plane_caps(bm, plane_co, plane_no, eps=eps)

    # Cleanup
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=remove_doubles_dist)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _keep_largest_island(bm)
    
    # Additional hole filling pass - try to fill any remaining boundary edges
    if fill:
        try:
            boundary_edges = _edges_on_plane_boundary(bm, plane_co, plane_no, eps=eps*10)  # Wider tolerance
            if boundary_edges:
                loops = _edge_loops_from_edges(boundary_edges)
                for loop_edges in loops:
                    try:
                        bmesh.ops.holes_fill(bm, edges=loop_edges, sides=0)
                    except Exception:
                        try:
                            bmesh.ops.edgenet_fill(bm, edges=loop_edges)
                        except Exception:
                            pass
        except Exception:
            pass

    bm.to_mesh(me)
    bm.free()
    me.update()
    me.validate()

def split_into_4_pieces_bisect(grooved, collection, add_base=False):
    """
    Returns list of 4 (or fewer) quadrant pieces created from `grooved`.
    Assumes grooved is at origin and transforms are applied.
    """
    pieces = []
    quadrants = [
        ("Piece_01", True,  True,  "X>=0, Y>=0"),
        ("Piece_02", False, True,  "X<0,  Y>=0"),
        ("Piece_03", False, False, "X<0,  Y<0"),
        ("Piece_04", True,  False, "X>=0, Y<0"),
    ]

    for piece_idx, (piece_name, keep_x_pos, keep_y_pos, desc) in enumerate(quadrants, 1):
        print(f"\nCreating {piece_name} ({desc})...")

        piece = grooved.copy()
        piece.data = grooved.data.copy()
        link_to_collection(piece, collection)
        set_obj_name(piece, piece_name)
        ensure_object_visible(piece)

        # Ensure local == world for plane cuts
        bpy.context.view_layer.objects.active = piece
        piece.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        piece.select_set(False)

        # Bisect by X=0 then Y=0
        bisect_keep_half(
            piece,
            plane_co=Vector((0, 0, 0)),
            plane_no=Vector((1, 0, 0)),
            keep_positive=keep_x_pos,
            fill=True,
        )
        bisect_keep_half(
            piece,
            plane_co=Vector((0, 0, 0)),
            plane_no=Vector((0, 1, 0)),
            keep_positive=keep_y_pos,
            fill=True,
        )

        piece.data.update()
        piece.data.validate()

        if len(piece.data.vertices) == 0:
            print(f"  ❗ {piece_name} ended empty -> deleting")
            bpy.data.objects.remove(piece, do_unlink=True)
            continue

        print(f"  ✅ {piece_name}: {len(piece.data.vertices)} verts, {len(piece.data.polygons)} faces")
        
        # Repair mesh after bisect operations (fixes holes from cutting)
        print(f"  Repairing {piece_name} mesh...")
        repair_mesh(piece, remove_doubles_dist=0.0001, fill_holes=True, make_manifold=True)

        if add_base and ADD_PRINT_BASE:
            create_square_base(piece, piece_idx, collection)

        pieces.append(piece)

    return pieces

def add_locks_to_piece(piece, piece_index):
    """
    Adds male/female locks to a torus quarter.
    Convention:
      X+ seam → MALE
      Y+ seam → FEMALE
    """
    if not ENABLE_TORUS_LOCKS:
        return

    # Directions in object space
    TOROIDAL = Vector((0, 1, 0))
    RADIAL   = Vector((1, 0, 0))
    ZAXIS    = Vector((0, 0, 1))

    # Determine which seams this piece has
    is_x_pos = piece_index in (1, 4)
    is_y_pos = piece_index in (1, 2)

    for k in range(LOCK_COUNT_PER_SEAM):
        z_shift = (k - (LOCK_COUNT_PER_SEAM-1)/2) * (LOCK_HEIGHT * 1.4)

        # ---------- MALE LOCK (X seam) ----------
        if is_x_pos:
            lock = make_rect_lock(
                f"{piece.name}_LOCK_MALE_{k}",
                LOCK_LENGTH, LOCK_DEPTH, LOCK_HEIGHT
            )

            lock.location = (
                RADIAL * (LOCK_DEPTH * 0.5)
                + ZAXIS * (LOCK_Z_OFFSET + z_shift)
            )

            lock.rotation_euler = TOROIDAL.to_track_quat('Y','Z').to_euler()
            link_to_collection(lock, piece.users_collection[0])

            boolean_intersect(piece, lock, f"MaleLock_{k}")
            bpy.data.objects.remove(lock, do_unlink=True)

        # ---------- FEMALE LOCK (Y seam) ----------
        if is_y_pos:
            socket = make_rect_lock(
                f"{piece.name}_LOCK_SOCKET_{k}",
                LOCK_LENGTH + LOCK_CLEARANCE,
                LOCK_DEPTH + LOCK_CLEARANCE,
                LOCK_HEIGHT + LOCK_CLEARANCE
            )

            socket.location = (
                Vector((0, LOCK_DEPTH * 0.5, 0))
                + ZAXIS * (LOCK_Z_OFFSET + z_shift)
            )

            socket.rotation_euler.z = math.pi / 2
            link_to_collection(socket, piece.users_collection[0])

            boolean_diff(piece, socket, f"FemaleLock_{k}")
            bpy.data.objects.remove(socket, do_unlink=True)

# =========================
# ---- MAIN EXECUTION ----
# =========================

def main():
    # Validate OUTPUT_MODE
    if OUTPUT_MODE not in ("full", "pieces", "both"):
        raise ValueError(f"OUTPUT_MODE must be 'full', 'pieces', or 'both', got '{OUTPUT_MODE}'")
    
    print(f"\n{'='*60}")
    print(f"OUTPUT MODE: {OUTPUT_MODE}")
    if OUTPUT_MODE == "full":
        print("  Will generate: Full Torus_grooved only")
    elif OUTPUT_MODE == "pieces":
        print("  Will generate: 4 pieces only")
    else:
        print("  Will generate: Both full Torus_grooved and 4 pieces")
    print(f"{'='*60}\n")
    
    ensure_units_mm()
    clear_scene()
    ensure_collection_visible()
    
    # Create a unique collection name with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Update collection name based on output mode
    if OUTPUT_MODE == "full":
        collection_name = f"Rodin_Torus_Full_{timestamp}"
    elif OUTPUT_MODE == "pieces":
        collection_name = f"Rodin_Torus_4Pieces_{timestamp}"
    else:  # both
        collection_name = f"{COLLECTION_NAME_BASE}_{timestamp}"
    
    # Create the named collection for all objects
    collection = get_or_create_collection(collection_name)
    print(f"Using collection: {collection.name}")
    print(f"Using timestamp for files: {timestamp}")

    # Make grooved torus (same as original script)
    print("\n=== Creating grooved torus ===")
    
    # Remove any existing Torus_grooved objects to avoid naming conflicts
    for obj in list(bpy.data.objects):
        if obj.name.startswith("Torus_grooved"):
            print(f"  Removing existing object: {obj.name}")
            bpy.data.objects.remove(obj, do_unlink=True)
    
    grooved_obj = make_torus(collection)
    set_obj_name(grooved_obj, "Torus_grooved")
    ensure_object_visible(grooved_obj)
    grooved = grooved_obj
    
    # Verify initial geometry
    grooved.data.update()
    initial_verts = len(grooved.data.vertices)
    initial_faces = len(grooved.data.polygons)
    print(f"  Created '{grooved.name}': {initial_verts} vertices, {initial_faces} faces")
    
    if initial_verts == 0:
        print("  ERROR: Grooved torus has no geometry after creation!")
        return

    # -------------------------
    # Depth endpoints + schedules
    # -------------------------
    cw_schedule  = make_depth_schedule(SINK_OUTER, SINK_CW_DEEP, CW_PASSES,  DEPTH_SCHEDULE_MODE)
    ccw_schedule = make_depth_schedule(SINK_OUTER, SINK_INNER,   CCW_PASSES, DEPTH_SCHEDULE_MODE)

    print("CW depth schedule :", [f"{d:.3f}" for d in cw_schedule])
    print("CCW depth schedule:", [f"{d:.3f}" for d in ccw_schedule])

    # Calculate total operations for comparison
    num_phases_normal = 3
    num_passes_normal = CW_PASSES_BASE + CCW_PASSES_BASE
    total_ops_normal = num_passes_normal * num_phases_normal

    # Reduce phases in quick render mode (major speedup - fewer curves/booleans per pass)
    if ULTRA_QUICK_RENDER:
        # Ultra quick: only 1 phase (fastest, but less complete pattern)
        phase_degs = [0]
        cw_colors  = [(1,0,0)]
        ccw_colors = [(1,1,0)]
        num_phases = 1
        print(f"  Ultra quick render: Using 1 phase per pass (normal: 3 phases)")
    elif QUICK_RENDER:
        # Quick render: reduce to 2 phases (good balance of speed vs completeness)
        phase_degs = [0, 180]  # Use 0 and 180 instead of 0, 120, 240
        cw_colors  = [(1,0,0), (0,1,0)]
        ccw_colors = [(1,1,0), (1,0,1)]
        num_phases = 2
        print(f"  Quick render: Using 2 phases per pass (normal: 3 phases)")
    else:
        # Normal render: all 3 phases
        phase_degs = [0, 120, 240]
        cw_colors  = [(1,0,0), (0,1,0), (0,0,1)]
        ccw_colors = [(1,1,0), (1,0,1), (0,1,1)]
        num_phases = 3
    
    # Calculate and display speedup summary
    num_passes_current = CW_PASSES + CCW_PASSES
    total_ops_current = num_passes_current * num_phases
    speedup_factor = total_ops_normal / total_ops_current if total_ops_current > 0 else 1.0
    
    print(f"\n{'='*60}")
    print(f"GROOVE OPERATIONS SUMMARY:")
    print(f"  Normal mode: {num_passes_normal} passes × {num_phases_normal} phases = {total_ops_normal} boolean operations")
    print(f"  Current mode: {num_passes_current} passes × {num_phases} phases = {total_ops_current} boolean operations")
    print(f"  SPEEDUP: {speedup_factor:.1f}x faster ({100*(1-1/speedup_factor):.0f}% fewer operations)")
    print(f"{'='*60}\n")

    # Validate grooved torus before starting groove passes
    grooved.data.update()
    grooved.data.validate()
    bpy.context.view_layer.update()
    initial_verts = len(grooved.data.vertices)
    initial_faces = len(grooved.data.polygons)
    print(f"\nGrooved torus before groove passes: {initial_verts} vertices, {initial_faces} faces")
    
    if initial_verts == 0:
        print("ERROR: Grooved torus is empty before starting groove passes!")
        return
    
    # Make apply_pass_for_three_phases visible to grooved/collection
    def apply_pass_for_three_phases(q_val, phase_degs, color_list, sink_depth, pass_tag):
        """Create 3 cutters (phases) for one direction and one sink depth, boolean them, then cleanup."""
        # Ensure we're still working with the correct grooved object
        grooved_obj = grooved
        if grooved_obj.name not in bpy.data.objects:
            print(f"    ERROR: Grooved torus '{grooved_obj.name}' no longer exists!")
            return
        
        # Get fresh reference to ensure we have the current object
        grooved_obj = bpy.data.objects[grooved_obj.name]
        
        pass_cutters = []
        for j, deg in enumerate(phase_degs):
            name = f"{pass_tag}_q{q_val:+d}_deg{deg:03d}"
            curve = make_lane_curve(name, deg, q_val, color_list[j], sink_depth)
            if curve is None:
                continue
            link_to_collection(curve, collection)

            cutter = curve_to_mesh(curve)
            if cutter is None or len(cutter.data.vertices) == 0 or len(cutter.data.polygons) == 0:
                if cutter is not None:
                    bpy.data.objects.remove(cutter, do_unlink=True)
                continue

            link_to_collection(cutter, collection)
            cutter.hide_viewport = True
            cutter.hide_render   = True
            pass_cutters.append(cutter)

        for idx, c in enumerate(pass_cutters):
            # Get fresh reference to grooved object
            grooved_obj = bpy.data.objects[grooved.name]
            
            # Validate grooved torus before boolean
            grooved_obj.data.update()
            grooved_obj.data.validate()
            verts_before = len(grooved_obj.data.vertices)
            faces_before = len(grooved_obj.data.polygons)
            
            if verts_before == 0:
                print(f"    ERROR: Grooved torus is empty before cut {idx+1}, aborting pass!")
                break
            
            boolean_diff(grooved_obj, c, name=f"{pass_tag}_cut_{idx:02d}")
            
            # Get fresh reference again after boolean (object might have been modified)
            grooved_obj = bpy.data.objects[grooved.name]
            
            # Quick repair after each boolean to prevent holes from accumulating
            # (light repair - just remove doubles and validate)
            try:
                bm = bmesh.new()
                bm.from_mesh(grooved_obj.data)
                bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
                bm.to_mesh(grooved_obj.data)
                bm.free()
            except Exception:
                pass  # If repair fails, continue anyway
            
            # Validate grooved torus after boolean
            grooved_obj.data.update()
            grooved_obj.data.validate()
            bpy.context.view_layer.update()
            verts_after = len(grooved_obj.data.vertices)
            faces_after = len(grooved_obj.data.polygons)
            
            # Ensure grooved torus stays visible after each boolean operation
            ensure_object_visible(grooved_obj)
            grooved_obj.hide_viewport = False
            grooved_obj.hide_render = False
            
            if verts_after == 0:
                print(f"    ERROR: Grooved torus became empty after cut {idx+1}!")
                print(f"      Before: {verts_before} vertices, {faces_before} faces")
                print(f"      After: {verts_after} vertices, {faces_after} faces")
                break
            else:
                print(f"    Cut {idx+1} complete: {verts_before} -> {verts_after} vertices, {faces_before} -> {faces_after} faces")

        for c in pass_cutters:
            bpy.data.objects.remove(c, do_unlink=True)

    # CW passes
    print(f"\n=== Applying CW groove passes ===")
    for pi, sink in enumerate(cw_schedule):
        print(f"  CW pass {pi+1}/{len(cw_schedule)}: sink={sink:.3f}mm")
        apply_pass_for_three_phases(+Q, phase_degs, cw_colors, sink, pass_tag=f"CWpass{pi:02d}")

    # CCW passes
    print(f"\n=== Applying CCW groove passes ===")
    for pi, sink in enumerate(ccw_schedule):
        print(f"  CCW pass {pi+1}/{len(ccw_schedule)}: sink={sink:.3f}mm")
        apply_pass_for_three_phases(-Q, phase_degs, ccw_colors, sink, pass_tag=f"CCWpass{pi:02d}")

    # Ensure grooved torus is visible and valid
    print(f"\n=== Ensuring grooved torus visibility ===")
    # Get fresh reference to grooved object (in case it was modified)
    if grooved.name not in bpy.data.objects:
        print(f"ERROR: Grooved torus '{grooved.name}' no longer exists!")
        return
    
    grooved = bpy.data.objects[grooved.name]
    
    # Make absolutely sure it's in the collection and visible
    link_to_collection(grooved, collection)
    ensure_object_visible(grooved)
    grooved.hide_viewport = False
    grooved.hide_render = False
    grooved.hide_select = False
    grooved.select_set(False)
    
    # Validate geometry
    grooved.data.update()
    grooved.data.validate()
    bpy.context.view_layer.update()
    
    final_verts = len(grooved.data.vertices)
    final_faces = len(grooved.data.polygons)
    print(f"  Grooved torus '{grooved.name}': {final_verts} vertices, {final_faces} faces")
    
    if final_verts == 0:
        print(f"  ERROR: Grooved torus is EMPTY! Geometry was destroyed during boolean operations.")
        print(f"  This usually means the cutters were too large or positioned incorrectly.")
        return
    else:
        print(f"  Grooved torus is visible in viewport and render")
    
    add_breakoff_legs(grooved, collection)
#    half_step = math.pi / LEG_COUNT

#    for k, r_off in enumerate(LEG_RADIAL_OFFSETS):
#        add_leg_ring(
#            obj=grooved,
#            collection=collection,
#            radius_offset=r_off,
#            angle_offset=0.0,
#            tag=f"r{k}_A"
#        )

#        add_leg_ring(
#            obj=grooved,
#            collection=collection,
#            radius_offset=r_off,
#            angle_offset=half_step,
#            tag=f"r{k}_B"
#        )

#    print(f"{2 * len(LEG_RADIAL_OFFSETS) * LEG_COUNT} break-off legs added.")


    # Final validation and mesh repair
    grooved.data.update()
    if len(grooved.data.vertices) == 0:
        print("ERROR: Grooved torus has no vertices after all cuts!")
        return
    else:
        print(f"Grooved torus final: {len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces")
    
    # Repair mesh after all groove operations (fixes holes from boolean operations)
    print(f"\n=== Repairing grooved torus mesh ===")
    repair_mesh(grooved, remove_doubles_dist=0.0001, fill_holes=True, make_manifold=True)

    # =========================
    # ADD CIRCULAR TOROIDAL BASE (if enabled)
    # =========================
    if ADD_CIRCULAR_TOROIDAL_BASE:
        print(f"\n=== Adding circular toroidal base ===")
        if OUTPUT_MODE in ("full", "both"):
            # Add base to full grooved torus
            create_circular_toroidal_base(grooved, collection)
            grooved.data.update()
            grooved.data.validate()
            bpy.context.view_layer.update()
    
    # =========================
    # EXPORT COMPLETE GROOVED TORUS
    # =========================
    out = get_output_dir()
    pieces = []  # Initialize pieces list
    
    if OUTPUT_MODE in ("full", "both"):
        print(f"\n=== Exporting complete grooved torus ===")
        
        # Final mesh repair before export
        print("  Performing final mesh repair before export...")
        repair_mesh(grooved, remove_doubles_dist=0.0001, fill_holes=True, make_manifold=True)
        
        # Ensure grooved torus is ready for export
        grooved.data.update()
        grooved.data.validate()
        bpy.context.view_layer.update()
        
        if len(grooved.data.vertices) > 0:
            complete_filename = f"torus_grooved_complete_{WIND_LABEL}_{timestamp}.stl"
            complete_filepath = os.path.join(out, complete_filename)
            
            try:
                export_stl(grooved, complete_filepath)
                print(f"  Exported: {complete_filename} ({len(grooved.data.vertices)} vertices, {len(grooved.data.polygons)} faces)")
            except Exception as e:
                print(f"  ERROR exporting complete torus: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"  WARNING: Complete grooved torus is empty, skipping export")
    else:
        print(f"\n=== Skipping complete grooved torus export (OUTPUT_MODE='{OUTPUT_MODE}') ===")

    # =========================
    # SPLIT INTO 4 PIECES (BMesh bisect)
    # =========================
    if OUTPUT_MODE in ("pieces", "both"):
        print(f"\n=== Splitting grooved torus into 4 pieces (BMesh bisect) ===")

        bpy.context.view_layer.objects.active = grooved
        grooved.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        grooved.select_set(False)
        grooved.data.update()
        grooved.data.validate()
        bpy.context.view_layer.update()

        pieces = split_into_4_pieces_bisect(grooved, collection, add_base=True)
        print(f"\nCreated {len(pieces)} pieces")
        
        # =========================
        # ADD CIRCULAR TOROIDAL BASE TO PIECES (if enabled)
        # =========================
        if ADD_CIRCULAR_TOROIDAL_BASE:
            print("\n=== Adding circular toroidal base to pieces ===")
            for i, piece in enumerate(pieces, 1):
                if piece and piece.name in bpy.data.objects:
                    create_circular_toroidal_base(piece, collection)
                    piece.data.update()
                    piece.data.validate()
        
        # =========================
        # ADD MECHANICAL LOCKS TO PIECES
        # =========================
        print("\n=== Adding mechanical locks to pieces ===")
        for i, piece in enumerate(pieces, 1):
            if piece and piece.name in bpy.data.objects:
                add_locks_to_piece(piece, i)
                piece.data.update()
                piece.data.validate()
        
        # Ensure grooved torus is still visible (it should be, as we created copies for pieces)
        ensure_object_visible(grooved)
        grooved.hide_viewport = False
        grooved.hide_render = False
        collection.hide_viewport = False
        collection.hide_render = False
        print(f"  Original grooved torus '{grooved.name}' remains visible")

        # =========================
        # EXPORT PIECES
        # =========================
        print(f"\n=== Exporting pieces ===")
        
        for i, piece in enumerate(pieces, 1):
            if piece is None or piece.name not in bpy.data.objects:
                print(f"  Skipping piece {i} (invalid)")
                continue
            
            piece.data.update()
            if len(piece.data.vertices) == 0:
                print(f"  Skipping piece {i} (empty)")
                continue
            
            # Final mesh repair before export
            print(f"  Performing final mesh repair for piece {i} before export...")
            repair_mesh(piece, remove_doubles_dist=0.0001, fill_holes=True, make_manifold=True)
            
            filename = f"torus_grooved_piece_{i:02d}_{WIND_LABEL}_{timestamp}.stl"
            filepath = os.path.join(out, filename)
            
            try:
                export_stl(piece, filepath)
                print(f"  Exported: {filename} ({len(piece.data.vertices)} vertices, {len(piece.data.polygons)} faces)")
            except Exception as e:
                print(f"  ERROR exporting piece {i}: {e}")
                import traceback
                traceback.print_exc()
    else:
        print(f"\n=== Skipping 4 pieces generation (OUTPUT_MODE='{OUTPUT_MODE}') ===")
    
    # Final visibility check
    print("\nFinal visibility check...")
    # Ensure grooved torus is visible
    if grooved and grooved.name in bpy.data.objects:
        ensure_object_visible(grooved)
        grooved.hide_viewport = False
        grooved.hide_render = False
        grooved.select_set(False)
        vertex_count = len(grooved.data.vertices) if grooved.data and hasattr(grooved.data, 'vertices') else 0
        face_count = len(grooved.data.polygons) if grooved.data and hasattr(grooved.data, 'polygons') else 0
        print(f"  {grooved.name} (GROOVED TORUS): visible, {vertex_count} vertices, {face_count} faces")
    
    if OUTPUT_MODE in ("pieces", "both") and pieces:
        for piece in pieces:
            if piece and piece.name in bpy.data.objects:
                ensure_object_visible(piece)
                piece.select_set(False)
                vertex_count = len(piece.data.vertices) if piece.data and hasattr(piece.data, 'vertices') else 0
                face_count = len(piece.data.polygons) if piece.data and hasattr(piece.data, 'polygons') else 0
                print(f"  {piece.name}: visible, {vertex_count} vertices, {face_count} faces")
    
    bpy.context.view_layer.update()
    
    # Generate appropriate blend filename based on output mode
    if OUTPUT_MODE == "full":
        blend_filename = f"torus_grooved_full_{WIND_LABEL}_{timestamp}.blend"
    elif OUTPUT_MODE == "pieces":
        blend_filename = f"torus_grooved_4pieces_{WIND_LABEL}_{timestamp}.blend"
    else:  # both
        blend_filename = f"torus_grooved_full_and_4pieces_{WIND_LABEL}_{timestamp}.blend"
    
    blend_filepath = os.path.join(out, blend_filename)
    bpy.ops.wm.save_as_mainfile(filepath=blend_filepath)
    print(f"\nScene saved to: {blend_filename}")
    print(f"\nAll files use timestamp: {timestamp}")
    print(f"Output mode: {OUTPUT_MODE}")

if __name__ == "__main__":
    main()
