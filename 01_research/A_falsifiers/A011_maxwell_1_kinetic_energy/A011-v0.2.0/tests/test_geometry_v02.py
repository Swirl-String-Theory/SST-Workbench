from pathlib import Path
import numpy as np
from maxwell_sst_falsifier.geometry import load_curves, resample_uniform, centered_unit_rms
from maxwell_sst_falsifier.modes import generate_mode_candidates, decompose_rigid_velocity

ROOT=Path(__file__).resolve().parents[1]

def test_vect_import_and_resample():
    rec=load_curves(ROOT/'examples'/'synthetic_knots'/'circle.vect')[0]
    assert rec.closed and rec.points.shape[1]==3
    q=resample_uniform(rec.points,128,True)
    assert q.shape==(128,3)
    seg=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
    assert seg.std()/seg.mean() < 1e-3

def test_mode_candidates_are_rigid_projected():
    rec=load_curves(ROOT/'examples'/'synthetic_knots'/'trefoil_T2_3.vect')[0]
    q,_,_=centered_unit_rms(resample_uniform(rec.points,192,True))
    modes=generate_mode_candidates(q,4)
    assert len(modes)>=8
    # Unit normalized deformation vectors.
    assert abs(np.linalg.norm(modes[0].vector)-1.0)<1e-10

def test_rigid_velocity_decomposition_translation():
    rec=load_curves(ROOT/'examples'/'synthetic_knots'/'circle.vect')[0]
    p=resample_uniform(rec.points,64,True)
    v=np.tile(np.array([2.0,-1.0,0.5]),(len(p),1))
    d=decompose_rigid_velocity(p,v)
    assert d['translation_fraction'] > 0.999999999
    assert d['shape_fraction'] < 1e-20
