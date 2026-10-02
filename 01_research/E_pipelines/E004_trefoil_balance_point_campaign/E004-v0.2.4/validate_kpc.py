from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))
runtime=set(D["frozen_non_qhp_baseline"])|{"charge","hooke","power"}
actions={"reset","load","mode","collision","energy","save","coords","safe","dowker","lnknum","length","distance","angle","acn","centre","ago","stop"}
bad=[]
expected={"kpc_cold_overlap":3,"kpc_cold_extension":13,"kpc_continuation":16}
for folder,nexp in expected.items():
    fs=sorted((ROOT/folder).glob("*.kpc"))
    if len(fs)!=nexp:bad.append((folder,0,f"expected {nexp}, got {len(fs)}"))
    for p in fs:
        txt=p.read_text(encoding="utf-8")
        if folder=="kpc_continuation":
            pre=txt.split("ago ",1)[0]
            for x in ["fitto ","refine ","\ncentre\n"]:
                if x in pre:bad.append((p.name,0,"forbidden resume transform "+x.strip()))
            if "_i200000.k" not in pre:bad.append((p.name,0,"missing 200k source"))
        else:
            if "FROZEN_K31_i00000.txt" not in txt:bad.append((p.name,0,"missing common i0"))
            pre=txt.split("ago ",1)[0]
            if "fitto " in pre or "refine " in pre:bad.append((p.name,0,"cold-start refit/refine forbidden"))
        for ln,line in enumerate(txt.splitlines(),1):
            s=line.strip()
            if not s or s.startswith("%"):continue
            m=re.match(r"^([^=]+?)\s*=\s*(.+)$",s)
            if m:
                if m.group(1).strip() not in runtime:bad.append((p.name,ln,"unknown var "+m.group(1).strip()))
            elif s.split()[0] not in actions:bad.append((p.name,ln,"unknown cmd "+s.split()[0]))
if bad:
    print("KPC VALIDATION FAIL")
    for x in bad[:100]:print(x)
    raise SystemExit(3)
print("KPC VALIDATION PASS: 3 overlap + 13 extension + 16 continuation")
print("METRIC-NEUTRAL RESUME PREFIX PASS: 16/16")
