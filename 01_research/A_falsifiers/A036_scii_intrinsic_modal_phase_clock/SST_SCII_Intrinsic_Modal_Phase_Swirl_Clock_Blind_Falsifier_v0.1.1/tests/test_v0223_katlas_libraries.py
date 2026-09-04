from pathlib import Path
import json
import numpy as np
from sst_modal_clock.sources import parse_katlas_braid,braid_to_components,discover_katlas,normalize_library_selection,discover_all_sources


def test_katlas_braid_parser_and_trefoil_component():
    b=parse_katlas_braid(r'<math>\textrm{BR}(2,\{-1,-1,-1\})</math>')
    assert b==(2,[-1,-1,-1])
    c=braid_to_components(*b,n_points=64)
    assert len(c)==1 and c[0].shape[1]==3 and np.isfinite(c[0]).all()


def test_katlas_discovery_marks_geometry_as_translated_not_source_coordinates(tmp_path):
    d=tmp_path/'knots'/'03'/'3_1';d.mkdir(parents=True)
    obj={'identity':{'katlas_id':'3_1','kind':'knot','crossings':3,'table':'Rolfsen'},'presentations':{'braid':[r'<math>\textrm{BR}(2,\{-1,-1,-1\})</math>'],'dt':['4 6 2'],'gauss':['-1, 3, -2, 1, -3, 2']},'invariants':{'Determinant':['3']}}
    (d/'katlas.json').write_text(json.dumps(obj))
    rows,st=discover_katlas(tmp_path/'knots',64)
    assert len(rows)==1 and rows[0].topology_id=='K3.1' and rows[0].provenance=='katlas'
    assert rows[0].metadata['geometry_origin']=='generated_from_katlas_braid'
    assert rows[0].metadata['source_coordinates'] is False
    assert st['geometry_records']==1


def test_katlas_dt_only_is_metadata_only_not_invented_geometry(tmp_path):
    d=tmp_path/'knots'/'12'/'12a_1';d.mkdir(parents=True)
    obj={'identity':{'katlas_id':'12a_1','kind':'knot','crossings':12,'table':'HT'},'presentations':{'dt':['4 6 2']}}
    (d/'katlas.json').write_text(json.dumps(obj))
    rows,st=discover_katlas(tmp_path/'knots',64)
    assert rows==[] and st['metadata_only_no_braid']==1


def test_library_names_normalize():
    assert normalize_library_selection('Fremlin,Gilbert,Katlas')==['fseries','gilbert','katlas']
    assert normalize_library_selection('KnotPlot,Fremlin')==['relaxed','fseries']


def _write_fseries(root):
    d=root/'3_1';d.mkdir(parents=True);(d/'knot.3_1.fseries').write_text('1 0 0 1 0 0\n0.1 0 0 0.1 0.2 0\n')

def _write_ideal(root):
    root.mkdir(parents=True,exist_ok=True);(root/'Ideal.txt').write_text('<DATA><AB Id="3:1:1"><Coeff I="1" A="1,0,0" B="0,1,0"/></AB><AB Id="4:1:1"><Coeff I="1" A="1,0,0" B="0,1,0"/></AB></DATA>')

def _write_katlas(root):
    for kid,cross,n,word in [('3_1',3,2,[-1,-1,-1]),('4_1',4,3,[-1,2,-1,2])]:
        d=root/f'{cross:02d}'/kid;d.mkdir(parents=True,exist_ok=True)
        br='<math>\\textrm{BR}(%d,\\{%s\\})</math>'%(n,','.join(map(str,word)))
        (d/'katlas.json').write_text(json.dumps({'identity':{'katlas_id':kid,'kind':'knot','crossings':cross},'presentations':{'braid':[br]}}))


def test_explicit_three_library_selection_uses_intersection_and_skips_knotplot(tmp_path):
    fr=tmp_path/'fremlin';ir=tmp_path/'ideal';kr=tmp_path/'katlas';_write_fseries(fr);_write_ideal(ir);_write_katlas(kr)
    cfg={'n_points':32,'source_roots':{'fseries':str(fr),'ideal':str(ir),'katlas':str(kr),'relaxed':str(tmp_path/'missing')},'max_variants_per_topology_per_provenance':16,'require_all_selected_libraries':True}
    rows,s=discover_all_sources(cfg,libraries='Fremlin,Gilbert,Katlas')
    assert s['selected_libraries']==['Fremlin','Gilbert','Katlas'] and s['discovered_counts']['relaxed']==0
    assert {r.topology_id for r in rows}=={'K3.1'}
    assert {r.provenance for r in rows}=={'fseries','ideal','katlas'}
