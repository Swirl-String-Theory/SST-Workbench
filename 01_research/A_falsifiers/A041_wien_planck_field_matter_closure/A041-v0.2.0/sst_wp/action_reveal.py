from __future__ import annotations
import argparse,json,hashlib,shutil,math
from pathlib import Path
from .common import load_json,dump_json,sha256_file,relerr,read_csv
from . import constants as C

def main():
    p=argparse.ArgumentParser();p.add_argument('blind_analysis');p.add_argument('seal');p.add_argument('blind_csv');p.add_argument('--private-dir',default='private_reveal_keys');p.add_argument('--out',required=True);a=p.parse_args()
    ana=load_json(a.blind_analysis);seal=load_json(a.seal);kp=Path(a.private_dir)/seal['private_key_name'];key=load_json(kp)
    commit=hashlib.sha256(json.dumps(key['mapping'],sort_keys=True).encode()).hexdigest();integrity=commit==seal['private_key_commitment_sha256']==key['commitment_sha256'] and sha256_file(a.blind_csv)==seal['blind_sha256']
    rows=read_csv(a.blind_csv);import numpy as np
    jf=[float(r['delta_E_J'])/float(r['frequency_Hz']) for r in rows if float(r['delta_E_J'])>0 and float(r['frequency_Hz'])>0]
    jw=[float(r['delta_E_J'])/float(r['omega_rad_s']) for r in rows if float(r['delta_E_J'])>0 and float(r['omega_rad_s'])>0]
    J=float(np.median(jf)) if jf else None;Jw=float(np.median(jw)) if jw else None
    eh=relerr(J,C.h) if J is not None else None;ehw=relerr(Jw,C.hbar) if Jw is not None else None
    target_ok=eh is not None and ehw is not None and eh<=0.05 and ehw<=0.05
    out={'format':'SST-WP-REVEAL-2.0','integrity_ok':integrity,'blind_pass':ana['blind_pass'],'target_comparison':{'median_positive_DeltaE_over_f_J_s':J,'h_J_s':C.h,'relative_error_to_h':eh,'median_positive_DeltaE_over_omega_J_s':Jw,'hbar_J_s':C.hbar,'relative_error_to_hbar':ehw},'final_pass':bool(integrity and ana['blind_pass'] and target_ok),'warning':'The reveal target cannot rescue a failed blind energy/discreteness/universality/convergence gate.','reveal_mapping':key['mapping']}
    outdir=Path(a.out).parent
    if key.get('private_raw_name') and (Path(a.private_dir)/key['private_raw_name']).exists(): shutil.copy2(Path(a.private_dir)/key['private_raw_name'],outdir/'REVEALED_RAW_OBSERVATIONS.csv')
    if key.get('private_campaign_name') and (Path(a.private_dir)/key['private_campaign_name']).exists(): shutil.copy2(Path(a.private_dir)/key['private_campaign_name'],outdir/'REVEALED_CAMPAIGN_PRIVATE.json')
    dump_json(a.out,out);print(json.dumps({k:v for k,v in out.items() if k!='reveal_mapping'},indent=2))
if __name__=='__main__':main()
