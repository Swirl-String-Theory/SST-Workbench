import json
from pathlib import Path

d = json.loads(
    Path(
        ".cursor/plans/restructure/SST_WORKBENCH_RESTRUCTURE_MAP_v0.1.legacy_draft.json"
    ).read_text(encoding="utf-8")
)
for e in d["research_catalog"]["A_falsifiers"]:
    src = (e.get("source_paths") or [None])[0]
    print(e["catalog_id"], e["slug"], e.get("catalog_created_tree"), src)

print("count", len(d["research_catalog"]["A_falsifiers"]))
print("a005", d.get("naming_policy", {}).get("a005_policy"))
