from pathlib import Path
import sys,numpy as np,json
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from a056_falsifier.numeric import mittag_leffler_relax,phase_features,phase_feature_parity,native_available
from sst_falsifier_framework.protocol import FrameworkContract
FrameworkContract('A056','A056 PKLSA SG ML','v0.2.0','source_group').validate()
t=np.linspace(0,2,40); err=float(np.max(np.abs(mittag_leffler_relax(t,2,1)-np.exp(-t/2))))
phi=np.sin(np.linspace(0,1,30))[:,None]*np.cos(np.linspace(0,2*np.pi,64,endpoint=False))[None,:]
y,s,p=phase_features(phi,1/29,2*np.pi/64,'periodic','python'); par=phase_feature_parity(phi,1/29,2*np.pi/64,'periodic')
status='PASS' if err<1e-10 and y.shape==s.shape==p.shape and (not par['available'] or par['relative_l2']<1e-10) else 'FAIL'
print(json.dumps({'status':status,'framework':'1.0.0.dev0','native_available':native_available(),'ml_exp_limit_max_abs':err,'native_parity':par},indent=2)); raise SystemExit(0 if status=='PASS' else 2)
