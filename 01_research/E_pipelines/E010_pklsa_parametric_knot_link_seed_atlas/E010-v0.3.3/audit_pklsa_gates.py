
import json
import sys
from pathlib import Path
from collections import Counter

root = Path(sys.argv[1])
failed = json.loads(
    (root / "FAILED_TOPOLOGIES.json").read_text(encoding="utf-8")
)

gate_counts = Counter()
missing = []

for item in failed:
    topology = item["topology_id"]
    path = root / "atlas" / topology / "qualification" / "geometry_metrics.json"

    if not path.is_file():
        missing.append(topology)
        continue

    data = json.loads(path.read_text(encoding="utf-8"))

    for carrier in data.get("carriers", []):
        if carrier.get("literature_hard_gate_pass") is not False:
            continue

        catalog = carrier.get("catalog_id", "UNKNOWN")
        for gate, status in carrier.get("literature_gate_status", {}).items():
            if gate.startswith("G") and status != "PASS":
                gate_counts[(catalog, gate, status)] += 1

print("Carrier-gate failures:")
for (catalog, gate, status), count in gate_counts.most_common():
    print(f"{catalog:8} {gate:42} {status:16} {count}")

print(f"Missing geometry indexes: {len(missing)}")
if missing:
    print("Examples:", missing[:20])