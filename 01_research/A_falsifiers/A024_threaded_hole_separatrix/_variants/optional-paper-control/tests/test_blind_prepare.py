from pathlib import Path
import json,csv
from sst_threaded_hole_falsifier.prepare import prepare
ROOT=Path(__file__).resolve().parents[1]

def test_prepare_hides_identity(tmp_path):
    cfg=json.loads((ROOT/'config/preset_basic.json').read_text(encoding='utf-8'));cfg['carrier_ids']=['TORUS_T2_3'];cfg['beta_values']=[.5];cfg['n_threads_values']=[1];cfg['pressure_enabled']=False
    cp=tmp_path/'c.json';cp.write_text(json.dumps(cfg), encoding='utf-8');m=prepare(ROOT,tmp_path/'campaign',cp);pub=tmp_path/'campaign/blind_catalog';raw=(pub/'pairs_public.csv').read_text(encoding='utf-8').lower();assert 'torus' not in raw and 'active' not in raw and 'null' not in raw and m['n_pairs']==1
    z=__import__('numpy').load(next((pub/'geometry').glob('*.npz')));assert 'n_carrier_components' in z and 'gammas' in z
