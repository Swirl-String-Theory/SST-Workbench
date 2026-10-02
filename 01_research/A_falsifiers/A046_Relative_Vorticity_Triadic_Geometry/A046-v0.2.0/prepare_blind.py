from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs"
OUT = BASE / "BLIND"

if BASE.exists():
    shutil.rmtree(BASE)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "logs").mkdir(parents=True, exist_ok=True)

cfg = ROOT / "configs" / "default.json"
source_manifest = ROOT / "MANIFEST_SHA256.txt"
manifest = {
    "catalog_id": "A046",
    "version": "v0.2.0",
    "stage": "prepared",
    "blind": True,
    "config": cfg.name,
    "config_sha256": hashlib.sha256(cfg.read_bytes()).hexdigest(),
    "source_manifest_sha256": (
        hashlib.sha256(source_manifest.read_bytes()).hexdigest()
        if source_manifest.exists() else None
    ),
    "canonical_constants_present_in_blind_config": False,
    "output_identity": BASE.name,
}
(OUT / "prepare_manifest.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8"
)
print(json.dumps(manifest, indent=2))
