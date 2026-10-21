#!/usr/bin/env python3
"""Run from staging: py -3 tests/test_patch_v043b.py [--base C:/.../A006]"""
import argparse,sys,math,tempfile,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from selection_v043b import (parse,checkpoints,bead_grid,select_names,required_beadlimit,
                             KNOTS,LINKS,components_from_xyz,write_xyz3,reflected,edge_stats)
from orientation_v043b import (rotate_about_normal,orientation_key,orient_components)

def test_synthetic():
 assert len(KNOTS)==13 and set(LINKS)=={'5_5_6','6_6_5'}
 assert bead_grid(256,2048)==[256,512,1024,2048]
 assert checkpoints(8000,500)[-1]==8000
 assert select_names('11_1,11_2',KNOTS)==['11a367','11a247']
 assert required_beadlimit([1215,1101,1024])==4000
 assert required_beadlimit([2048,2048,2048])==8000
 assert required_beadlimit([256,256,256]) is None
 assert parse(['--knots=5_2','--links=5_5_6','minN=256','--closurePolicy=MANUAL','--closureAngles=0,0,180']).closurePolicy=='MANUAL'
 assert orientation_key('MANUAL',(0,0,180))!=orientation_key('MANUAL',(0,180,0))
 n=256;t=np.arange(n)*2*np.pi/n
 p=np.column_stack((np.cos(t),np.sin(t),.1*np.cos(2*t)))
 o=np.array([1.,2.,3.]);normal=np.array([0.,0.,1.])
 q=rotate_about_normal(p,o,normal,180)
 assert np.allclose(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1),np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1))
 with tempfile.TemporaryDirectory() as td:
  path=Path(td)/'three.xyz'
  write_xyz3(path,[p,p,q]); txt=path.read_text()
  assert txt.count('\n\n')==2
  assert [len(v) for v in components_from_xyz(path)]==[256]*3
  bad=Path(td)/'labelled.xyz';bad.write_text('Component 0:\n'+txt)
  try:components_from_xyz(bad)
  except ValueError:pass
  else:raise AssertionError('Multicomponent header incorrectly accepted')
 print('PASS: independent synthetic parser, arguments, beadlimits, geometry invariance, XYZ contract')

def test_real(base):
 from selection_v043b import legacy_output_subdir
 root=Path(base)
 src=legacy_output_subdir(root,'borromean')/'Borromean_5_5_6_BALANCED_MIN0256_S0800_v042c.xyz'
 comp=components_from_xyz(src)
 out,rep=orient_components(comp,'CENTER',(0,0,180),root,('5_2','5_2','6_1'))
 assert rep['angles_deg']==[0.,0.,180.],rep['angles_deg']
 assert [len(p) for p in out]==[284,264,256]
 assert rep['tested_candidates'][-1]['accepted']
 assert all(np.allclose(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1),
                               np.linalg.norm(np.roll(b,-1,axis=0)-b,axis=1)) for a,b in zip(comp,out))
 with tempfile.TemporaryDirectory() as d:
  xyz=Path(d)/'three.xyz';write_xyz3(xyz,out)
  assert [len(p) for p in components_from_xyz(xyz)]==[284,264,256]
 print('PASS: native A006 v0.4.2d whole-component 5_5_6 CENTER selects only 6_1 flip; three-block XYZ')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path)
 args=p.parse_args();test_synthetic()
 if args.base:test_real(args.base)
 else:print('SKIP: native-base integration requires --base')
