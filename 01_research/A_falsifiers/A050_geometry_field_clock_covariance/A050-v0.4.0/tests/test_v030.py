import gzip, json
from pathlib import Path
import numpy as np
from tools.pklsa_stage_lib import load_xyz,load_vect,find_gilbert_record,sample_coeff
from sst_gfcc_blind.geometry import resample_closed
from sst_gfcc_blind.modes import bishop_frame

def test_xyz_loader(tmp_path):
 p=tmp_path/'a.txt'; p.write_text('0 0 0\n1 0 0\n0 1 0\n'); c=load_xyz(p); assert len(c)==1 and c[0].shape==(3,3)
def test_vect_loader(tmp_path):
 p=tmp_path/'a.vect'; p.write_text('VECT\n1 4 0\n-4\n0\n0 0 0\n1 0 0\n1 1 0\n0 1 0\n'); c=load_vect(p); assert len(c)==1 and c[0].shape==(4,3)
def test_gilbert_sampler(tmp_path):
 s='<AB Id="3:1:1"><Coeff I="1" A="1,0,0" B="0,1,0"/></AB>\n'; p=tmp_path/'Ideal.txt.gz'
 with gzip.open(p,'wt',encoding='utf-8') as f:f.write(s)
 comps=find_gilbert_record(p,'3_1'); q=sample_coeff(comps[0],64); assert q.shape==(64,3); assert np.max(np.abs(np.sqrt(q[:,0]**2+q[:,1]**2)-1))<1e-12
def test_bishop_frame_external_curve():
 t=np.linspace(0,2*np.pi,72,endpoint=False); p=np.c_[np.cos(t),np.sin(t),.2*np.sin(3*t)]; p=resample_closed(p,72); T,N,B=bishop_frame(p); assert np.max(np.abs(np.sum(T*N,axis=1)))<1e-10; assert np.isfinite(B).all()
def test_blind_config_has_no_fixed_target_mode():
 cfg=json.loads((Path(__file__).parents[1]/'config/default.json').read_text()); assert cfg['observation_protocol']['target_branch_mode_fixed'] is False
