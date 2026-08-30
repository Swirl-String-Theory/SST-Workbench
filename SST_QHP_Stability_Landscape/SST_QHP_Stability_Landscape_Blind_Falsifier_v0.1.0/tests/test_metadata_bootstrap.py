from pathlib import Path
import csv
import numpy as np
from sst_qhp_falsifier.geometry import bootstrap_metadata


def _write_xyz(path):
    t=np.linspace(0,2*np.pi,32,endpoint=False)
    x=np.c_[np.cos(t),np.sin(t),0.1*np.sin(2*t)]
    np.savetxt(path,x)


def test_bootstrap_promotes_complete_filename_tokens(tmp_path):
    _write_xyz(tmp_path/'shape_q0p1_h-0p2_p0p3.txt')
    z=bootstrap_metadata(tmp_path)
    assert z['ready'] and z['source']=='filename-inference-promoted'
    mp=tmp_path/'qhp_metadata.csv'
    assert mp.exists()
    r=next(csv.DictReader(mp.open(newline='',encoding='utf-8')))
    assert float(r['q'])==0.1 and float(r['h'])==-0.2 and float(r['p'])==0.3


def test_bootstrap_never_invents_missing_coordinates(tmp_path):
    _write_xyz(tmp_path/'shape_q0p1.txt')
    z=bootstrap_metadata(tmp_path)
    assert not z['ready'] and z['source']=='template-required'
    assert (tmp_path/'qhp_metadata_template.csv').exists()
    assert not (tmp_path/'qhp_metadata.csv').exists()


def test_signed_qhp_filename_tokens_preserve_sign():
    from sst_qhp_falsifier.geometry import parse_qhp_from_name
    a=parse_qhp_from_name('shape_q0p1_h-0p2_p0p3.txt')
    assert a=={'q':0.1,'h':-0.2,'p':0.3}
    b=parse_qhp_from_name('shape_q_m0p4_h_0p5_p_m0p6.txt')
    assert b=={'q':-0.4,'h':0.5,'p':-0.6}
