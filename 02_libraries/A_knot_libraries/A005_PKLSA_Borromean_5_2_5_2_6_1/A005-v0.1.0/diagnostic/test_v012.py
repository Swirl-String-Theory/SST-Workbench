from pathlib import Path
import sys,json,hashlib,numpy as np
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'src'))
import legacy_build as l
b0=(HERE/'geometry/borromean_5_2_5_2_6_1_SMOKE.kpt').read_bytes()
b2=(HERE/'geometry/borromean_5_2_5_2_6_1_SMOKE_SCALE2.kpt').read_bytes()
p0=l.decode_kpt(b0);p2=l.decode_kpt(b2)
assert all(np.array_equal(2*a,b) for a,b in zip(p0,p2))
assert len(p0)==3 and all(len(a)==307 for a in p0)
assert hashlib.sha256(b0).hexdigest()==json.loads((HERE/'candidate_report_SMOKE.json').read_text())['geometries_sha256']
for name in ['01_original_LOAD_BASELINE','02_original_GO1','03_original_SNAPSHOT_AFTER1','11_scale2_LOAD_BASELINE','12_scale2_GO1','13_scale2_SNAPSHOT_AFTER1']:
 assert (HERE/'diagnostic'/f'{name}.kpc').exists()
assert 'go 1' not in (HERE/'diagnostic/01_original_LOAD_BASELINE.kpc').read_text()
assert 'go 1' not in (HERE/'diagnostic/03_original_SNAPSHOT_AFTER1.kpc').read_text()
assert 'go 1' not in (HERE/'diagnostic/11_scale2_LOAD_BASELINE.kpc').read_text()
assert 'go 1' not in (HERE/'diagnostic/13_scale2_SNAPSHOT_AFTER1.kpc').read_text()
assert (HERE/'source_native/5_2__knotplot_final.txt').exists()
assert (HERE/'source_native/6_1__knotplot_final.txt').exists()
print('v0.1.2 offline instrumentation checks: PASS (KnotPlot runtime not tested)')
