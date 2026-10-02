import json, numpy as np
from pathlib import Path
from sst_modal_clock.sources import parse_katlas_pd,pd_to_components,discover_katlas,discover_all_sources

HOPF_PD='X<sub>4132</sub> X<sub>2314</sub>'

def _lk(a,b):
    A=np.roll(a,-1,axis=0)-a; am=.5*(a+np.roll(a,-1,axis=0))
    B=np.roll(b,-1,axis=0)-b; bm=.5*(b+np.roll(b,-1,axis=0)); s=0.0
    for i in range(len(A)):
        r=am[i]-bm; den=np.linalg.norm(r,axis=1)**3+1e-15
        s += np.sum(np.einsum('ij,ij->i',np.cross(A[i],B),r)/den)
    return s/(4*np.pi)

def test_katlas_pd_hopf_translator_preserves_two_components_and_linking():
    pd=parse_katlas_pd(HOPF_PD)
    assert pd==[(4,1,3,2),(2,3,1,4)]
    comps=pd_to_components(pd,64,12)
    assert len(comps)==2 and all(len(x)>=32 for x in comps)
    assert abs(abs(_lk(comps[0],comps[1]))-1.0)<0.08

def _write_katlas_link(root):
    d=root/'links'/'02'/'L2a1'; d.mkdir(parents=True)
    obj={'identity':{'katlas_id':'L2a1','kind':'link','crossings':2,'table':'Thistlethwaite'},
         'presentations':{'pd':[HOPF_PD],'gauss':['{1, -2}, {2, -1}'],'dt':['']},'invariants':{}}
    (d/'katlas.json').write_text(json.dumps(obj))

def _write_gilbert_link(root):
    root.mkdir(parents=True,exist_ok=True)
    txt='''<TL Id="L2a1"><STRING I="1"><Coeff I="1" A="{1,0,0}" B="{0,1,0}"/></STRING><STRING I="2"><Coeff I="1" A="{1,0,0}" B="{0,1,0}"/><Coeff I="0" A="{0,0,2}" B="{0,0,0}"/></STRING></TL>'''
    (root/'IdealLinks.txt').write_text(txt)

def test_katlas_link_discovery_marks_pd_generated_not_source_coordinates(tmp_path):
    _write_katlas_link(tmp_path/'katlas')
    rows,st=discover_katlas(tmp_path/'katlas',64)
    assert len(rows)==1 and rows[0].topology_id=='L2.2.1' and len(rows[0].components)==2
    assert rows[0].metadata['translator']=='SST-KATLAS-PD-3D-1.0'
    assert rows[0].metadata['geometry_origin']=='generated_from_katlas_pd'
    assert rows[0].metadata['source_coordinates'] is False
    assert st['link_geometry_records']==1 and st['component_mismatch']==0

def test_katlas_link_prefers_sibling_conditioned_geometry_npz(tmp_path):
    root=tmp_path/'katlas'; _write_katlas_link(root)
    link_dir=root/'links'/'02'/'L2a1'
    c0=np.column_stack([np.cos(np.linspace(0,2*np.pi,32,endpoint=False)),
                        np.sin(np.linspace(0,2*np.pi,32,endpoint=False)),
                        np.zeros(32)])
    c1=np.column_stack([np.cos(np.linspace(0,2*np.pi,32,endpoint=False))+2.0,
                        np.zeros(32),
                        np.sin(np.linspace(0,2*np.pi,32,endpoint=False))])
    pts=np.vstack([c0,c1]); offs=np.array([0,len(c0),len(pts)],dtype=np.int64)
    np.savez(link_dir/'conditioned_geometry.npz',points=pts,component_offsets=offs)
    rows,st=discover_katlas(root,64)
    assert len(rows)==1 and len(rows[0].components)==2
    assert st['conditioned_link_records']==1 and st['pd_link_records']==0
    assert rows[0].metadata['translator']=='SST-KATLAS-ISOTOPY-HARMONIC-2.0'
    assert rows[0].metadata['geometry_origin']=='generated_from_katlas_pd_conditioned'
    assert rows[0].metadata['source_coordinates'] is False
    assert abs(rows[0].components[0][0,0]-1.0)<1e-12

def test_min_carriers_counts_source_families_not_files(tmp_path):
    ir=tmp_path/'ideal'; kr=tmp_path/'katlas'; fr=tmp_path/'fremlin'; fr.mkdir()
    _write_gilbert_link(ir); _write_katlas_link(kr)
    cfg={'n_points':32,'source_roots':{'fseries':str(fr),'ideal':str(ir),'katlas':str(kr),'relaxed':str(tmp_path/'none')},
         'max_variants_per_topology_per_provenance':16,'require_all_selected_libraries':True}
    rows,s=discover_all_sources(cfg,libraries='Fremlin,Gilbert,Katlas',min_carriers=2,kind='links')
    assert len(rows)==2 and {r.provenance for r in rows}=={'ideal_links','katlas'}
    assert s['min_carriers_required']==2 and s['source_kind']=='links'
    rows3,_=discover_all_sources(cfg,libraries='Fremlin,Gilbert,Katlas',min_carriers=3,kind='links')
    assert rows3==[]
