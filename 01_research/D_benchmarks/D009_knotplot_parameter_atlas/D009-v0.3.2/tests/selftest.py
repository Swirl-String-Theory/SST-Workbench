from pathlib import Path
import json,re,sys,subprocess
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/"parameter_manifest.json").read_text())
subprocess.run([sys.executable,str(ROOT/"generate_kpc.py")],check=True,cwd=str(ROOT))
n=sum(len(f["values"]) for f in D["families"])
for stage in ("probe","extended"):
    fs=list((ROOT/"kpc"/stage).glob("*.kpc"))
    assert len(fs)==n,(stage,len(fs),n)
    for f in fs:
        txt=f.read_text()
        assert "load 3.1" in txt
        assert "refine nbeads 300" in txt
        assert "__BUNDLE_ROOT__" in txt
        family=f.stem.split("__",1)[0]
        # exactly one swept assignment after explicit baseline/context; presence is enough
        assert re.search(rf"(?m)^\s*{re.escape(family)}\s*=\s*",txt),(f,family)
        assert "timeincr" not in txt
# Critical runtime names/defaults
assert D["baseline"]["charge"]==15
assert D["baseline"]["hooke"]==1
assert D["baseline"]["power"]==5
assert D["baseline"]["tinc"]==15
assert any(f["name"]=="tinc" for f in D["families"])
assert not any(f["name"]=="timeincr" for f in D["families"])
print(f"SELFTEST PASS: {len(D['families'])} families, {n} candidates/stage, correct `tinc` runtime parameter, explicit baseline")


# Packaging regression: runtime directories must be recreated even if omitted
# from a ZIP because they were empty.
for p in (
    ROOT/"out"/"probe", ROOT/"out"/"extended",
    ROOT/"logs"/"probe", ROOT/"logs"/"extended",
    ROOT/"runtime_kpc"/"probe", ROOT/"runtime_kpc"/"extended",
    ROOT/"analysis", ROOT/"archive",
):
    assert p.is_dir(), p
    q=p/".selftest_write.tmp"
    q.write_text("ok\n")
    assert q.is_file() and q.stat().st_size>0
    q.unlink()

print("FILESYSTEM BOOTSTRAP REGRESSION PASS")
