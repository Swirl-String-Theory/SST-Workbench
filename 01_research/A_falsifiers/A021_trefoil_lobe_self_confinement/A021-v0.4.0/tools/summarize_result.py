from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> int:
    ap=argparse.ArgumentParser(description='Print compact gate conclusions from a completed SST trefoil campaign.')
    ap.add_argument('out_dir'); a=ap.parse_args(); out=Path(a.out_dir)
    p=out/'final_verdict.json'
    if not p.exists(): raise SystemExit(f'Missing {p}')
    d=json.loads(p.read_text(encoding='utf-8'))
    print(f"Version: {d.get('version','legacy')}  Overall: {d.get('overall')}")
    for src,sc in d.get('unblinded_scores',{}).items():
        print(f"\n{src}: {sc.get('status')}")
        det=sc.get('gate_details',{})
        for g,v in sc.get('gates',{}).items():
            role=det.get(g,{}).get('role','legacy'); conc=det.get(g,{}).get('conclusion','')
            print(f"  {g} [{role}]: {'PASS' if v else 'FAIL'}")
            if conc: print(f"    {conc}")
        m=sc.get('metrics',{})
        keys=['shape_velocity_ratio','normalized_growth','jacobian_convergence','cross_jacobian_fraction','cross_growth_improvement','nearest_pair_cross_rate','contact_cross_positive_fraction','lobe_pair_positive_fraction','dominant_cross_real_normalized','c3_sector_peak','c3_block_leakage','counterfactual_growth_difference','TBK_jacobian_convergence','TBK_min_family_participation','torsion_decouple_growth_penalty','kelvin_decouple_growth_penalty','breathing_decouple_growth_penalty','TBK_block_diagonal_growth_penalty','phase_lock_strength','phase_frequency_spread','rpo_best_recurrence','floquet_spectral_radius_excluding_neutral']
        print('  selected metrics:')
        for k in keys:
            if k in m: print(f"    {k}: {m[k]}")
    print('\nCircle nulls:')
    for bid,z in d.get('circle_nulls',{}).items(): print(f"  {bid}: pass={z.get('pass_null')} radial_mean={z.get('radial_velocity_mean')}")
    gc=out/'GATE_CONCLUSIONS.md'
    if gc.exists(): print(f"\nFull gate report: {gc}")
    return 0
if __name__=='__main__': raise SystemExit(main())
