from pathlib import Path
import hashlib,json
import numpy as np
from a060_preflight.__main__ import run
from a060_preflight.mechanics import diagnostics,rank_one,balanced,rank_one_gate,landreman_field,finite_jacobian,direct_spherical_flux,gradient_flux_prediction
from a060_preflight.projection import projection_demo
ROOT=Path(__file__).resolve().parents[1]
def test_m00_sources():
 p=json.loads((ROOT/'sources/REFERENCE_HASHES.json').read_text())
 assert len(p['papers'])==4
 assert all(hashlib.sha256((ROOT/'sources/papers'/x['filename']).read_bytes()).hexdigest()==x['sha256'] for x in p['papers'])
def test_m01_euler():
 for e in (0,.2,.5):
  x=np.array([1.04,.16,.04]);f=lambda p:landreman_field(p,e);A=finite_jacobian(f,x)
  assert abs(np.trace(A))<3e-7
  assert max(abs(A@f(x)+x*np.array([1,1,4])))<2e-7
def test_m02_wedge():
 r=np.random.default_rng(20261013)
 for _ in range(100):
  A=r.normal(size=(3,3));A-=np.trace(A)/3*np.eye(3);d=diagnostics(A)
  assert d['m']-1e-10<=1-d['f']<=3*d['m']+1e-10
def test_m02_shear():
 assert abs(diagnostics(rank_one())['poisson_source'])<1e-13
 assert abs(diagnostics(balanced())['poisson_source'])<1e-13
 assert abs(diagnostics(balanced())['fluxfactor'])<1e-13
def test_m03_va_projection():
 d=projection_demo(25)
 assert d['projection_curl_error']<1e-8
 assert d['non_solenoidal_va_max']>.01
def test_m04_angular_flux():
 A=rank_one_gate()
 assert abs(direct_spherical_flux(A)-gradient_flux_prediction(A))<1e-12
def test_framework_pin():
 assert (ROOT/'.sst_framework_root').exists()
 assert (ROOT/'.sst_framework_root').read_text().strip().endswith('SST_Falsifier_Framework_v1.0.7')
