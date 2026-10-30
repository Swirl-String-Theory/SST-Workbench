from pathlib import Path
import importlib.util
import json
import math
import sys
import tempfile
import subprocess
import hashlib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ruban_generator', ROOT/'generate_seed.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


def test_exact_paper_parameters():
    p=mod.exact_params()
    assert p['B0']=='0.154'
    assert p['delta']=='0.05'
    assert p['delta_squared']=='0.0025'
    assert abs(float(p['Lambda_65d'])- (1.4+0.5*math.log(200)))<1e-14
    assert abs(float(p['tilde_Lambda0_65d'])-(1.4-0.5*math.log(2)))<1e-14
    assert abs(float(p['xi_over_R0_65d'])-(math.exp(-1.4)/math.sqrt(200)))<1e-14


def test_seed_geometry_both_samplings():
    for n,mode in [(2048,'equal_arclength'),(4096,'equal_arclength'),(2048,'uniform_theta')]:
        p=mod.xyz(n,mode)
        v=mod.check(p,mode)
        assert v['toroidal_winding']==2
        assert v['poloidal_winding']==3
        assert v['max_torus_minor_radius_residual']<1e-13
        if mode=='equal_arclength': assert v['segment_ratio_max_to_min']<1.00001


def test_reference_files_unchanged_and_parseable():
    data=json.loads((ROOT/'SEED_MANIFEST.json').read_text(encoding='utf-8'))
    for x in data['files']:
        fn=ROOT/'seeds'/x['filename']
        assert hashlib.sha256(fn.read_bytes()).hexdigest()==x['sha256']
        p=np.loadtxt(fn,comments='#',usecols=(0,1,2))
        assert p.shape==(x['n_vertices'],3)
        assert np.all(np.isfinite(p))


def test_generator_reproduces_filenames_and_vertices():
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)/'seeds'
        subprocess.run([sys.executable, str(ROOT/'generate_seed.py'), '--out',str(out)], check=True, stdout=subprocess.DEVNULL)
        for x in json.loads((ROOT/'SEED_MANIFEST.json').read_text())['files']:
            fresh=np.loadtxt(out/x['filename'],comments='#',usecols=(0,1,2))
            shipped=np.loadtxt(ROOT/'seeds'/x['filename'],comments='#',usecols=(0,1,2))
            assert np.max(np.abs(fresh-shipped))<2e-15


def test_a075_loader_readonly_and_scale():
    import importlib.util
    spec=importlib.util.spec_from_file_location('ruban_loader', ROOT/'a075_seed_loader.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    out, prov=m.load_ruban_t23(ROOT, n=2048, target_outer_radius=0.82, center_z=0.65)
    assert out.shape==(2048,3)
    assert abs(np.max(np.hypot(out[:,0],out[:,1]))-.82)<1e-13
    assert abs(prov['scaled_r0']/prov['scaled_R0']-.154)<1e-14
    assert abs(prov['scaled_ruban_regularization_delta_NOT_EULER_SIGMA']-.05*prov['scale_factor'])<1e-15
