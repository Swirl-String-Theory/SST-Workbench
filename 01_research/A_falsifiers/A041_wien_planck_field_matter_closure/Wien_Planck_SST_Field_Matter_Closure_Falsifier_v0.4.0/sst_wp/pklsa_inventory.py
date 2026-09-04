from __future__ import annotations
import argparse, json
from pathlib import Path
from .common import dump_json, sha256_file
from .pklsa_adapter import atlas_rows
from .blind_guard import assert_blind_code_clean

def main():
    ap=argparse.ArgumentParser();ap.add_argument('atlas_root');ap.add_argument('--out',required=True);a=ap.parse_args()
    root=Path(__file__).resolve().parents[1];assert_blind_code_clean(root)
    atlas=Path(a.atlas_root); rows=atlas_rows(atlas); fams=sorted({r['family'] for r in rows})
    bundles=sorted((atlas/'families').glob('*.npz'))
    result={
      'format':'SST-WP-PKLSA-INVENTORY-PUBLIC-4.0',
      'candidate_count':len(rows),'family_count':len(fams),'family_bundle_count':len(bundles),
      'expected_candidate_count':2352,'expected_family_count':49,
      'manifest_sha256':sha256_file(atlas/'manifests'/'CANDIDATES_FULL.csv'),
      'catalog_sha256':sha256_file(atlas/'CATALOG_49.json'),
      'all_family_bundles_present':len(bundles)==49,
      'pass':bool(len(rows)==2352 and len(fams)==49 and len(bundles)==49),
      'identity_policy':'family/candidate identities are not emitted by the falsifier inventory; only counts and source commitments are public.'
    }
    dump_json(a.out,result); print(json.dumps(result,indent=2)); raise SystemExit(0 if result['pass'] else 2)
if __name__=='__main__':main()
