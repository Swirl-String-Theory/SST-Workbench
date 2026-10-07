from pathlib import Path
import sys,numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from a056_falsifier.numeric import mittag_leffler_relax,phase_features
from a056_falsifier.models import phase_model_competition

def test_ml_exponential_limit():
    t=np.linspace(0,2,40); assert np.max(np.abs(mittag_leffler_relax(t,2,1)-np.exp(-t/2)))<1e-10

def test_phase_feature_shapes():
    phi=np.sin(np.linspace(0,1,30))[:,None]*np.cos(np.linspace(0,2*np.pi,64,endpoint=False))[None,:]
    y,s,p=phase_features(phi,1/29,2*np.pi/64,'periodic','python'); assert y.shape==s.shape==p.shape
