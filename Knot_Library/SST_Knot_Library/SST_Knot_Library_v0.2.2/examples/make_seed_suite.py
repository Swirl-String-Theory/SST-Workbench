from pathlib import Path
import json
from sst_knotlib import (
    classic_trefoil, shader_track_trefoil, torus_knot, figure8_s3, lissajous_7_4,
    generate_topology_seed, thread_bundle, qualify_seed, KAtlasSnapshot,
)
from sst_knotlib.io import save_xyz

out=Path('outputs/seed_suite'); out.mkdir(parents=True,exist_ok=True)
seeds={
 'classic_trefoil': classic_trefoil(512),
 'track_trefoil_balanced': shader_track_trefoil(512,bulge_R=2.2,z_weave=3.0),
 'track_trefoil_flat': shader_track_trefoil(512,bulge_R=2.4,z_weave=2.2),
 'track_trefoil_tall': shader_track_trefoil(512,bulge_R=1.8,z_weave=4.2),
 'figure8_s3': figure8_s3(512),
 'T_3_5': torus_knot(3,5,512,R=2.5,a=0.65),
 '7_4_lissajous': lissajous_7_4(512),
}
for kid in KAtlasSnapshot().ids(): seeds[f'{kid}_katlas_braid']=generate_topology_seed(kid,method='braid',n=512)
report={}
for name,p in seeds.items():
    save_xyz(out/f'{name}.xyz',p)
    # dimensionless demo core radius; physical falsifiers must normalize and inject configured core radius
    report[name]=qualify_seed(p,core_radius=0.05,n=512)
bundle=thread_bundle(seeds['track_trefoil_balanced'],n_threads=6,turns=3.0,radius=0.12)
for i,p in enumerate(bundle): save_xyz(out/f'bundle_thread_{i:02d}.xyz',p)
(out/'qualification_demo.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(out)
