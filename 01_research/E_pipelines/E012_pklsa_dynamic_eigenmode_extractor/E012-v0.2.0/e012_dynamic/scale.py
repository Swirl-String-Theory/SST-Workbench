from __future__ import annotations
import json, math
from pathlib import Path
from .util import centered_slopes

def load_scale_contract(path: Path | None):
    if path is None or not Path(path).exists(): return None
    return json.loads(Path(path).read_text(encoding='utf-8'))

def validate_scale_contract(contract, mode_ids):
    reasons=[]
    if not contract: return False,['NO_PHYSICAL_SCALE_CONTRACT']
    if not bool(contract.get('approved',False)): reasons.append('CONTRACT_NOT_APPROVED')
    if not bool(contract.get('derived_without_GRB_target_fit',False)): reasons.append('GRB_TARGET_INDEPENDENCE_NOT_ASSERTED')
    D=contract.get('D_m'); G=contract.get('Gamma_m2_s')
    if not isinstance(D,(int,float)) or D<=0: reasons.append('D_M_MISSING_OR_NONPOSITIVE')
    if not isinstance(G,(int,float)) or G==0: reasons.append('GAMMA_M2_S_MISSING_OR_ZERO')
    energy={}
    for row in contract.get('energy_mapping',[]):
        if isinstance(row,dict) and isinstance(row.get('mode_m'),int): energy[row['mode_m']]=row.get('energy_TeV')
    for m in mode_ids:
        E=energy.get(m)
        if not isinstance(E,(int,float)) or E<=0: reasons.append(f'ENERGY_MAPPING_MISSING_FOR_MODE_{m}')
    return len(reasons)==0,reasons

def make_physical_candidate(branch,contract):
    mode_ids=[int(r['mode_m']) for r in branch.get('samples',[])]
    ok,reasons=validate_scale_contract(contract,mode_ids)
    if not ok: return None,reasons
    D=float(contract['D_m']); G=float(contract['Gamma_m2_s']); omega_scale=abs(G)/(4*math.pi*D*D)
    energy={int(r['mode_m']):float(r['energy_TeV']) for r in contract['energy_mapping']}
    k=[]; omega=[]; energies=[]
    for r in branch['samples']:
        m=int(r['mode_m']); k.append(float(r['kD'])/D); omega.append(float(r['omega_hat'])*omega_scale); energies.append(energy[m])
    return {
      'candidate_id':'E012_PKLSA_DYNAMIC_EIGENBRANCH_v0.2.0',
      'derived_without_GRB_target_fit':True,
      'dynamical_generator':'C006-v0.3.0 regularized Biot-Savart projected temporal Jacobian; E012-v0.2.0 cross-provider and RPO-conditioned qualification.',
      'mode_identity':'Fine-anchored positive-frequency Kelvin branch tracked across resolution by eigenvalue distance plus complex eigenvector overlap; consensus across independent E011 provider anchors.',
      'convergence_evidence':'E012-v0.2.0 GATES.json, PROVIDER_DYNAMIC_BRANCHES.json, CROSS_PROVIDER_AGREEMENT.json and RPO_CONDITIONING.json.',
      'propagation_branch_metadata':'Cross-provider dimensionless Kelvin eigenbranch with same-generator RPO qualification. RPO conditioning is not a true Floquet/monodromy claim.',
      'birefringent':bool(contract.get('birefringent',False)),
      'c_reference_m_s':float(contract.get('c_reference_m_s',299792458.0)),
      'k':k,'omega':omega,'energy_TeV':energies,
      'physical_scale':{'D_m':D,'Gamma_m2_s':G,'omega_scale_s_inv':omega_scale,'scale_provenance':contract.get('scale_provenance')},
      'dimensionless_group_slopes':centered_slopes([float(r['kD']) for r in branch['samples']],[float(r['omega_hat']) for r in branch['samples']])
    },[]
