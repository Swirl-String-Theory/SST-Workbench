import json
import numpy as np
import sst_knotlib as sk
from sst_knotlib.topology import braid_reference_report

cases={
    'classic_trefoil':sk.classic_trefoil(512),
    'track_trefoil':sk.shader_track_trefoil(512),
    'torus_2_3':sk.torus_knot(2,3,512,R=2.0,a=0.6),
    'figure8_s3':sk.figure8_s3(512),
    'lissajous_7_4':sk.lissajous_7_4(512),
}
out={'library_version':sk.__version__,'registry':sk.KAtlasSnapshot().report(),'providers':sk.provider_status(),'cases':{},'braids':{}}
for name,p in cases.items(): out['cases'][name]={'convergence':sk.convergence_report(p,levels=(128,256,512)),'finite':bool(np.isfinite(p).all())}
for kid in sk.KAtlasSnapshot().ids():
    out['braids'][kid]=braid_reference_report(kid)
    p=sk.generate_topology_seed(kid,method='braid',n=256)
    out['braids'][kid]['seed']={'N':len(p),'finite':bool(np.isfinite(p).all()),'length':sk.curve_length(p),'writhe':sk.writhe(p)}
p=sk.classic_trefoil(512,scale=0.2); d=sk.s3_deform(p,angle=0.35)
out['s3_control']={'length_ratio':sk.curve_length(d)/sk.curve_length(p),'writhe_before':sk.writhe(p),'writhe_after':sk.writhe(d)}
print(json.dumps(out,indent=2))
