from pathlib import Path
from tools.audit_original_scripts import audit

def test_historical_archive_shape():
    root=Path(__file__).resolve().parents[1]; a=audit(root)
    assert a['file_count']==50
    assert a['kind_counts']=={'knot':20,'link':16,'torus':14}
    assert a['implicit_sformat_dependency'] is True
