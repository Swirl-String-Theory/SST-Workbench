from pathlib import Path
import json

from sst_bkm.campaign import NAME, VERSION, create_archives

ROOT = Path(__file__).resolve().parent
OUT = ROOT / f"{NAME}_{VERSION}-outputs"
required = [
    OUT / "BLIND" / "summary.json",
    OUT / "BLIND" / "run_manifest.json",
    OUT / "REVEALED" / "case_reveal_map.json",
    OUT / "REVEALED" / "e010_pklsa_v031_provenance.json",
]
missing = [str(p) for p in required if not p.is_file()]
if missing:
    raise SystemExit("Existing campaign output is incomplete; missing: " + "; ".join(missing))
archives = create_archives(ROOT, OUT, OUT / "REVEALED")
print(json.dumps({"status": "PACKED_EXISTING_OUTPUTS", "output": str(OUT), "archives": archives}, indent=2))
