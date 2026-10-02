from pathlib import Path
import sys
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE/'tools'))
from sklsa.discovery import candidate_knotplot_roots, scan_knotplot
from run_inventory import normalize_workbench_root


def _fake_wb(tmp_path: Path) -> Path:
    wb=tmp_path/'SST-Workbench'
    (wb/'01_research').mkdir(parents=True)
    (wb/'03_data'/'A_knots'/'KnotPlot'/'knots'/'final'/'3_1').mkdir(parents=True)
    (wb/'03_data'/'A_knots'/'KnotPlot'/'knots'/'final'/'4_1').mkdir(parents=True)
    (wb/'03_data'/'A_knots'/'KnotPlot'/'knots'/'final'/'3_1'/'final.xyz').write_text('0 0 0\n1 0 0\n0 1 0\n',encoding='utf-8')
    (wb/'03_data'/'A_knots'/'KnotPlot'/'knots'/'final'/'4_1'/'final.xyz').write_text('0 0 0\n1 0 0\n0 1 0\n',encoding='utf-8')
    return wb


def test_normalize_parent_to_workbench(tmp_path):
    wb=_fake_wb(tmp_path)
    assert normalize_workbench_root(tmp_path)==wb
    assert normalize_workbench_root(wb)==wb


def test_knotplot_scan_selected_only(tmp_path):
    wb=_fake_wb(tmp_path)
    roots=candidate_knotplot_roots(wb)
    assert roots
    rows=scan_knotplot(wb,{'3_1'})
    assert len(rows)==1
    assert rows[0]['topology_id']=='3_1'
    assert rows[0]['sha256']
