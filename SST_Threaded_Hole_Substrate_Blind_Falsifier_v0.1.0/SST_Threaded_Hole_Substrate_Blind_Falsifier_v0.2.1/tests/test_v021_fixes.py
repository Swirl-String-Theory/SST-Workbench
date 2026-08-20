from pathlib import Path
import json
import numpy as np
from sst_threaded_hole_falsifier.model import CurveSet
from sst_threaded_hole_falsifier.dynamics import physical_gap,cfl_dt
from sst_threaded_hole_falsifier.pressure import free_space_potential_from_source
from sst_threaded_hole_falsifier.phase import helix_phase
from sst_threaded_hole_falsifier.generators import threaded_racetrack
from sst_threaded_hole_falsifier.prepare import prepare


def circle(r=1.0,n=64,z=0.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[r*np.cos(t),r*np.sin(t),np.full(n,z)]


def test_zero_gamma_ghost_excluded_from_contact():
    carrier=circle(1.0,64);ghost=circle(.1,32,z=.001)+np.array([1.0,0,0]);cs=CurveSet.from_components([carrier,ghost])
    g=physical_gap(cs,[1.0,0.0],3);g0=physical_gap(CurveSet.from_components([carrier]),[1.0],3)
    assert abs(g-g0)<1e-12


def test_zero_gamma_ghost_excluded_from_cfl():
    carrier=circle(1.0,64);tiny=circle(.01,96,z=3.0);cs=CurveSet.from_components([carrier,tiny])
    a=cfl_dt(cs,[1.0,0.0],.035,dt_max=.01);b=cfl_dt(CurveSet.from_components([carrier]),[1.0],.035,dt_max=.01)
    assert abs(a-b)<1e-12


def test_free_space_green_recovers_one_over_r():
    src=np.array([[0.,0.,0.]]);val=np.array([1.]);samples=np.array([[2.,0,0],[4.,0,0]])
    p=free_space_potential_from_source(samples,src,val,1.0,0.0)
    assert p[0]<0 and p[1]<0
    assert abs((p[0]/p[1])-2.0)<1e-12


def test_geometric_helix_phase_survives_marker_independence():
    ref=threaded_racetrack((0,0,1),(0.08,0),1.0,.02,2.6,3.4,160);ang=.37;R=np.array([[np.cos(ang),-np.sin(ang),0],[np.sin(ang),np.cos(ang),0],[0,0,1.]])
    mov=ref@R.T;ph=helix_phase(ref,mov)
    assert np.isfinite(ph)
    assert abs(np.angle(np.exp(1j*(ph-ang))))<.12


def test_confirmatory_pair_specs_make_four_pairs(tmp_path):
    root=Path(__file__).resolve().parents[1];cfg=root/'config'/'preset_confirmatory_stability.json';out=tmp_path/'campaign';m=prepare(root,out,cfg)
    assert m['n_pairs']==4
