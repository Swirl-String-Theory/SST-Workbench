from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from helmholtz_sst.io import sha256_file,atomic_json
from helmholtz_sst.reveal import physical_secondary

def main():
    ap=argparse.ArgumentParser();ap.add_argument('frozen_result',type=Path);a=ap.parse_args();fp=a.frozen_result;side=fp.with_suffix(fp.suffix+'.sha256')
    if not side.exists():raise SystemExit('Refusing reveal: missing frozen_result.json.sha256')
    recorded=side.read_text().split()[0];actual=sha256_file(fp)
    if recorded!=actual:raise SystemExit('Refusing reveal: frozen result hash mismatch')
    result=json.loads(fp.read_text());mpath=fp.parent/'private/reveal_map.json'
    if not mpath.exists():raise SystemExit('Refusing reveal: missing private/reveal_map.json')
    mapping={x['blind_id']:x for x in json.loads(mpath.read_text())['mapping']};rows=[];revealed=[]
    for s in result['samples']:
        m=mapping.get(s['blind_id'],{});sec=physical_secondary(s);r={'blind_id':s['blind_id'],'filename':m.get('filename','?'),'overall_status':s['overall_status'],'H3_RE_normal_nrmse':s['diagnostics']['relative_equilibrium']['normal_nrmse'],'G_H_over_r_c_secondary':sec['G_H_over_r_c_secondary'],'bulk_Helmholtz_energy_using_rho_f_J':sec['bulk_Helmholtz_energy_using_rho_f_J'],'conditional_energy_using_rho_core_J':sec['conditional_energy_using_rho_core_J'],'torsion_impedance_lemma_status':sec['torsion_impedance_lemma_status']};rows.append(r);revealed.append({'identity':m,'blind_sample':s,'secondary_physical_interpretation':sec})
    out={'frozen_result_sha256':actual,'protocol':result['protocol'],'revealed_samples':revealed};atomic_json(fp.parent/'revealed_result.json',out)
    if rows:
        with (fp.parent/'revealed_summary.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(rows,indent=2));print('Wrote',fp.parent/'revealed_result.json');return 0
if __name__=='__main__':raise SystemExit(main())
