import bpy, math, json, os, datetime
from mathutils import Vector
import bmesh
import uuid


# ============================================================
# PARAMETERS
# ============================================================
R_MAJOR = 100.0
R_RATIO = 0.30

TORUS_P = 3
TORUS_Q = 2


RES = 600
CIRC_TURNS = -TORUS_P     # start small: 0.05, 0.10, 0.25, 0.50, 1.0
CIRC_OFFSET_DEG = -90.0  # rigid rotate all profiles together (aim knob)
CIRC_GAIN = 1        # >1 exaggerates rotation for debugging

CHORD = 30.0
THICKNESS = 0.15
CAMBER = 0.06
CAMBER_POS = 0.4

GRID_SPACING = 100.0
PHASES = [ 0]
AMPLS  = [0  ]
CIRCS = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25]  # 0..90 degrees


# ============================================================
# CLEAN PREVIOUS
# ============================================================
RUN_ID = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
NAME_PREFIX = f"TorusKnot_P{TORUS_P}_Q{TORUS_Q}_{RUN_ID}"

#for o in list(bpy.data.objects):
#    if o.name.startswith("TorusKnot") or o.name.startswith("Trefoil") or o.name.startswith("Label"):
#        bpy.data.objects.remove(o, do_unlink=True)


# ============================================================
# HELPERS
# ============================================================

def enable_stl_addon():
    for m in ("io_mesh_stl", "io_scene_stl"):
        try:
            bpy.ops.preferences.addon_enable(module=m)
        except:
            pass

def export_stl_selected(filepath: str):
    enable_stl_addon()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True, ascii_format=False)
    else:
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True, ascii=False)


# ============================================================
# CODEX
# ============================================================
DATA_ROOT = os.path.expanduser("~/trefoil_codex")
os.makedirs(DATA_ROOT, exist_ok=True)
CODEX = os.path.join(DATA_ROOT,"TREFOIL_CODEX.json")
today=str(datetime.date.today())
codex = json.load(open(CODEX)) if os.path.exists(CODEX) else {}


# ============================================================
# MATERIALS
# ============================================================
def mat(name,color):
    m=bpy.data.materials.get(name)
    if not m:
        m=bpy.data.materials.new(name)
        m.use_nodes=True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=color
    return m

mat_bottom=mat("Bottom",(0.9,0.2,0.2,1))
mat_top=mat("Top",(0.2,0.6,1.0,1))
mat_stripe = mat("Stripe",(1.0, 0.9, 0.1, 1.0))

# ============================================================
# GEOMETRY
# ============================================================
def torus_knot(t, p=2, q=3):
    R = R_MAJOR
    r = R_RATIO * R_MAJOR
    return Vector(((R + r * math.cos(q * t)) * math.cos(p * t),
                   (R + r * math.cos(q * t)) * math.sin(p * t),
                   r * math.sin(q * t)))


def resample_path(raw,N):
    L=[0]
    for i in range(1,len(raw)): L.append(L[-1]+(raw[i]-raw[i-1]).length)
    out=[]
    for k in range(N):
        s=L[-1]*k/(N-1)
        for i in range(1,len(raw)):
            if L[i]>=s:
                t=(s-L[i-1])/(L[i]-L[i-1])
                out.append(raw[i-1].lerp(raw[i],t))
                break
    return out

# ============================================================
# AIRFOIL
# ============================================================
def camber(x):
    p=CAMBER_POS; m=CAMBER
    if x<p: return m/p**2*(2*p*x-x*x)
    return m/(1-p)**2*((1-2*p)+2*p*x-x*x)

def thickness(x):
    t=THICKNESS
    return 5*t*(0.2969*math.sqrt(x)-0.126*x-0.3516*x**2+0.2843*x**3-0.1015*x**4)

def airfoil(n=120):
    up,lo=[],[]
    for i in range(n+1):
        x=i/n; yt=thickness(x); yc=camber(x)
        up.append((x,yc+yt)); lo.append((x,yc-yt))
    return up+list(reversed(lo[1:-1]))

