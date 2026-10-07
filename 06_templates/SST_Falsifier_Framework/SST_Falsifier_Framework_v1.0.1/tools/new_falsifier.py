from __future__ import annotations
from pathlib import Path
import argparse,re,shutil,secrets

FRAMEWORK=Path(__file__).resolve().parents[1]; TEMPLATE=FRAMEWORK/"instance_template"
p=argparse.ArgumentParser(description="Create a thin SST falsifier instance using the shared framework runtime.")
p.add_argument("catalog_id"); p.add_argument("name"); p.add_argument("destination"); p.add_argument("--profile",choices=["minimal","cpu","gpu","multilibrary_gpu"],default="cpu"); p.add_argument("--version",default="v0.1.0")
a=p.parse_args()
if not re.fullmatch(r"v\d+\.\d+\.\d+",a.version): raise SystemExit("--version must look like v0.1.0")
if not re.fullmatch(r"[A-Za-z0-9_-]+",a.catalog_id): raise SystemExit("invalid catalog id")
dst=Path(a.destination)
if dst.exists(): raise SystemExit(f"destination exists: {dst}")
shutil.copytree(TEMPLATE,dst,ignore=shutil.ignore_patterns("__pycache__",".pytest_cache","*.pyc","*.pyd","*.dll","*.exe","*.lib","*.exp","build"))
repls={"__CATALOG_ID__":a.catalog_id,"__NAME__":a.name,"__VERSION__":a.version,"__PROFILE__":a.profile}
tex_repls={"@@CATALOG-ID@@":a.catalog_id,"@@FALSIFIER-NAME@@":a.name,"@@VERSION@@":a.version,"@@PROFILE@@":a.profile}
def tex_escape(v: str) -> str:
    table={"\\":r"\textbackslash{}","&":r"\&","%":r"\%","$":r"\$","#":r"\#","_":r"\_","{":r"\{","}":r"\}","~":r"\textasciitilde{}","^":r"\textasciicircum{}"}
    return "".join(table.get(ch,ch) for ch in v)
for f in dst.rglob("*"):
    if not f.is_file() or f.suffix.lower() not in {".py",".md",".json",".toml",".cmd",".tex",".txt",".cpp",".hpp",".h"}: continue
    try:t=f.read_text(encoding="utf-8")
    except Exception:continue
    active_repls=tex_repls if f.suffix.lower()==".tex" else repls
    for old,newval in active_repls.items():
        t=t.replace(old,tex_escape(newval) if f.suffix.lower()==".tex" else newval)
    f.write_text(t,encoding="utf-8",newline="\n")
private=dst/"private";private.mkdir(exist_ok=True);(private/"OPAQUE_ID_KEY.bin").write_bytes(secrets.token_bytes(32));(private/"REVEAL_NONCE.bin").write_bytes(secrets.token_bytes(32))
print(f"Created {dst}")
print(f"Profile: {a.profile}; status: UNVALIDATED")
print("Next: complete science_contract.json + FALSIFIER_REPORT.tex + source/gate contracts, implement pipeline, then FREEZE.")
