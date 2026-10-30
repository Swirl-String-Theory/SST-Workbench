"""Offline verification entry point shipped INSIDE the portable output ZIP."""
from pathlib import Path
import argparse, json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sst_pklsa.combined_atlas import CombinedSeedAtlas, need, sha, verify_file_manifest

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--all-geometries',action='store_true');args=ap.parse_args()
    count=verify_file_manifest(args.root);atlas=CombinedSeedAtlas(args.root)
    need(len(atlas.list_ids(include_research=True))==11757,'Combined count')
    need(len(atlas.list_ids())==4497,'Research selection isolation')
    representatives={}
    for identity in atlas.list_ids(include_research=True):
        r=atlas.describe(identity)
        key=(r['collection'],r.get('variant'),r['component_count'],r.get('carrier',{}).get('representation'))
        representatives.setdefault(key,identity)
    ids=atlas.list_ids(include_research=True) if args.all_geometries else list(representatives.values())
    for identity in ids:atlas.load(identity,allow_research=True)
    print(json.dumps({'status':'PASS_PORTABLE_ATLAS','manifest_files':count,'record_count':11757,
                     'loaded_geometries':len(ids),'index_sha256':sha(args.root/'COMBINED_INDEX.json'),
                     'scientific':'NOT_RUN'}))

if __name__=='__main__':main()
