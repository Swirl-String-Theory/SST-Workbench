from __future__ import annotations
from .constants import *

def physical_secondary(sample):
    a=sample['diagnostics']['core_radius_reference'];el=sample['diagnostics']['energy_length_reference'];L=sample['diagnostics']['length_reference']
    scale=R_C/a
    elp=el*scale;Lp=L*scale
    return {
      'scale_assumption':'dimensionless thickness_proxy/core_radius_reference is mapped to r_c; secondary only, not used in blind scoring',
      'scale_m_per_input_unit':scale,
      'physical_centerline_length_m':Lp,
      'Gamma_SST_m2_per_s':GAMMA_SST,
      'bulk_Helmholtz_energy_using_rho_f_J':RHO_F*GAMMA_SST**2*elp,
      'conditional_energy_using_rho_core_J':RHO_CORE*GAMMA_SST**2*elp,
      'G_H_over_r_c_secondary':8.0*PI*elp/R_C,
      'legacy_secondary_target_G_H_over_r_c':4.0,
      'legacy_secondary_target_abs_error':abs(8.0*PI*elp/R_C-4.0),
      'rho_f_kg_m3':RHO_F,
      'rho_core_kg_m3':RHO_CORE,
      'torsion_impedance_if_cT_equals_c_kg_m2_s':Z_TORSION_IF_C,
      'torsion_stiffness_if_cT_equals_c_Pa':K_TORSION_IF_C,
      'torsion_impedance_lemma_status':'NOT_TESTED_BY_STATIC_CENTERLINE_DATA'
    }
