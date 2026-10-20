import json
import numpy as np
import pytest
from pathlib import Path
import torch
from gp_full_xpu import (SCHEMA,metrics,torch_k2,step,load_numpy_checkpoint,load_generated_checkpoint,
                        seed_chunked,source_geometry_screen,save_field,fp64_parity,sha256)
from gp_xpu_probe_v063_baseline import numpy_step,kinetic_numpy,relative_l2
from a069_v061.campaign_v062 import CASES,Case
from a069_v061.gp_core_v062 import conserved_mu,coupling_from_xi
from framework_v110_export import transform


def sample(n=16):
    x=np.arange(n)*2*np.pi/n
    a=1+.018*np.cos(x[:,None,None])+.009*np.sin(2*x[None,:,None])
    p=.01*np.sin(x[None,None,:]+x[:,None,None])
    return np.broadcast_to(a*np.exp(1j*p),(n,n,n)).copy()


def test_energy_parseval_matches_fp64():
    n=16;box=10.;mu=6.377551020408163
    z=sample(n).astype(np.complex64)
    g=metrics(torch,torch.from_numpy(z),torch_k2(torch,n,box,torch.device('cpu')),box,mu)
    m,e=conserved_mu(z.astype(np.complex128),box,mu)
    assert abs(g['mass']/m-1)<2e-7
    assert abs(g['energy']/e-1)<8e-6


def test_gp_step_cpu_vs_numpy_fp64():
    n=16;box=10.;dt=.003;mu=6.377551020408163
    z=sample(n).astype(np.complex64)
    k2=torch_k2(torch,n,box,torch.device('cpu'))
    kin=torch.exp((-0.5j*dt)*k2)
    t=torch.from_numpy(z.copy());ref=z.astype(np.complex128);k=kinetic_numpy(n,box,dt)
    for _ in range(6):
        t=step(torch,t,kin,dt,mu)
        ref=numpy_step(ref,k,dt,mu)
    assert relative_l2(t.numpy(),ref)<3e-6


def test_generated_checkpoint_fingerprint(tmp_path):
    c=Case('TINY','B',16,.28,box=10.,dt=.003,steps=8)
    p=tmp_path/'T000004.npy';z=torch.ones((16,16,16),dtype=torch.complex64)
    r=save_field(torch,z,p,c,4,{'kind':'test','step':0})
    state,source=load_generated_checkpoint(p,c)
    assert state.shape==(16,)*3 and source['step']==4
    assert r['field_sha256']==sha256(p)
    with pytest.raises(FileExistsError):save_field(torch,z,p,c,4,{})
    side=p.with_suffix('.json');meta=json.loads(side.read_text());meta['science']['xi']=.3
    side.write_text(json.dumps(meta))
    with pytest.raises(ValueError,match='science identity'):load_generated_checkpoint(p,c)


def test_v062_checkpoint_strict(tmp_path):
    c=Case('B160','B',16,.28,box=10.,dt=.003,steps=8)
    a=np.ones((16,)*3,dtype=np.complex128);p=tmp_path/'a.npz'
    np.savez(p,psi=a,dt=.003,box=10.,xi=.28,mu=coupling_from_xi(.28),case='B160',step=16,
             source_sha256='bb8e1d392e3e72c0c2caee22df406469f9f3de5504296da45cedc6fda8d04b6e',grid_n=16)
    state,meta=load_numpy_checkpoint(p,c)
    assert meta['step']==16 and meta['not_independent']
    with pytest.raises(ValueError):load_numpy_checkpoint(p,Case('A160','A',16,.08))


def test_short_fp64_reference_screening():
    c=Case('B_SIM','B',16,.28,box=10.,dt=.003)
    r=fp64_parity(torch,sample(16),c,torch.device('cpu'),2,2e-5)
    assert r['status']=='PASS_NUMERICAL_SCREENING'


def test_gate_export_does_not_promote_physics():
    input={'schema':SCHEMA,'g32_screen':{'all_preconditions_met':True},'cpu_fp64_parity':{
        'status':'PASS_NUMERICAL_SCREENING','execution_status':'EXECUTED'}}
    e=transform(input)
    assert e['evaluations']['G32']['qualification']=='DIAGNOSTIC_ONLY'
    assert e['evaluations']['G34']['status']=='UNRESOLVED'
    assert e['evaluations']['G35']['status']=='UNRESOLVED'
    assert e['G9_reveal_eligibility']=='BLOCKED'


def test_science_fingerprint_source_native():
    geom,screen=source_geometry_screen(CASES['B160'])
    assert geom['samples']==1200
    assert screen['all_preconditions_met']
    _,a=source_geometry_screen(CASES['A160'])
    assert not a['all_preconditions_met']


def test_streaming_initialization_matches_original(tmp_path):
    from gp_full_xpu import ROOT
    import sys
    up=ROOT/'upstream_runtime'/'A069_3D_SwirlClock_Emergence'/'A069-v0.5.0'
    sys.path.insert(0,str(up))
    from experiment.knotted_gp3d import initialize
    case=Case('TINY_B','B',16,.28,box=10.,dt=.003,steps=2,segments=32)
    field,info=seed_chunked(case,tmp_path/'source.npy',planes=3)
    orig,_=initialize('B',n=16,xi=.28,box=10.,segments=32)
    assert relative_l2(field.astype(np.complex128),orig)<3e-7
    assert info['kind']=='independent_2015_source_native_seed'


def test_vram_calibration_failclosed(tmp_path):
    from gp_full_xpu import calibrated_vram_bytes_per_voxel
    p=tmp_path/'B256.json';p.write_text(json.dumps({'schema':SCHEMA,'xpu_used':True,'case':{'case_id':'B256','n':256},
                                                    'peak_reserved_bytes':1500000000,'start_step':0,'end_step':16}))
    x,observed=calibrated_vram_bytes_per_voxel(p)
    assert x>=90 and observed>0
    p.write_text(json.dumps({'schema':SCHEMA,'xpu_used':False,'case':{'case_id':'B256','n':256},
                             'peak_reserved_bytes':1500000000,'start_step':0,'end_step':16}))
    with pytest.raises(ValueError):calibrated_vram_bytes_per_voxel(p)


def test_time_refinement_is_seed_only():
    from gp_full_xpu import parse
    a=parse(['--case','B256','--init','seed','--dt','.0015','--total-steps','32'])
    assert a.dt==.0015 and a.total_steps==32
