#!/usr/bin/env python3
"""Corrected Route A--D Planck-route audit.

This script verifies that the four trial candidates A--D reduce to one
algebraic seed relation and quantifies the look-elsewhere freedom of the
low-complexity scan. It is a diagnostic, not a derivation.
"""
import math, json, csv, argparse

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--json', default='route_ABCD_equivalence_audit.json')
    ap.add_argument('--top-csv', default='route_ABCD_look_elsewhere_top25.csv')
    args=ap.parse_args()
    C=299792458.0; HBAR=1.054571817e-34; G_REF=6.67430e-11
    M_E=9.1093837015e-31; V=1.09384563e6; R_C=1.40897017e-15
    RHO_F=7.0e-7; RHO_CORE=3.8934358266918687e18; F_SWIRL=29.053507
    alpha=2*V/C
    A=(16/math.pi**2)*(RHO_CORE/RHO_F)*(C/V)**6/R_C**2
    B=2*R_C**2*A
    Croute=(math.pi**2/32)*(RHO_F/RHO_CORE)*(V/C)**5*(V**2*R_C/M_E)
    D=C**4/(4*Croute)
    Gseed=(math.pi**3/16)*RHO_F*V**9*R_C**4/(M_E**2*C**7)
    Gseed_alpha=(math.pi**3/(2**17))*alpha**13*RHO_F*HBAR**4/(M_E**6*C**2)
    t_ref=math.sqrt(HBAR*G_REF/C**5); t_seed=math.sqrt(HBAR*Croute/C**5)
    rho_exact=G_REF*16*M_E**2*C**7/(math.pi**3*V**9*R_C**4)
    alpha_shift=(G_REF/Croute)**(1/13)-1
    G0=V**2*R_C/M_E; dr=RHO_F/RHO_CORE; beta=V/C
    rows=[]
    for k in range(-3,4):
      for n in range(-20,21):
        for p in range(-8,9):
          for m in range(-12,13):
            val=G0*(dr**k)*(beta**n)*(math.pi**p)*(2.0**m)
            ratio=val/G_REF; rel=ratio-1
            rows.append({'abs_rel_error':abs(rel),'rel_error':rel,'ratio':ratio,'G_value':val,
                         'k_density_ratio':k,'n_v_over_c':n,'p_pi':p,'m_two':m,
                         'complexity':abs(k)+abs(n)+abs(p)+abs(m),'log_error':abs(math.log(ratio))})
    rows_sorted=sorted(rows,key=lambda r:(r['abs_rel_error'], r['complexity']))
    payload={'seed_relation':{'G_seed':Gseed,'G_route_C':Croute,'G_ref':G_REF,'G_ratio':Croute/G_REF,
                              't_seed':t_seed,'t_ref':t_ref,'t_ratio':t_seed/t_ref,
                              'G_seed_alpha_form':Gseed_alpha},
             'equivalence_checks':{'B_over_2rc2A':B/(2*R_C**2*A),
                                   'A_C_duality_2_A_hbar_GC_over_c3':2*A*HBAR*Croute/C**3,
                                   'D_over_c4_4GC':D/(C**4/(4*Croute)),
                                   'G_seed_over_G_C':Gseed/Croute,
                                   'G_seed_alpha_over_G_seed':Gseed_alpha/Gseed},
             'look_elsewhere':{'grid_points':len(rows),'within_5_percent':sum(1 for r in rows if r['abs_rel_error']<=0.05),
                               'within_0_575_percent':sum(1 for r in rows if r['abs_rel_error']<=0.00575),
                               'best_25':rows_sorted[:25]},
             'degeneracies':{'rho_f_exact':rho_exact,'rho_f_exact_ratio_to_7e_minus_7':rho_exact/RHO_F,
                             'alpha_shift_fraction':alpha_shift,'alpha_shift_percent':100*alpha_shift,
                             'dlnG_dlnalpha':13}}
    with open(args.json,'w') as f: json.dump(payload,f,indent=2)
    with open(args.top_csv,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows_sorted[0].keys()))
        w.writeheader(); w.writerows(rows_sorted[:25])
    print('Route A-D corrected audit')
    print(f'G_seed/G_N = {Croute/G_REF:.15f}')
    print(f't_seed/t_p = {t_seed/t_ref:.15f}')
    print(f'B/(2rc^2 A) = {B/(2*R_C**2*A):.15f}')
    print(f'2 A hbar G_C/c^3 = {2*A*HBAR*Croute/C**3:.15f}')
    print(f'D/[c^4/(4G_C)] = {D/(C**4/(4*Croute)):.15f}')
    print(f'look-elsewhere grid points = {len(rows)}')
    print(f'within 5% = {sum(1 for r in rows if r["abs_rel_error"]<=0.05)}')
    print(f'within 0.575% = {sum(1 for r in rows if r["abs_rel_error"]<=0.00575)}')
    print(f'rho_f required = {rho_exact:.15e} kg/m^3')
    print(f'alpha shift to absorb residual = {100*alpha_shift:.6f}%')
if __name__=='__main__': main()
