from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parent
BLIND = ROOT.parent / "A049_Isotropic_Euler_Vortex_Shear_Modulus_Falsifier_v0.4.1-outputs" / "BLIND"
seal = BLIND / "BLIND_SEAL_SHA256.txt"
rows = []
for p in sorted(BLIND.rglob("*")):
    if p.is_file() and p.name != seal.name:
        rel = p.relative_to(BLIND).as_posix()
        rows.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel}")
seal.write_text("\n".join(rows) + "\n", encoding="utf-8")
print(f"sealed_files={len(rows)}")
print(f"seal={seal}")
