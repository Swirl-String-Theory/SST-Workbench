from __future__ import annotations
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
import tempfile
from pathlib import Path
import numpy as np
from sst_blind.io import load_fseries, load_xyz_text
from sst_blind.geometry import resample_closed, circle, detect_lobes, build_lobe_modes
from sst_blind.experiment import reduced_jacobian
from sst_blind.diagnostics import modal_attribution, closest_cross_lobe_pairs, lobe_pair_centroid_rates
from sst_blind.coupled import build_coupled_modes, coupled_jacobian, coupled_spectrum_analysis, family_coupling_ablation, floquet_monodromy
from native_ext.core import load_native, biot_savart, centerline_split

def main():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'circle.fseries';p.write_text('% test\n0 0 0\n1 0 0 1 0 0\n',encoding='utf-8')
        x=load_fseries(p,256);assert np.max(np.abs(np.linalg.norm(x[:,:2],axis=1)-1))<1e-10
        q=Path(td)/'xyz.txt';q.write_text('\n'.join(f'{i} {a} {b} {c}' for i,(a,b,c) in enumerate(x)),encoding='utf-8');y=load_xyz_text(q);assert y.shape==(256,3)
    mod=load_native(force_build=False,build_verbose=True); c=circle(128); v,b=biot_savart(c,c,gamma=1,core=.04,backend='openmp' if mod else 'python',mod=mod)
    radial=np.c_[c[:,:2],np.zeros(len(c))];radial/=np.linalg.norm(radial,axis=1)[:,None];rr=float(np.mean(np.einsum('ij,ij->i',v,radial)));assert abs(rr)<1e-5,rr
    t=np.linspace(0,2*np.pi,144,endpoint=False);tr=np.c_[(2+.45*np.cos(3*t))*np.cos(2*t),(2+.45*np.cos(3*t))*np.sin(2*t),.45*np.sin(3*t)];tr=resample_closed(tr,144,target_length=2*np.pi);pk,lab,_=detect_lobes(tr);mi=build_lobe_modes(tr,pk,lab);assert len(mi['modes'])==6
    sp,bb=centerline_split(tr,lab,gamma=1,core=.04,local_span=4,mod=mod);err=np.linalg.norm(sp['total']-(sp['local']+sp['same_lobe']+sp['cross_lobe']+sp['transition']))/np.linalg.norm(sp['total']);assert err<1e-10,err
    cp=closest_cross_lobe_pairs(tr,lab,sp,top_k=6,skip=12,exclusion=3);assert len(cp['pairs'])>=3
    lp=lobe_pair_centroid_rates(tr,lab,gamma=1,core=.04);assert len(lp['pairs'])==3
    j=reduced_jacobian(tr,mi,eps=.005,gamma=1,core=.04,local_span=4,mod=mod);ma=modal_attribution(j['J'],mi['names']);assert len(ma)==6
    recon=max(r['reconstruction_abs_error'] for r in ma);assert recon<1e-8,recon
    cmi=build_coupled_modes(tr,kelvin_harmonics=(2,3),peaks=pk,labels=lab);assert {'breathing','torsion','kelvin'}<=set(cmi['families'])
    cj=coupled_jacobian(tr,cmi,eps=.005,gamma=1,core=.04,local_span=4,mod=mod);cs=coupled_spectrum_analysis(cj['J']['total'],cmi);assert len(cs)==len(cmi['names'])
    fa=family_coupling_ablation(cj['J']['total'],cmi);assert 'decouple_torsion' in fa and 'decouple_kelvin' in fa and 'block_diagonal_families' in fa
    fg=floquet_monodromy(tr,cmi,{'candidate':{'best_recurrence':0.5}},cfg={'rpo_recurrence_max':0.05},gamma=1,core=.04,backend='python',allow_sycl_cpu=False,mod=mod);assert not fg['valid'] and fg['reason']=='rpo_recurrence_above_threshold'
    print({'ok':True,'native':bool(mod),'circle_radial_rate':rr,'split_rel_error':err,'modal_reconstruction_error':recon,'contact_pairs':len(cp['pairs']),'lobe_pairs':len(lp['pairs']),'legacy_modes':mi['names'],'coupled_mode_count':len(cmi['names']),'families':sorted(set(cmi['families']))})
if __name__=='__main__':main()
