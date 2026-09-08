from pathlib import Path
import numpy as np
from sst_threaded_hole_falsifier.generators import carrier_catalog,make_thread_bundle
from sst_threaded_hole_falsifier.topology import gauss_link,thread_link_matrix
ROOT=Path(__file__).resolve().parents[1]

def test_catalog_families():
    c=carrier_catalog(ROOT/'assets/fseries',72)
    assert {'TORUS_T2_3','TWIST_5_2','TRIPLE_GEAR_T3_3'}<=set(c)
    assert c['TRIPLE_GEAR_T3_3']['geometry'].n_components==3

def test_triple_gear_is_three_pairwise_linked_unknot_proxy():
    c=carrier_catalog(ROOT/'assets/fseries',96)['TRIPLE_GEAR_T3_3']['geometry'].components()
    vals=[abs(gauss_link(c[i],c[j])) for i in range(3) for j in range(i+1,3)]
    assert all(abs(x-1)<0.08 for x in vals)

def test_threads_link_torus_and_triple_gear():
    cats=carrier_catalog(ROOT/'assets/fseries',96)
    for key in ('TORUS_T2_3','TRIPLE_GEAR_T3_3'):
        e=cats[key];t,m=make_thread_bundle(e['geometry'],1,1.0,72,e['hole_axis'],.035);lm=thread_link_matrix(e['geometry'],t)
        assert m['hole_clearance']>.1
        assert max(abs(x) for row in lm for x in row)>.8

def test_twist_axis_search_finds_threadable_hole():
    cats=carrier_catalog(ROOT/'assets/fseries',96)
    for key in ('TWIST_4_1','TWIST_5_2','TWIST_6_1','TWIST_7_2'):
        e=cats[key];t,m=make_thread_bundle(e['geometry'],1,1.0,72,e['hole_axis'],.035);lm=thread_link_matrix(e['geometry'],t)
        assert m['hole_clearance']>.11
        assert abs(lm[0][0])>.75
