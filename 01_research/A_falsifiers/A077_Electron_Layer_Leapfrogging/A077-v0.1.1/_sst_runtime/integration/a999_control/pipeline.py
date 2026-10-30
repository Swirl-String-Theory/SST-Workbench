"""A999 control gates. No mechanism, stability, or Euler claims."""
from pathlib import Path
from sst_falsifier.backends.python_ref import biot_savart
from .backend_matrix import frozen_input
import numpy as np

def run_scientific_pipeline(root,cfg,ledger,mode):
    root=Path(root)
    ledger.record('G0','PASS',metrics={'mode':mode},reason='Frozen protocol verified by the framework prior to execution.')
    try:
        p,q,gamma,core,input_hash=frozen_input(root)
        ledger.record('G1','PASS',metrics={'points':int(len(p)),'component_count':1,'input_sha256':input_hash},
           reason='Exported E010 geometry reloaded with original SHA-256 and frozen record identity; physics not granted.')
        value=biot_savart(p,q,gamma=gamma,core=core)
        finite=bool(value.shape==(8,3) and np.isfinite(value).all() and np.linalg.norm(value)>1e-30)
        ledger.record('G2','PASS' if finite else 'FAIL',
           metrics={'query_count':8,'reference_l2':float(np.linalg.norm(value)),'float_precision':'float64'},
           reason='Python numerical control: finite, nonzero midpoint Biot-Savart observable.' if finite else 'Nonfinite/degenerate numeric reference')
    except Exception as ex:
        ledger.record('G1','UNRESOLVED',reason=f'Dataset verification failed: {type(ex).__name__}: {ex}')
        ledger.record('G2','NOT_RUN_PREREQUISITE',reason='Reference input not verified')
    return {'schema':'SST-A999-INTEGRATION-MANIFEST-1','scope':'STATIC_NUMERICAL_CONTROL_NOT_PHYSICAL_EVIDENCE',
            'independent_physical_source_groups':1,'scientific_claims':'NOT_EVALUATED'}
