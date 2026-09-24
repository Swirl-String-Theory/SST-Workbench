from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parents[1] / "SST_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.1.0-outputs" / "BLIND"
OUT.mkdir(parents=True, exist_ok=True)

cfg = ROOT / "configs" / "default.json"
manifest = {
    "stage": "prepared",
    "blind": True,
    "config": cfg.name,
    "config_sha256": hashlib.sha256(cfg.read_bytes()).hexdigest(),
    "canonical_constants_present_in_blind_config": False,
}
(OUT / "prepare_manifest.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8"
)
print(json.dumps(manifest, indent=2))
