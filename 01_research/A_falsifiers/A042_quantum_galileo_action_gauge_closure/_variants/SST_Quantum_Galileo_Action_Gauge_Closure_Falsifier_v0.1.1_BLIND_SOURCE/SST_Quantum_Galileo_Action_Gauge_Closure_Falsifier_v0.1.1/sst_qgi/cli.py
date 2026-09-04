from __future__ import annotations
from pathlib import Path
import argparse, json, shutil

from .dataset import collect_candidates
from .blind import prepare_blind
from .analysis import run_blind
from .reveal import reveal
from .package_outputs import package

def load_cfg(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)

    for name in ("prepare","basic","extended","reveal"):
        p=sub.add_parser(name)
        p.add_argument("--config",default="configs/basic.json")
    p=sub.add_parser("package")
    p.add_argument("--config",default="configs/basic.json")
    p=sub.add_parser("clean")
    p.add_argument("--config",default="configs/basic.json")

    args=ap.parse_args()
    root=Path.cwd()
    cfg=load_cfg(args.config)
    out=root/f"{cfg['project_name']}-outputs"

    if args.cmd=="prepare":
        if (out/"blind").exists():
            shutil.rmtree(out/"blind")
        if (root/"private").exists():
            shutil.rmtree(root/"private")
        candidates,audit=collect_candidates(cfg)
        manifest=prepare_blind(candidates,out/"blind",root/"private",audit)
        print(json.dumps({
            "format":manifest["format"],
            "n_candidates":manifest["n_candidates"],
            "n_blind_strata":manifest["n_blind_strata"],
            "private_key_commitment_sha256":manifest["private_key_commitment_sha256"],
            "source_identity_read":False,
        },indent=2))
    elif args.cmd in ("basic","extended"):
        r=run_blind(cfg,root,args.cmd)
        print(json.dumps({
            "mode":args.cmd,
            "backend":r["backend"],
            "n_candidates":r["n_candidates"],
            "blind_verdict":r["blind_verdict"],
            "source_identity_read":False,
        },indent=2))
    elif args.cmd=="reveal":
        r=reveal(root,cfg)
        print(json.dumps(r,indent=2))
    elif args.cmd=="package":
        a,b=package(root,cfg["project_name"])
        print(a)
        print(b)
    elif args.cmd=="clean":
        if out.exists(): shutil.rmtree(out)
        if (root/"private").exists(): shutil.rmtree(root/"private")
        print("cleaned")

if __name__=="__main__":
    main()