# ============================================================
# BUILD VARIANT
# ============================================================
def make_variant(phase,ampl,gx,gy,idx):

    curve=bpy.data.curves.new("Trefoil","CURVE")
    curve.dimensions='3D'
    s=curve.splines.new("POLY"); s.points.add(RES)

    raw = [torus_knot(2*math.pi*i/(RES*3), TORUS_P, TORUS_Q ) for i in range(RES*3)]

    pts=resample_path(raw,RES+1)

    for i,p in enumerate(pts): s.points[i].co=(p.x,p.y,p.z,1)
    s.use_cyclic_u=True
    obj=bpy.data.objects.new("TrefoilPath",curve)
    bpy.context.collection.objects.link(obj)

    center=sum(pts,Vector())/len(pts)
    A=math.radians(ampl); phi0=math.radians(phase)

    U = Vector((0,0,1))     # initial parallel-transport frame
    T_prev = None

    for i,p in enumerate(s.points):
        P = Vector(p.co[:3])
        Pn = Vector(s.points[(i+1)%len(s.points)].co[:3])
        T = (Pn-P).normalized()

        # --- Parallel transport frame (Bishop frame) ---
        if T_prev is not None:
            v = (T_prev + T)
            if v.length > 1e-6:
                U -= 2 * (U.dot(v) / v.dot(v)) * v
                U.normalize()
        T_prev = T

        # radial inward direction
        R = (center - P)
        R -= R.dot(T)*T
        R.normalize()

        # base orientation from twist-free frame
       # Compute vector pointing toward global Z, orthogonalized to the tangent
        Z = Vector((0, 0, 1))
        N = Z - Z.dot(T) * T  # projection of Z onto the normal plane of T
        if N.length < 1e-6:
            N = Vector((1, 0, 0))  # fallback for vertical tangent
        else:
            N.normalize()

        # Use a fixed frame for comparison
        ref = T.cross(N).normalized()
        tilt = math.atan2(ref.dot(Vector((0, 1, 0))), ref.dot(Vector((1, 0, 0))))



        # arc-length parameter
        s_param = i/(len(s.points)-1)

        # ONE single global oscillation
        osc = A * math.sin(2*math.pi*s_param + phi0)

        # true filament helicity
        circ = CIRC_GAIN * (2*math.pi*CIRC_TURNS*s_param + math.radians(CIRC_OFFSET_DEG))

        p.tilt = tilt  + osc + circ



    pc=bpy.data.curves.new("Airfoil","CURVE")
    pc.dimensions='2D'
    sp=pc.splines.new("POLY")
    pts2=airfoil(); sp.points.add(len(pts2)-1)
    for i,(x,y) in enumerate(pts2):
        sp.points[i].co=((x-0.5)*CHORD,y*CHORD,0,1)
    sp.use_cyclic_u=True
    prof=bpy.data.objects.new("Airfoil",pc)
    bpy.context.collection.objects.link(prof)

    curve.bevel_mode='OBJECT'; curve.bevel_object=prof; curve.fill_mode='FULL'
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    bpy.ops.object.convert(target='MESH')
    solid=bpy.context.object
    # Rename mesh object + mesh datablock so exports are clean
    solid_name = f"{NAME_PREFIX}_{idx:03d}"
    solid.name = solid_name
    solid.data.name = solid_name + "_mesh"

    solid.location=(gx,gy,0)
    solid.data.materials.clear()
    solid.data.materials.append(mat_bottom)
    solid.data.materials.append(mat_top)
    solid.data.materials.append(mat_stripe)  # 2

    # paint a stripe on sharp features (trailing-edge-ish) to visualize twist
    bm = bmesh.new()
    bm.from_mesh(solid.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    thr = math.radians(50.0)  # adjust 40..70
    for e in bm.edges:
        if len(e.link_faces) == 2:
            ang = e.link_faces[0].normal.angle(e.link_faces[1].normal)
            if ang > thr:
                e.link_faces[0].material_index = 2
                e.link_faces[1].material_index = 2

    bm.to_mesh(solid.data)
    bm.free()

    bpy.data.objects.remove(prof,do_unlink=True)
    return solid

#    # label
#    bpy.ops.object.text_add(location=(gx,gy,-35))
#    t=bpy.context.object
#    t.data.body=f"{idx}\nP={phase}\nA={ampl}"
#    t.scale=(6,6,6)

#    codex[f"T{idx:03d}"]={"phase":phase,"ampl":ampl,"chord":CHORD,"thickness":THICKNESS,"circ":CIRC_TURNS,"date":today}

# ============================================================
# RUN GRID
# ============================================================
solids = []
idx = 0
for iy, a in enumerate(AMPLS):
    for ix, p in enumerate(PHASES):
        s = make_variant(p, a, (ix-2.5)*GRID_SPACING, (2.5-iy)*GRID_SPACING, idx)
        if s:
            solids.append(s)
        idx += 1

with open(CODEX, "w") as f:
    json.dump(codex, f, indent=2)

print("Trefoil Hydrofoil Laboratory built.")
print(f"RUN_ID = {RUN_ID}")


# ============================================================
# EXPORT (unique filenames with P/Q + RUN_ID)
# ============================================================
out_dir = os.path.expanduser("~/3d-mesh/trefoil_exports")
os.makedirs(out_dir, exist_ok=True)

# Export ONE STL per object
for obj in solids:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    stl_path = os.path.join(out_dir, f"{obj.name}.stl")
    export_stl_selected(stl_path)
    print(f"✅ Exported: {stl_path}")

