from __future__ import annotations
from pathlib import Path
import argparse, hashlib, importlib, json, os, shutil, sys, time

EXPECTED_NATIVE_SHA256 = "ba6f8c9fdbcaa2525a4268d597c697c9067a331a170bd63a04b4440d640b2645"
A054_REL = Path("01_research")/"A_falsifiers"/"A054_nucleon_topology_architecture_blind_falsifier"/"A054-v0.2.0-r2"
CAMPAIGN_REL = Path("A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.2.0-outputs")/"full_20261006_230912"

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20), b""):
            h.update(block)
    return h.hexdigest()

def norm(k: str) -> str:
    return "/".join(x for x in k.replace("\\","/").split("/") if x)

def find_workbench(explicit: str|None) -> Path:
    candidates=[]
    if explicit:
        candidates.append(Path(explicit))
    env=os.environ.get("SST_WORKBENCH_ROOT")
    if env:
        candidates.append(Path(env))
    for start in [Path.cwd(), Path(__file__).resolve().parent]:
        candidates.extend([start,*start.parents])
    candidates.append(Path(r"C:\workspace\projects\SST-Workbench"))
    seen=set()
    for p in candidates:
        try: q=p.resolve()
        except Exception: q=p
        if str(q).casefold() in seen: continue
        seen.add(str(q).casefold())
        # direct WB root
        if (q/A054_REL).is_dir():
            return q
        # ancestor named SST-Workbench
        if q.name.casefold()=="sst-workbench" and (q/A054_REL).is_dir():
            return q
    raise SystemExit("Could not locate SST-Workbench. Pass --workbench-root C:\\workspace\\projects\\SST-Workbench")

def verify_manifest(runner: Path, manifest: dict):
    bad=[]
    for raw,expected in (manifest.get("files") or {}).items():
        rel=norm(raw)
        if "/__pycache__/" in f"/{rel}/" or rel.endswith(".pyc"):
            continue
        p=runner/Path(*rel.split("/"))
        actual=sha256_file(p) if p.is_file() else "MISSING"
        if actual!=expected:
            bad.append({"path":rel,"expected":expected,"actual":actual})
    return bad

def import_probe(runner: Path, dest: Path):
    if sys.platform!="win32":
        return {"status":"SKIP_NON_WINDOWS"}
    sys.path.insert(0,str(runner))
    for k in list(sys.modules):
        if k=="a054_blind" or k.startswith("a054_blind."):
            del sys.modules[k]
    try:
        mod=importlib.import_module("a054_blind._native")
        actual_path=str(Path(mod.__file__).resolve())
        if Path(mod.__file__).resolve()!=dest.resolve():
            raise RuntimeError(f"Imported wrong extension: {actual_path}")
        physics=importlib.import_module("a054_blind.physics")
        backend=physics.backend_name()
        openmp=bool(getattr(mod,"openmp_enabled",False))
        return {"status":"PASS","module_file":actual_path,"backend":backend,"openmp_enabled":openmp}
    except Exception as e:
        return {"status":"FAIL","error":f"{type(e).__name__}: {e}"}
    finally:
        try: sys.path.remove(str(runner))
        except ValueError: pass

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workbench-root")
    ap.add_argument("--verify-only",action="store_true")
    args=ap.parse_args()

    wb=find_workbench(args.workbench_root)
    root=wb/A054_REL
    campaign=root/CAMPAIGN_REL
    runner=campaign/"blind_runner"
    manifest_path=runner/"RUNNER_MANIFEST.json"
    dest=runner/"a054_blind"/"_native.pyd"
    payload=Path(__file__).resolve().parent/"payload"/"_native.pyd"

    if not manifest_path.is_file():
        raise SystemExit(f"Missing {manifest_path}")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))

    expected=None
    for k,v in (manifest.get("files") or {}).items():
        if norm(k).casefold()=="a054_blind/_native.pyd":
            expected=v
            break
    if expected!=EXPECTED_NATIVE_SHA256:
        raise SystemExit(f"Unexpected sealed native hash in RUNNER_MANIFEST: {expected!r}")

    payload_hash=sha256_file(payload)
    if payload_hash!=expected:
        raise SystemExit(f"Restore payload corrupt: {payload_hash} != {expected}")

    before=sha256_file(dest) if dest.is_file() else "MISSING"
    bad_before=verify_manifest(runner,manifest)
    non_native=[x for x in bad_before if x["path"].casefold()!="a054_blind/_native.pyd"]
    if non_native:
        raise SystemExit("Refusing restore: other sealed runner files differ:\n"+json.dumps(non_native,indent=2))

    report={
        "schema":"A054-NATIVE-RUNNER-RESTORE-2",
        "workbench_root":str(wb),
        "a054_root":str(root),
        "campaign":str(campaign),
        "target":str(dest),
        "expected_native_sha256":expected,
        "before_native_sha256":before,
        "verify_only":bool(args.verify_only),
    }

    if not args.verify_only and before!=expected:
        backup=root/"A054-native-runner-backups"
        backup.mkdir(exist_ok=True)
        stamp=time.strftime("%Y%m%d_%H%M%S")
        if dest.is_file():
            b=backup/f"_native.before_restore_{stamp}_{before[:12]}.pyd"
            shutil.copy2(dest,b)
            report["backup_path"]=str(b)
        tmp=dest.with_suffix(dest.suffix+".restore_tmp")
        shutil.copy2(payload,tmp)
        if sha256_file(tmp)!=expected:
            raise SystemExit("Temporary restored payload hash check failed")
        os.replace(tmp,dest)

    after=sha256_file(dest) if dest.is_file() else "MISSING"
    bad_after=verify_manifest(runner,manifest)
    probe=import_probe(runner,dest) if after==expected and not bad_after else {"status":"NOT_RUN"}

    report.update({
        "after_native_sha256":after,
        "manifest_mismatches_after":bad_after,
        "import_probe":probe,
        "status":"PASS" if after==expected and not bad_after and probe.get("status") in {"PASS","SKIP_NON_WINDOWS"} else "FAIL"
    })

    out=root/"A054_native_runner_restore_v2_report.json"
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    print("Report:",out)
    return 0 if report["status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
