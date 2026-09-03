import json, math
import numpy as np
import sst_knotlib as sk

cases={
    'classic_trefoil': sk.classic_trefoil(512),
    'track_trefoil': sk.shader_track_trefoil(512),
    'torus_2_3': sk.torus_knot(2,3,512,R=2.0,a=0.6),
    'figure8_s3': sk.figure8_s3(512),
}
out={}
for name,p in cases.items():
    conv=sk.convergence_report(p,levels=(128,256,512))
    out[name]={'convergence':conv,'finite':bool(np.isfinite(p).all())}

# S3 topology-preserving control: roundtrip/deformation preserves sample count and finite coordinates.
p=sk.classic_trefoil(512,scale=0.2)
d=sk.s3_deform(p,angle=0.35)
out['s3_control']={
    'length_ratio': sk.curve_length(d)/sk.curve_length(p),
    'writhe_before': sk.writhe(p),
    'writhe_after': sk.writhe(d),
}
print(json.dumps(out,indent=2))
