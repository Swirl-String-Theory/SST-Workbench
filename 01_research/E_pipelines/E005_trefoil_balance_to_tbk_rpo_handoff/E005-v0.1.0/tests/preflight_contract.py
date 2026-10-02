from pathlib import Path
import json, os, shutil, subprocess, sys, tempfile

SRC=Path(__file__).resolve().parents[1]
C=json.loads((SRC/"handoff_contract.json").read_text())

def make_target(root, kind):
    t=root/("target_"+kind)
    t.mkdir(parents=True)
    if kind=="v048":
        version="0.4.8"
        req=[
            "VERSION.json","run_install.cmd","sst_blind/multitopology.py","sst_blind/io.py",
            C["v048"]["screen_config"],
            C["v048"]["spectral"]["k16"], C["v048"]["spectral"]["k24"],
            C["v048"]["spectral"]["k32"], C["v048"]["spectral"]["k48"],
            C["v048"]["spectral"]["k64"], C["v048"]["spectral"]["plan"],
            C["v048"]["full_confirm_config"], "sst_blind/spectral_extension.py",
        ]
    else:
        version="0.4.6.1"
        req=[
            "VERSION.json","run_install.cmd","sst_blind/multitopology.py","sst_blind/io.py",
            C["v046"]["full_config"],
        ]
    for rel in req:
        p=t/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        if rel=="VERSION.json":
            p.write_text(json.dumps({"version":version}),encoding="utf-8")
        else:
            p.write_text("# synthetic presence fixture\n",encoding="utf-8")
    py=t/".venv/Scripts/python.exe"
    py.parent.mkdir(parents=True,exist_ok=True)
    py.write_text("synthetic",encoding="ascii")
    return t

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    for kind in ("v048","v046"):
        target=make_target(td,kind)
        env=os.environ.copy()
        env["SST_TBK_TARGET"]=str(target)
        cp=subprocess.run(
            [sys.executable,str(SRC/"bridge.py"),"preflight","--prefer",kind],
            cwd=SRC,env=env,text=True,capture_output=True,timeout=20
        )
        print(cp.stdout,end="")
        assert cp.returncode==0, cp.stderr
print("TARGET CONTRACT PREFLIGHT SELFTEST PASS")
