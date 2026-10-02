from __future__ import annotations
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
import tempfile
from pathlib import Path
import numpy as np
from sst_blind.io import load_fseries, load_xyz_text
from sst_blind.geometry import resample_closed, circle, detect_lobes, build_lobe_modes, shape_field
from native_ext.core import load_native, biot_savart, centerline_split

def main():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'circle.fseries';p.write_text('% test\n0 0 0\n1 0 0 1 0 0\n',encoding='utf-8')
        x=load_fseries(p,256);assert np.max(np.abs(np.linalg.norm(x[:,:2],axis=1)-1))<1e-10
        q=Path(td)/'xyz.txt';q.write_text('\n'.join(f'{i} {a} {b} {c}' for i,(a,b,c) in enumerate(x)),encoding='utf-8');y=load_xyz_text(q);assert y.shape==(256,3)
    mod=load_native(force_build=False,build_verbose=True); c=circle(128); v,b=biot_savart(c,c,gamma=1,core=.04,backend='openmp' if mod else 'python',mod=mod)
    radial=np.c_[c[:,:2],np.zeros(len(c))];radial/=np.linalg.norm(radial,axis=1)[:,None];rr=float(np.mean(np.einsum('ij,ij->i',v,radial)));assert abs(rr)<1e-5,rr
    t=np.linspace(0,2*np.pi,192,endpoint=False);tr=np.c_[(2+.45*np.cos(3*t))*np.cos(2*t),(2+.45*np.cos(3*t))*np.sin(2*t),.45*np.sin(3*t)];tr=resample_closed(tr,192,target_length=2*np.pi);pk,lab,_=detect_lobes(tr);mi=build_lobe_modes(tr,pk,lab);assert len(mi['modes'])>=4
    sp,bb=centerline_split(tr,lab,gamma=1,core=.04,local_span=4,mod=mod);err=np.linalg.norm(sp['total']-(sp['local']+sp['same_lobe']+sp['cross_lobe']+sp['transition']))/np.linalg.norm(sp['total']);assert err<1e-10,err
    print({'ok':True,'native':bool(mod),'circle_radial_rate':rr,'split_rel_error':err,'modes':mi['names']})
if __name__=='__main__':main()
