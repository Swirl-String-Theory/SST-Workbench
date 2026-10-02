from pathlib import Path
import argparse, json, sys

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--forbidden-file")
    a=ap.parse_args(); root=Path(a.root); out=root/"SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier_v0.1.0-outputs"/"blind"
    if not out.exists(): raise SystemExit("blind output missing")
    bad=[]
    for p in out.rglob("*"):
        if "private" in p.parts or "revealed" in p.parts:
            bad.append((str(p),"forbidden output path"))
    tokens=[]
    if a.forbidden_file and Path(a.forbidden_file).exists():
        tokens += json.loads(Path(a.forbidden_file).read_text(encoding="utf-8"))["forbidden_substrings"]
    for p in out.rglob("*"):
        if p.is_file():
            try: txt=p.read_text(encoding="utf-8")
            except UnicodeDecodeError: continue
            for t in tokens:
                if t in txt: bad.append((str(p),t))
    if bad:
        print(json.dumps({"status":"FAIL","matches":bad},indent=2)); return 2
    print(json.dumps({"status":"PASS","scanned":str(out),"token_count":len(tokens)},indent=2)); return 0
if __name__=="__main__": sys.exit(main())
