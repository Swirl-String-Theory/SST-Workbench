"""Non-optimistic scientific assessment of an already executed G2 coupled pilot."""
import csv,hashlib,json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'Gate2_Coupled_Trefoil_Grid_v0.1.0-outputs'

def main():
    records=[];missing=[]
    for name in ['T_2_3_B1600_N512','T_3_2_B1600_N512']:
        for n in (32,48,64):
            file=OUT/f'{name}_n{n}.json'
            if not file.exists():missing.append(str(file));continue
            r=json.loads(file.read_text())
            a=r['case_results'];p=r['geometry']['trefoil_seed_diagnostics'];q=r['geometry']['background_seed_diagnostics'];comp=r['comparison']
            records.append({'source':name,'n':n,'L0':r['geometry']['L0_source_polyline'],
              'knot_spectral_filter_correction':p['spectral_projection_correction_ratio'],
              'background_spectral_filter_correction':q['spectral_projection_correction_ratio'],
              'knot_relative_resid_free':a['free_knot']['initial']['component_residuals'][0]['relative_to_induced_rms'],
              'knot_relative_resid_coupled':a['coupled']['initial']['component_residuals'][0]['relative_to_induced_rms'],
              'knot_Rstar_free':comp['knot_Rstar_free'],'knot_Rstar_coupled':comp['knot_Rstar_coupled'],
              'background_Rstar_alone':comp['background_Rstar_alone'],'background_Rstar_coupled':comp['background_Rstar_coupled'],
              'momentum_Rstar_coupled':a['coupled']['initial']['momentum_projected_R_star'],
              'divergence_Dstar_max':a['coupled']['initial']['max_D_star'],
              'induced_background_on_knot':r['mutual_induction']['rms_background_velocity_weighted_on_trefoil'],
              'induced_knot_on_background':r['mutual_induction']['rms_knot_velocity_weighted_on_background'],
              'knot_background_vorticity_overlap_ratio':r['mutual_induction']['vorticity_overlap_cauchy_ratio'],
              'direct_cross_rhs_knot_from_background_rms':r['mutual_induction']['direct_cross_rhs_knot_from_background_rms'],
              'direct_cross_rhs_background_from_knot_rms':r['mutual_induction']['direct_cross_rhs_background_from_knot_rms']})
    csvp=OUT/'spatial_holdout.csv'
    if records:
        with csvp.open('w',newline='') as f:
            w=csv.DictWriter(f,records[0].keys());w.writeheader();w.writerows(records)
    # Temporal comparison of fixed seed + fixed physical final time.
    temporal={'executed':False}
    f=OUT/'T_2_3_B1600_N512_n48.json';q=OUT/'time_refinement'/'T_2_3_B1600_N512_n48.json'
    if f.is_file() and q.is_file():
        a=json.loads(f.read_text());b=json.loads(q.read_text())
        assert abs(a['config']['dt']*a['config']['steps']-b['config']['dt']*b['config']['steps'])<1e-12
        temporal={'executed':True,'mesh_n':48,'common_T':a['config']['dt']*a['config']['steps'],
            'dt_first':a['config']['dt'],'dt_second':b['config']['dt'],'results':{}}
        for name in ('free_knot','coupled','background_only'):
            p=a['case_results'][name]['final'];v=b['case_results'][name]['final']
            temporal['results'][name]={'energy_abs_diff':abs(p['energy']-v['energy']),
               'helicity_abs_diff':abs(p['helicity']-v['helicity']),
               'Rstar_abs_diff':abs(p['max_R_star']-v['max_R_star'])}
    sens={}
    for name,sub in [('negative','negative'),('strong_positive','strong_positive')]:
        q=OUT/'circulation_sensitivity'/sub/'T_2_3_B1600_N512_n32.json'
        if q.exists():
            a=json.loads(q.read_text());sens[name]={'gamma_bg':a['config']['gamma_bg'],
                 'knot_Rstar_coupled':a['comparison']['knot_Rstar_coupled'],
                 'background_Rstar_coupled':a['comparison']['background_Rstar_coupled']}
    fine=[r for r in records if r['n']==64]
    checks={
       'source_provenance':len(records)==6 and not missing,
       'spectral_seed_divergence':len(records)==6 and all(r['divergence_Dstar_max']<1e-8 for r in records),
       'spectral_filter_correction_fine_below_2pct':len(fine)==2 and all(max(r['knot_spectral_filter_correction'],r['background_spectral_filter_correction'])<.02 for r in fine),
       'background_backreaction_resolved_as_a_signal':len(fine)==2 and all(r['direct_cross_rhs_background_from_knot_rms']>1e-4 and r['direct_cross_rhs_knot_from_background_rms']>1e-4 for r in fine),
       'time_refinement_fixed_final_time':temporal['executed'] and temporal['results']['coupled']['Rstar_abs_diff']<1e-5,
       'nontrivial_joint_relative_equilibrium':False,
       'continuum_zero_residual_shown':False,
       'material_topology_numerically_certified':False,
       'infinite_or_large_grid_tested':False,
    }
    assessed={'status':'G2_COUPLED_UNRESOLVED_NO_JOINT_EULER_EQUILIBRIUM',
      'what_is_actually_tested':'finite-core Gaussian mollification of embedded closed polygonal centerlines, periodic Euler spectral short-time pilot, full two-way coupling',
      'what_is_not_tested':'unbounded free-space dynamics, exactly compact-supported core, nonlinear relative equilibrium continuation, intrinsic stability, 3/9/25-core grids',
      'checks':checks,'temporal':temporal,'circulation_sensitivity':sens,'missing':missing,
      'interpretation':['Raw Fourier coefficients are solenoidal by a closed-polygon line-integral identity.',
         'Bandlimited projection preserves solenoidality but alters finite-resolution seed; compare corrections.',
         'Separately optimized background-alone Rstar versus jointly optimized Rstar use different translation speeds; this difference is NOT a causal measure of backreaction. Use direct cross RHS terms instead.',
         'Rstar does not converge to zero with refinement and is large.',
         'Only common z-translation was fitted; a rotating relative equilibrium is not a continuous symmetry of cubic periodic boundaries.',
         'Gaussian vortex cores have tails and are not compact support; no certified material flux-surface topology from discretized Euler.',
         'Fixed background is deliberately non-Euler and only a causal diagnostic.',
         'Spatial and temporal tests operate at different scales and do not establish physical stability.']}
    (OUT/'G2_ASSESSMENT.json').write_text(json.dumps(assessed,indent=2)+'\n')
    print('Status:',assessed['status'],'records',len(records),'checks:',checks)
    return assessed

if __name__=='__main__':main()
