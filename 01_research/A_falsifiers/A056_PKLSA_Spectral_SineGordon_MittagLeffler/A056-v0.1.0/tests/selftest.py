from pathlib import Path
import sys, numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from a056_falsifier.numeric import mittag_leffler_relax, phase_features, native_available

t=np.linspace(0,2,40); exact=np.exp(-t/2); got=mittag_leffler_relax(t,2,1.0); err=float(np.max(np.abs(exact-got)))
if err>1e-10: raise SystemExit(f'ML exponential-limit failure {err}')
phi=np.sin(np.linspace(0,1,30))[:,None]*np.cos(np.linspace(0,2*np.pi,64,endpoint=False))[None,:]
y,ss,p=phase_features(phi,1/29,2*np.pi/64,'periodic','python')
if not (y.shape==ss.shape==p.shape): raise SystemExit('phase feature shape failure')
parity=None
if native_available():
    yn,sn,pn=phase_features(phi,1/29,2*np.pi/64,'periodic','native')
    parity=max(float(np.max(np.abs(yn-y))),float(np.max(np.abs(sn-ss))),float(np.max(np.abs(pn-p))))
    if parity>1e-10: raise SystemExit(f'native/python parity failure {parity}')
print({'status':'PASS','native_available':native_available(),'ml_exp_limit_max_abs':err,'feature_shape':y.shape,'native_python_max_abs':parity})
