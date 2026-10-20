import hashlib,json
from pathlib import Path
import numpy as np
from src.runner import ROOT,input_integrity,sha_file
from src.metrics import analyze_arrays

def test_manifest_and_encrypted_labels():
    m=input_integrity();assert len(m['inputs'])==3
    h=[]
    for x in m['inputs']:
        assert len(x['salted_truth_commitment_sha256'])==64
        assert (ROOT/'datasets'/x['truth_cipher_path']).exists()
        with np.load(ROOT/'datasets'/x['path'],allow_pickle=False) as d:
            h.append(hashlib.sha256(d['re'].tobytes()+d['im'].tobytes()).hexdigest())
    assert len(set(h))==1, '2D phase must be identical across three mechanisms'

def test_three_mechanisms_are_identifiable_only_with_3d():
    m=input_integrity();pred=[]
    for x in m['inputs']:
        with np.load(ROOT/'datasets'/x['path'],allow_pickle=False) as d:
            out=analyze_arrays({k:d[k] for k in d.files})
        pred.append(out['prediction'])
        assert out['gates']['G00_OBSERVABILITY']=='PASS'
        assert out['gates']['G01_PHASE_PAIR_ANNIHILATION']=='PASS'
        assert out['gates']['G05_PHYSICAL_RECONNECTION']=='UNRESOLVED_NO_NONIDEAL_PDE'
    assert len(set(pred))==3

def test_closed_contours_have_no_boundary_gaps():
    manifest=input_integrity()
    for x in manifest['inputs']:
        with np.load(ROOT/'datasets'/x['path'],allow_pickle=False) as d:
            f=d['filaments'];present=d['present']
            for frame in range(len(d['t'])):
                for j in range(present.shape[1]):
                    if present[frame,j]:
                        lengths=np.linalg.norm(np.roll(f[frame,j],-1,axis=0)-f[frame,j],axis=1)
                        assert lengths.max()/lengths.min()<1.05
