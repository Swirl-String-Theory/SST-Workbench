import os
import math
import json
import zipfile
import numpy as np
import trimesh
import matplotlib.pyplot as plt

BASE = "/mnt/data/triple_gear_split_clickfit_kit"
OUT_DIR = "/mnt/data/triple_gear_6up_100x100"
os.makedirs(OUT_DIR, exist_ok=True)

# Compact packing solution using only the uploaded split click-fit halves.
# All connector features are oriented downward toward the build plate.
SCALE = 0.8360647135388535
PLACEMENTS = {
    "gear_1_half_A.stl": {"x": 25.66275955, "y": 53.34406852, "angle_deg": 38.12479378},
    "gear_1_half_B.stl": {"x": 34.55814058, "y": 16.45983050, "angle_deg": 250.63823218},
    "gear_2_half_A.stl": {"x": 70.69391875, "y": 4.12563634,  "angle_deg": 290.35592405},
    "gear_2_half_B.stl": {"x": 56.17238878, "y": 52.43823384, "angle_deg": 333.37292511},
    "gear_3_half_A.stl": {"x": 66.88618566, "y": 23.08684519, "angle_deg": 190.79781902},
    "gear_3_half_B.stl": {"x": 89.83364088, "y": 64.27725743, "angle_deg": 277.59719083},
}

parts = {}
for name in sorted(PLACEMENTS):
    path_in = os.path.join(BASE, name)
    mesh = trimesh.load_mesh(path_in)

    # Make every connector face downward toward the build plate.
    # In the earlier split kit, half_B parts have their socket side upward.
    if "_half_B" in name:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))

    # Sit each part on the build plate.
    mesh.apply_translation([0, 0, -mesh.bounds[0][2]])

    # Uniform scale to fit on a 100 x 100 mm bed.
    mesh.apply_scale(SCALE)

    # In-plane placement.
    angle = math.radians(PLACEMENTS[name]["angle_deg"])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(angle, [0, 0, 1]))
    mesh.apply_translation([PLACEMENTS[name]["x"], PLACEMENTS[name]["y"], 0])

    parts[name] = mesh

# Center the full arrangement on the 100 x 100 mm plate.
combined = trimesh.util.concatenate(list(parts.values()))
min_corner, max_corner = combined.bounds
dims = max_corner - min_corner
offset_xy = np.array([
    (100.0 - dims[0]) / 2.0 - min_corner[0],
    (100.0 - dims[1]) / 2.0 - min_corner[1],
    -min_corner[2],
])

for mesh in parts.values():
    mesh.apply_translation(offset_xy)

combined = trimesh.util.concatenate(list(parts.values()))
min_corner, max_corner = combined.bounds
dims = max_corner - min_corner

stl_path = os.path.join(OUT_DIR, "triple_gear_6up_compact_100x100_clickfit_down.stl")
obj_path = os.path.join(OUT_DIR, "triple_gear_6up_compact_100x100_clickfit_down.obj")
meta_path = os.path.join(OUT_DIR, "triple_gear_6up_compact_100x100_clickfit_down_metadata.json")
preview_path = os.path.join(OUT_DIR, "triple_gear_6up_compact_100x100_clickfit_down_preview.png")
zip_path = os.path.join("/mnt/data", "triple_gear_6up_compact_100x100_clickfit_down.zip")

combined.export(stl_path)
combined.export(obj_path)

meta = {
    "source": "upload-only split click-fit kit",
    "scale_uniform": SCALE,
    "build_plate_target_mm": [100.0, 100.0],
    "final_bounds_mm": {
        "min": min_corner.tolist(),
        "max": max_corner.tolist(),
        "dims": dims.tolist(),
    },
    "all_connectors_down": True,
    "note": (
        "Native triangle fidelity of the split halves was kept. "
        "No smoothing or remeshing was applied because that could change click-fit tolerances."
    ),
}
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)

# Top-view preview from projected vertices.
fig, ax = plt.subplots(figsize=(8, 8))
colors = ["#D55E00", "#0072B2", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]

for color, (name, mesh) in zip(colors, sorted(parts.items())):
    verts = mesh.vertices[:, :2]
    ax.scatter(verts[:, 0], verts[:, 1], s=0.15, color=color, alpha=0.18)
    ax.scatter([], [], color=color, label=name.replace(".stl", ""))

ax.set_title("Triple gear split kit — 6-up compact layout on 100 x 100 mm")
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_aspect("equal")
ax.grid(True, alpha=0.25)
ax.legend(fontsize=7, loc="upper right")
plt.tight_layout()
plt.savefig(preview_path, dpi=220)
plt.close(fig)

with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for fp in [stl_path, obj_path, meta_path, preview_path]:
        zf.write(fp, arcname=os.path.basename(fp))

print("Created:")
print(stl_path)
print(obj_path)
print(meta_path)
print(preview_path)
print(zip_path)
print("Final dims (mm):", dims.tolist())
