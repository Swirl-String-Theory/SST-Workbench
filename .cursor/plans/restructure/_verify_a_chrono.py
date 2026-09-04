import csv
import json
import re
from pathlib import Path

md = Path(".cursor/plans/restructure/CATALOG_v0.1.md").read_text(encoding="utf-8")
part = md.split("## A_falsifiers")[1].split("## B_closures")[0]
rows = re.findall(r"\| (A\d+) \| `([^`]+)` \|", part)
print("CATALOG A count", len(rows))
for i in (0, 4, 5, 41):
    print(" ", rows[i])

d = json.loads(
    Path(".cursor/plans/restructure/SST_WORKBENCH_RESTRUCTURE_MAP_v0.1.json").read_text(
        encoding="utf-8"
    )
)
ja = [(e["catalog_id"], e["slug"]) for e in d["research_catalog"]["A_falsifiers"]]
print("JSON A count", len(ja))
assert ja[0] == ("A001", "route_a_parallel_derivation_falsification")
assert ja[4] == ("A005", "finite_core_c2")
assert ja[5] == ("A006", "contact_billiard_hydrodynamic")
assert ja[-1] == ("A042", "quantum_galileo_action_gauge_closure")

# Compare to user table
user = {r[0]: r[1] for r in rows}
for cid, slug in ja:
    assert user[cid] == slug, (cid, user[cid], slug)
print("CATALOG == JSON for all A IDs")

pm = list(csv.DictReader(open("10_docs/migration/path_map.csv", encoding="utf-8")))
checks = {
    "SST_contact_billiard_hydrodynamic_falsifier": ("A006", "A006_contact"),
    "SST_Quantum_Galileo_Action_Gauge_Closure": ("A042", "A042_quantum"),
    "SST_ideal_links": ("A007", "A007_ideal"),
    "SST_dark_knot_rayleigh_research": ("A003", "A003_dark"),
    "SST_minimal_falsification_harness": ("D004", "D004_minimal"),
    "SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier": ("A038", "A038_trefoil"),
}
for old, (cid, frag) in checks.items():
    hits = [r for r in pm if r["old_path"] == old or r["old_path"].startswith(old)]
    assert hits, old
    r = hits[0]
    assert r["catalog_id"] == cid, (old, r["catalog_id"], cid)
    assert frag in r["new_path"], (old, r["new_path"])
    print("path_map OK", old, "->", r["catalog_id"])

# totals line
assert "| `01_research/A_falsifiers` | 42 |" in md
print("totals OK")
