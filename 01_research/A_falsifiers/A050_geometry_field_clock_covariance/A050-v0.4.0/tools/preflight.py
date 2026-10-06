from pathlib import Path
import argparse,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check_manifest(path,bad):
    if not path.exists(): return False
    man=json.loads(path.read_text(encoding='utf-8'))
    for e in man['entries']:
        p=ROOT/e['file']
        if not p.exists() or sha(p)!=e['sha256']: bad.append(e['carrier_id'])
    return True
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='config/default.json'); ap.add_argument('--seal-only',action='store_true'); a=ap.parse_args(); seal=json.loads((ROOT/'config/SEAL_v0.4.0.json').read_text(encoding='utf-8')); bad=[]
    for rel,h in seal['files'].items():
        p=ROOT/rel
        if not p.exists() or sha(p)!=h: bad.append(rel)
    cfg=json.loads((ROOT/a.config).read_text(encoding='utf-8')); parent=ROOT/cfg['mechanism_gate']['parent_v032_evidence']
    if not parent.exists(): bad.append(str(parent.relative_to(ROOT)))
    source_exists=False; fresh_exists=False
    if not a.seal_only:
        source_exists=check_manifest(ROOT/cfg['external_geometry_gate']['staged_manifest'],bad); fresh_exists=check_manifest(ROOT/cfg['mechanism_gate']['fresh_staged_manifest'],bad)
    if bad: raise SystemExit('PREFLIGHT FAIL: '+', '.join(bad))
    print(f'PREFLIGHT PASS: {len(seal["files"])} sealed files; source_manifest={source_exists}; fresh_manifest={fresh_exists}; config={a.config}')
if __name__=='__main__': main()
