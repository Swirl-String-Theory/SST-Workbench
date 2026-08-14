from __future__ import annotations
import numpy as np
from .blind import gate

def evaluate(gstats,closure_ratios,thickness,edge_mean,conv,hol,req,sym,cfg):
    s=cfg['scoring'];nmin=s['H0_geometry']['min_vertices_per_component'];cmax=s['H0_geometry']['closure_edge_ratio_max'];tr=s['H0_geometry']['min_thickness_proxy_over_edge']
    g0=all(int(r['n_vertices'])>=nmin for r in gstats) and max(closure_ratios)<=cmax and np.isfinite(thickness) and thickness/max(edge_mean,1e-300)>=tr
    G0=gate('H0-GEOMETRY',g0,{'closure_edge_ratio_max_observed':max(closure_ratios),'thickness_proxy_over_edge':thickness/max(edge_mean,1e-300),'min_vertices':min(int(r['n_vertices']) for r in gstats)},'Closed-centerline/data-integrity precondition; not a time-evolution Helmholtz theorem test.')
    c1=s['H1_convergence'];g1=conv['energy_rel_diff']<=c1['energy_rel_diff_max'] and conv['re_abs_diff']<=c1['re_abs_diff_max'];G1=gate('H1-CONVERGENCE',g1,conv,'Resolution convergence of finite-core energy and relative-equilibrium residual.')
    c2=s['H2_holonomy'];valid=[r for r in hol if abs(r['nearest_integer'])>=1];err=max([r['integer_abs_error'] for r in valid],default=float('inf'));g2=len(valid)>=c2['min_valid_loops'] and err<=c2['integer_abs_error_max'];G2=gate('H2-HOLONOMY',g2,{'n_valid_loops':len(valid),'max_integer_abs_error':err},'Unit-circulation line integral around local meridians; numerical/topological consistency gate.')
    c3=s['H3_relative_equilibrium'];g3=req['normal_nrmse']<=c3['normal_nrmse_max'];G3=gate('H3-RELATIVE-EQUILIBRIUM',g3,req,'Main scientific falsifier: shape must be stationary up to rigid translation, rigid rotation, and tangential reparameterization.')
    c4=s['H4_symmetry'];g4=sym['orientation_relative_error']<=c4['orientation_relative_error_max'] and sym['mirror_relative_error']<=c4['mirror_relative_error_max'];G4=gate('H4-SYMMETRY',g4,sym,'Circulation reversal and mirror covariance audit; primarily an implementation/branch-control gate.')
    gates=[G0,G1,G2,G3,G4]
    if not g0:overall='INVALID_GEOMETRY'
    elif not g1 or not g2 or not g4:overall='INCONCLUSIVE_NUMERICS'
    elif not g3:overall='FALSIFIED_RELATIVE_EQUILIBRIUM'
    else:overall='PASS_CANDIDATE'
    return gates,overall
