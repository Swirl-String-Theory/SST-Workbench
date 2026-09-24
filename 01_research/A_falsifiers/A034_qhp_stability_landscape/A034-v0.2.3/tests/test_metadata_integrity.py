import csv
import numpy as np
import pytest
from sst_qhp_falsifier.geometry import load_metadata


def _xyz(path):
    t=np.linspace(0,2*np.pi,32,endpoint=False)
    np.savetxt(path,np.c_[np.cos(t),np.sin(t),0.1*np.sin(2*t)])


def test_geometry_ok_false_is_excluded(tmp_path):
    _xyz(tmp_path/'a.txt'); _xyz(tmp_path/'b.txt')
    with (tmp_path/'qhp_metadata.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['file','family','q','h','p','replicate','geometry_ok']); w.writeheader()
        w.writerow({'file':'a.txt','family':'knot_3.1','q':0,'h':0,'p':0,'replicate':0,'geometry_ok':'true'})
        w.writerow({'file':'b.txt','family':'knot_3.1','q':.1,'h':0,'p':0,'replicate':0,'geometry_ok':'false'})
    rows,src,stats=load_metadata(tmp_path,return_stats=True)
    assert len(rows)==1
    assert stats['metadata_rows_total']==2 and stats['geometry_rejected_excluded']==1


def test_duplicate_coordinate_node_is_hard_error(tmp_path):
    _xyz(tmp_path/'a.txt'); _xyz(tmp_path/'b.txt')
    with (tmp_path/'qhp_metadata.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['file','family','q','h','p','replicate']); w.writeheader()
        for fn in ('a.txt','b.txt'):
            w.writerow({'file':fn,'family':'6.3','q':0,'h':0,'p':0,'replicate':0})
    with pytest.raises(RuntimeError,match='duplicate .*nodes'):
        load_metadata(tmp_path)


def test_duplicate_file_path_is_hard_error(tmp_path):
    _xyz(tmp_path/'a.txt')
    with (tmp_path/'qhp_metadata.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['file','family','q','h','p','replicate']); w.writeheader()
        w.writerow({'file':'a.txt','family':'A','q':0,'h':0,'p':0,'replicate':0})
        w.writerow({'file':'a.txt','family':'B','q':.1,'h':0,'p':0,'replicate':0})
    with pytest.raises(RuntimeError,match='duplicate geometry file paths'):
        load_metadata(tmp_path)
