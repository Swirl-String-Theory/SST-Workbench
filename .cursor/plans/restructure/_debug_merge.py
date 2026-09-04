import json
import re
from collections import Counter
from pathlib import Path

md = Path(".cursor/plans/restructure/CATALOG_v0.1.md").read_text(encoding="utf-8")
d = json.loads(
    Path(".cursor/plans/restructure/SST_WORKBENCH_RESTRUCTURE_MAP_v0.1.json").read_text(
        encoding="utf-8"
    )
)

# Parse all table rows with backticks after ID
rows = []
current_domain = None
for line in md.splitlines():
    if re.match(r"^# 0[1-5]_", line):
        current_domain = line[2:].strip().split()[0]
    m = re.match(r"^\| ([A-F]\d{3}) \| `([^`]+)`", line)
    if m and current_domain:
        rows.append((current_domain, m.group(1), m.group(2)))

print("md rows", len(rows))
print(Counter(r[0] for r in rows))

got = []
for letter, items in d["research_catalog"].items():
    for e in items:
        got.append(("01_research", e["catalog_id"], e["slug"]))
for domain, items in d["non_research_catalog"].items():
    for e in items:
        got.append((domain, e["catalog_id"], e["slug"]))

print("got rows", len(got))
print(Counter(r[0] for r in got))

md_keys = {(dom, cid, slug) for dom, cid, slug in rows}
got_keys = {(dom, cid, slug) for dom, cid, slug in got}
print("missing", sorted(md_keys - got_keys))
print("extra", sorted(got_keys - md_keys))

# duplicates in got
c = Counter((dom, cid) for dom, cid, slug in got)
print("dup catalog ids in domain", [k for k, v in c.items() if v > 1])

print("root_plan", len(d["root_plan"]), "unique", len({r["source_root"] for r in d["root_plan"]}))
