from pathlib import Path
import sys,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from a056_science.numeric import mittag_leffler_python,phase_features
from a056_science.models import phase_model_competition

def test_ml_exponential_limit():
    t=np.linspace(0,2,41); assert np.max(np.abs(mittag_leffler_python(t,2,1)-np.exp(-t/2)))<1e-12

def test_phase_feature_shapes():
    phi=np.sin(np.linspace(0,1,30))[:,None]*np.cos(np.linspace(0,2*np.pi,64,endpoint=False))[None,:]
    y,s,p=phase_features(phi,1/29,2*np.pi/64,'periodic','python'); assert y.shape==s.shape==p.shape

def test_sg_design_recovers_positive_coefficients():
    nt,ns=80,96;t=np.linspace(0,4,nt);s=np.linspace(-5,5,ns);w=.8;eta=np.sqrt(1-w*w)
    phi=4*np.arctan((eta/w)*np.sin(w*t[:,None])/np.cosh(eta*s[None,:]));dt=t[1]-t[0];ds=s[1]-s[0]
    y,ss,p=phase_features(phi,dt,ds,'open','python');sg=phase_model_competition(y,ss,p,.65)['SG'];assert sg['physical_coefficients']
