from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "A049_Isotropic_Euler_Vortex_Shear_Modulus_Falsifier_v0.4.1-outputs"
OUT = BASE / "BLIND"

if BASE.exists():
    shutil.rmtree(BASE)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "logs").mkdir(parents=True, exist_ok=True)

cfg = ROOT / "configs" / "default.json"
source_manifest = ROOT / "MANIFEST_SHA256.txt"
manifest = {
    "catalog_id": "A049",
    "version": "v0.4.1",
    "stage": "prepared",
    "blind": True,
    "config": cfg.name,
    "config_sha256": hashlib.sha256(cfg.read_bytes()).hexdigest(),
    "source_manifest_sha256": hashlib.sha256(source_manifest.read_bytes()).hexdigest() if source_manifest.exists() else None,
    "canonical_constants_present_in_blind_config": False,
    "forbidden_blind_inputs": ["alpha", "c", "r_c", "rho_f", "v_circlearrow", "Gamma_SST", "m_p", "m_e", "m_p/m_e", "proton_electron_mass_ratio", "wave_target"],
    "output_identity": BASE.name
}
(OUT / "prepare_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
