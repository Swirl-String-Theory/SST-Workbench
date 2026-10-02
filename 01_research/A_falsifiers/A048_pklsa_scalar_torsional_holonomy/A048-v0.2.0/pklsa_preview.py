from pathlib import Path
import argparse,json
from sst_torsion.pklsa import geometry_screen
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--non-strict-hash',action='store_true'); ap.add_argument('--out',default='pklsa_geometry_preview.json')
    a=ap.parse_args(); r=geometry_screen(a.root,strict_hash=not a.non_strict_hash); Path(a.out).write_text(json.dumps(r,indent=2),encoding='utf-8'); print(json.dumps({'count':r['count'],'bundle_sha256':r['bundle_sha256'],'out':a.out},indent=2))
