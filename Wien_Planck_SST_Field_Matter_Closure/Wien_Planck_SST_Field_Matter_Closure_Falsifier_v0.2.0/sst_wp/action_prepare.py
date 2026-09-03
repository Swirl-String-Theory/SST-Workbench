from __future__ import annotations
import argparse,json,secrets,hashlib,shutil
from pathlib import Path
from .common import read_csv,write_csv,dump_json,sha256_file
HIDDEN={'source_name','source_path','family_hint','case_index','source_sha256','geometry_sha256'}

def main():
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('--out-dir',required=True);p.add_argument('--private-dir',default='private_reveal_keys');p.add_argument('--quarantine-raw',action='store_true');a=p.parse_args()
    rows=read_csv(a.raw);out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);priv=Path(a.private_dir);priv.mkdir(parents=True,exist_ok=True)
    token=secrets.token_hex(16); carrier_map={};key=[];blind=[]
    for i,r in enumerate(rows):
        src=r.get('source_sha256') or r.get('source_name') or r.get('case_index')
        if src not in carrier_map: carrier_map[src]=f'C{len(carrier_map):04d}_{secrets.token_hex(2)}'
        oid=f'Q{i:06d}_{secrets.token_hex(3)}';key.append({'opaque_id':oid,'anon_carrier_id':carrier_map[src],**{k:r.get(k,'') for k in HIDDEN}})
        b={'opaque_id':oid,'anon_carrier_id':carrier_map[src],**{k:v for k,v in r.items() if k not in HIDDEN}};blind.append(b)
    write_csv(out/'BLIND_INPUT.csv',blind);raw_hash=sha256_file(a.raw);blind_hash=sha256_file(out/'BLIND_INPUT.csv');commit=hashlib.sha256(json.dumps(key,sort_keys=True).encode()).hexdigest();kpath=priv/f'{token}.json'
    private_raw_name='';private_campaign_name=''
    if a.quarantine_raw:
        private_raw=priv/f'{token}_raw.csv';shutil.move(str(a.raw),private_raw);private_raw_name=private_raw.name
        cp=out/'campaign_private.json'
        if cp.exists():
            pc=priv/f'{token}_campaign_private.json';shutil.move(str(cp),pc);private_campaign_name=pc.name
    dump_json(kpath,{'format':'SST-WP-PRIVATE-KEY-2.0','mapping':key,'carrier_map':carrier_map,'commitment_sha256':commit,'raw_sha256':raw_hash,'blind_sha256':blind_hash,'private_raw_name':private_raw_name,'private_campaign_name':private_campaign_name})
    dump_json(out/'BLIND_SEAL.json',{'format':'SST-WP-BLIND-SEAL-2.0','private_key_name':kpath.name,'private_key_commitment_sha256':commit,'raw_sha256':raw_hash,'blind_sha256':blind_hash,'hidden_fields':sorted(HIDDEN),'raw_quarantined':bool(a.quarantine_raw)})
    print(json.dumps({'rows':len(rows),'carriers':len(carrier_map),'blind':str(out/'BLIND_INPUT.csv'),'private_key':str(kpath),'commitment':commit,'raw_quarantined':bool(a.quarantine_raw)},indent=2))
if __name__=='__main__':main()
