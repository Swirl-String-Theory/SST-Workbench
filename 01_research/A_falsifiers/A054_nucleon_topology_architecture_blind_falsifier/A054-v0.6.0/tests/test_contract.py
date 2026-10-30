from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_cross_contract():
 c=json.loads((ROOT/'cross_falsifier_contract.json').read_text());assert c['catalog_id']=='A054';assert c['version']=='v0.6.0';assert c['stage']==30;assert c['forbid_legacy_outputs'] is True;assert c['input_geometry_source']=='E013_COMMON_SKLSA_PROVIDER_ANCHORS'
def test_configs():
 for n in ('basic','full','certify'):
  c=json.loads((ROOT/'configs'/f'{n}.json').read_text());assert c['stationarity_max']>0;assert c['max_iterations']>0;assert c['provider_energy_cv_max']>0
  assert c['armijo_c1']>0 and 0<c['backtrack_factor']<1 and c['min_step']>0
  assert c['hessian_fd_rel_l2_max']>0 and c['max_backtracks']>=12
