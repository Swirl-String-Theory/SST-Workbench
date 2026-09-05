from __future__ import annotations
import argparse, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description='Print compact gate conclusions from an SST falsifier output directory.');ap.add_argument('out_dir');a=ap.parse_args();out=Path(a.out_dir)
    p=out/'final_verdict.json'
    if not p.exists(): raise SystemExit(f'Missing {p}')
    d=json.loads(p.read_text(encoding='utf-8'));print(f"Version: {d.get('version','legacy')}  Overall: {d.get('overall')}")
    # v0.4 panel
    if d.get('version')=='0.4.0' or 'blind_scores' in d:
        mapping=d.get('blind_to_source',{})
        for bid,sc in d.get('blind_scores',{}).items():
            print(f"\n{mapping.get(bid,bid)} [{bid}]: {sc.get('status')}")
            for g,v in sc.get('gates',{}).items(): print(f"  {g}: {'N/A' if v is None else ('PASS' if v else 'FAIL')}")
            m=sc.get('metrics',{}); keys=['component_count','normalized_growth','jacobian_convergence','nearest_relevant_rate','TBK_block_diagonal_growth_penalty','ringdown_max_recurrence','linking_drift_max','rpo_found','floquet_rho_non']
            for k in keys:
                if k in m: print(f"    {k}: {m[k]}")
        for fn in ('GATE_CONCLUSIONS.md','COMPARATIVE_CONCLUSIONS.md'):
            q=out/fn
            if q.exists(): print(f"\n{fn}: {q}")
        return 0
    # v0.1-v0.3
    for src,sc in d.get('unblinded_scores',{}).items():
        print(f"\n{src}: {sc.get('status')}")
        det=sc.get('gate_details',{})
        for g,v in sc.get('gates',{}).items():
            role=det.get(g,{}).get('role','legacy');conc=det.get(g,{}).get('conclusion','')
            print(f"  {g} [{role}]: {'PASS' if v else 'FAIL'}")
            if conc: print('    '+conc)
    return 0
if __name__=='__main__':raise SystemExit(main())
