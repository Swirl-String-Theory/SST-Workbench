import hashlib
import numpy as np

def pklsa_hash(comps):
    h=hashlib.sha256(); h.update(b'PKLSA-GEOMETRY-SHA256-v1\0')
    for c in comps:
        a=np.asarray(c,dtype='<f8',order='C'); h.update(np.asarray(a.shape,dtype='<i8').tobytes()); h.update(a.tobytes(order='C'))
    return h.hexdigest()

def test_hash_is_component_order_sensitive():
    a=np.arange(12,dtype=float).reshape(4,3); b=a+100
    assert pklsa_hash([a,b]) != pklsa_hash([b,a])
