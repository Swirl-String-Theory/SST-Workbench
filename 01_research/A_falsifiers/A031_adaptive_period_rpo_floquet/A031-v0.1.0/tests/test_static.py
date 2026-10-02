from pathlib import Path
import json,ast
ROOT=Path(__file__).resolve().parents[1]
ast.parse((ROOT/'rpo_falsifier.py').read_text())
C=json.loads((ROOT/'CONTRACT.json').read_text())
assert C['target_version']=='0.4.8'
s=(ROOT/'rpo_falsifier.py').read_text()
for term in ['period_pred','oscillatory_pairs','shooting_residual','floquet_multi','SPECTRAL_PENDING','return_ratio_max']:
 assert term in s,term
for fn in ['run_preflight.cmd','run_basic.cmd','run_extended.cmd','run_stochastic_branch.cmd','run_all.cmd','run_campaign.cmd','run_coarse_only.cmd','run_resume_from_refine.cmd']:
 assert (ROOT/fn).is_file(),fn
print('STATIC CONTRACT SELFTEST PASS')
