from dataclasses import replace
from pathlib import Path
import csv
import numpy as np
import pytest
from experiment.euler3d import Config, Euler3D, stable_dt, run_paired
from experiment.science import profile_plan,probe_backend,run_matrix
from runtime_options import parse

def test_adaptive_cfl_core_and_vorticity_caps():
    c=Config(n=16,dt=.10,cfl_target=.1,max_core_shift=.04,max_vorticity_turn=.03)
    dt=stable_dt(c,c.box/c.n,2.0,5.0,.2)
    assert dt==pytest.approx(min(.1,.1*(10/16)/2,.04*c.core/2,.03/5))
    assert 2*dt/(10/16)<=.1 and 2*dt/c.core<=.04 and 5*dt<=.03

def test_absolute_final_time_and_synchronized_control():
    c=Config(n=16,dt=.017,final_time=.055,cfl_target=.02,steps_per_diagnostic=1)
    src,control,rows=run_paired(c)
    assert len(rows)>3
    assert rows[-1]['t']==pytest.approx(.055,abs=1e-12)
    assert all(0 < x['dt']<=.017+1e-14 for x in rows)
    assert all(x['max_shift_cells']<=.02+1e-12 for x in rows)
    assert [x['t'] for x in src['timeseries']]==[x['t'] for x in control['timeseries']]
    assert src['global_relative_energy_drift']<1e-7
    assert src['max_CFL']<=.02+1e-12
    assert abs(src['timeseries'][0]['E_global']-rows[0]['E_donor_run_J'])<1e-6

def test_cpp_nonlin_parity_and_short_evolution():
    if not probe_backend('cpp',Path('.'))['available']:
        pytest.skip('pybind11 artifact must be built locally')
    c=Config(n=16,dt=.03,final_time=.03,backend='cpu-scipy-fft')
    p=Euler3D(c);u,_=p.initial_velocity()
    cpp=Euler3D(replace(c,backend='cpp-hybrid'))
    assert np.allclose(p.rhs(u),cpp.rhs(u),rtol=1e-12,atol=1e-12)
    assert np.allclose(p.rk4(u,.03),cpp.rk4(u,.03),rtol=1e-12,atol=1e-12)

def test_torch_cpu_parity_same_state():
    torch=pytest.importorskip('torch')
    from experiment.euler_torch import TorchEuler3D
    c=Config(n=16,backend='torch-cpu-reference',final_time=.02,dt=.01)
    t=TorchEuler3D(c);w,_=t.initial_velocity()
    f=Euler3D(replace(c,backend='cpu-scipy-fft'));u,_=f.initial_velocity()
    assert np.allclose(w.cpu().numpy(),u,rtol=3e-12,atol=1e-10)
    assert np.allclose(t.rhs(w).cpu().numpy(),f.rhs(u),rtol=3e-10,atol=1e-10)

def test_gpu_no_cpu_fallback():
    a=probe_backend('gpu',Path('.'))
    if not a['available']:
        from experiment.euler_torch import TorchEuler3D
        with pytest.raises(RuntimeError,match='XPU_UNAVAILABLE'):
            TorchEuler3D(Config(n=16,backend='arc-xpu'))

def test_cli_adaptive_and_extended_and_matrix():
    a,opts,p=parse(['EXTENDED','--grid','80','--grid-up','96','--dt=.019',
       '--cfl=.09','--max-core-shift=.10','--max-vorticity-turn=.08',
       '--threads','12','--backends','py,cpp,gpu'])
    assert p['adaptive'] and p['dt_max']==.019 and opts['backends']==['py','cpp','gpu']
    assert p['final_time']==3.0

def test_energy_matrix_csv_and_missing_gpu_block(tmp_path):
    from experiment.science import run_suite
    root=Path(__file__).parents[1]
    res=run_suite(root,'PREVIEW',tmp_path/'out',{'grid':16,'grid_up':24,'dt':.03,'t_end':.03,
                             'knots':['0_1'],'threads':1})
    mat=tmp_path/'out'/'0_1_base_energy_matrix.csv'
    assert mat.exists()
    with mat.open(newline='') as f:
        rows=list(csv.DictReader(f))
    assert rows and 'numerical_loss_donor_J' in rows[0]
    assert 'E_donor_run_J' in rows[0]
    if not probe_backend('gpu',root)['available']:
        with pytest.raises(RuntimeError,match='Required backend unavailable'):
            run_matrix(root,'PREVIEW',tmp_path/'matrix',{'grid':16,'grid_up':24,
                  'dt':.03,'t_end':.03,'knots':['0_1'],
                  'backends':['py','gpu'],'require_all_backends':True})
