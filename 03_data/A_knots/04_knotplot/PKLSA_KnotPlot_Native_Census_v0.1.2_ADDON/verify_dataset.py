#!/usr/bin/env python3
"""Check PKLSA native KnotPlot dataset deterministically. No mutation."""
from __future__ import annotations
from pathlib import Path
import argparse,json,hashlib,math,numpy as np

def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,default=Path(__file__).resolve().parent/'dataset')
 a=p.parse_args(argv);root=a.dataset;reg=json.loads((root/'registry.json').read_text(encoding='utf-8'))
 assert reg['dataset_id']=='knotplot.native_census.v0.1.2'
 seen=set();cn=beads=0;total=0.
 for obj in reg['objects']:
  ident=obj['geometry_id'];assert ident not in seen;seen.add(ident)
  for key,hashkey in [('kpf_path','sha256_kpf'),('xyz_path','sha256_xyz')]:
   pp=root/obj[key]; assert pp.resolve().parent == (root/'raw_native').resolve()
   assert hashlib.sha256(pp.read_bytes()).hexdigest()==obj[hashkey], pp
  text=(root/obj['xyz_path']).read_text(encoding='utf-8')
  chunks=[];cur=[]
  for line in text.splitlines():
   if not line.strip():
    if cur:chunks.append(np.asarray(cur,float));cur=[]
   else:
    nums=line.split();assert len(nums)==3
    cur.append([float(i) for i in nums])
  if cur:chunks.append(np.asarray(cur,float))
  assert len(chunks)==obj['component_count']
  for a,b in zip(chunks,obj['components']):
   assert np.isfinite(a).all() and len(a)==b['n_beads']
   v=np.roll(a,-1,axis=0)-a
   L=float(np.linalg.norm(v,axis=1).sum())
   # Audited L is from FP32 KnotPlot KPF; ASCII coordinates may deviate slightly
   assert abs(L-b['length_polygon_knotplot_units'])<3e-4,(ident,L)
   cn+=1;beads+=len(a)
  total+=obj['length_polygon_knotplot_units']
 assert len(seen)==50 and cn==85 and beads==4431
 assert abs(total-7094.924)<1e-4
 print(json.dumps({'dataset_id':reg['dataset_id'],'objects':len(seen),'components':cn,'beads':beads,'length_knotplot_units':total,'sha256':'PASS','xyz_polygon_arclength':'PASS','topology_identity':'UNVERIFIED','finite_core_convergence':'NOT_TESTED','result':'DATASET_VERIFIED'},indent=2))
if __name__=='__main__':main()
