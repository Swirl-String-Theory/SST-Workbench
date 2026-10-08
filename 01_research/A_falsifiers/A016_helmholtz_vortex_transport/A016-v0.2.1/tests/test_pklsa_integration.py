from pathlib import Path
import json
import numpy as np

from experiment.pklsa import discover_qualified_carriers, load_pklsa_geometry


def _circle(n=64, radius=1.0):
    a=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.column_stack([radius*np.cos(a),radius*np.sin(a),np.zeros_like(a)])


def test_pklsa_v040_release_and_carrier_discovery(tmp_path, monkeypatch):
    wb=tmp_path/'wb'; pklsa=wb/'01_research'/'E_pipelines'/'E010_pklsa_parametric_knot_link_seed_atlas'/'E010-v0.4.0'; atlas=pklsa/'atlas_out'; atlas.mkdir(parents=True)
    (atlas/'RELEASE.json').write_text(json.dumps({
        'schema':'PKLSA-HIGH-RES-QUALIFICATION-4','atlas_version':'0.4.0','builder_version':'0.4.0',
        'publication_ready_geometry_layer':True,'scientific_boundary':'geometry only'
    }),encoding='utf8')
    top=atlas/'topologies'/'KX'; (top/'qualification').mkdir(parents=True)
    (top/'qualification'/'summary.json').write_text(json.dumps({'topology_id':'KX','qualification_gate_pass':True}),encoding='utf8')
    g1=tmp_path/'a.npz'; np.savez_compressed(g1,component_0=_circle(80,1.0))
    g2=tmp_path/'b.npz'; np.savez_compressed(g2,component_0=_circle(80,1.1))
    for branch,fam,prov,path,role in [
        ('sources','fam_a','provider_a',g1,'upstream'),
        ('sources','fam_b','provider_b',g2,'upstream'),
        ('generated','ptsa_braid','sst_generated',g1,'generated_from_topology_braid'),
    ]:
        d=top/branch/fam; d.mkdir(parents=True,exist_ok=True)
        payload={'carrier':{
            'topology_id':'KX','carrier_id':fam,'source_family':fam,'source_role':role,
            'source_path':str(path),'representation':'npz','independence_group':fam,
            'provider_group':prov,
        },'geometry_sha256':('1' if fam=='fam_a' else '2' if fam=='fam_b' else '3')*64}
        (d/f'{fam}.json').write_text(json.dumps(payload),encoding='utf8')
    monkeypatch.setenv('SST_WORKBENCH_ROOT',str(wb))
    carriers,meta=discover_qualified_carriers(Path(__file__).resolve().parents[1])
    assert meta['publication_ready_geometry_layer'] is True
    assert meta['n_qualified_carriers']==3
    assert meta['n_upstream_carriers']==2
    assert meta['n_generated_carriers']==1
    assert sum(c.generated for c in carriers)==1
    assert all(len(load_pklsa_geometry(c.source_path))==1 for c in carriers)
