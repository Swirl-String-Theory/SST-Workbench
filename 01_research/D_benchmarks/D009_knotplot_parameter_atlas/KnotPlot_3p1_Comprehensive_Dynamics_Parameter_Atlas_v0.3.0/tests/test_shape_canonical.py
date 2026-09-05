from pathlib import Path
import sys, numpy as np, subprocess, json

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import shape_canonical_analysis as sc

# Correct row-vector Kabsch: rigid rotation+translation must vanish.
t=np.linspace(0,2*np.pi,96,endpoint=False)
a=np.c_[1.7*np.cos(t),0.8*np.sin(t),0.15*np.sin(3*t)]
q=np.array([[0,-1,0],[1,0,0],[0,0,1]],float)
b=a@q + np.array([3.2,-1.1,4.7])
assert sc.kabsch_rms(a,b)<1e-11, sc.kabsch_rms(a,b)

# Closed arclength + cyclic phase must remove pure bead-phase shift.
arc=sc.closed_arclength_resample(a,96)
shifted=np.roll(arc,23,axis=0)
raw=sc.kabsch_rms(arc,shifted)
shape,phase,rev=sc.phase_kabsch_rms(arc,shifted,allow_reverse=False)
assert raw>1e-3, raw
assert shape<1e-11, (shape,phase)
assert rev is False

# Genuine shape change remains.
c=np.c_[2.2*np.cos(t),0.8*np.sin(t),0.15*np.sin(3*t)]
carc=sc.closed_arclength_resample(c,96)
shape2,_,_=sc.phase_kabsch_rms(arc,carc,allow_reverse=False)
assert shape2>1e-3, shape2

# Orientation reversal is not silently allowed.
rev_arc=arc[::-1].copy()
shape3,_,rev3=sc.phase_kabsch_rms(arc,rev_arc,allow_reverse=False)
assert rev3 is False

# Bridge and discovery launchers exist.
for fn in (
    "run_50_shape_canonical_extended.cmd",
    "run_60_prepare_sst_stability_handoff.cmd",
    "run_70_discover_sst_v048_interface.cmd",
    "run_reanalyze_shape_and_prepare_stability.cmd",
):
    assert (ROOT/fn).is_file(), fn

print("SHAPE-CANONICAL SELFTEST PASS: corrected row-Kabsch + arclength resampling + cyclic phase gate")
