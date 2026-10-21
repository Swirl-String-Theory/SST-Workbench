import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pytest
from scipy.spatial.distance import cdist
from smooth_clasp import PROFILES,fold_map,resample_periodic_c2
from tikz_roundfold import dense_xyz
from near_unknot import approximate_curvature
from clearance import _segment_distance,global_min_nonlocal
from build import topology,script_preset,ROOT,CLOSE,MAX_DR
from knotplot_io import encode,decode

@pytest.mark.parametrize('label,det,crossings',[('5_2',7,5),('6_1',9,6)])
@pytest.mark.parametrize('profile',list(PROFILES))
def test_topology_and_clearance(label,det,crossings,profile):
    base,_=dense_xyz(label,width=.020,height=.10)
    mapped,info=fold_map(base,profile)
    assert info['alpha_min']>0
    x=resample_periodic_c2(mapped,256)
    t=topology(x,label)
    assert (t['crossings'],t['determinant'])==(crossings,det)
    assert global_min_nonlocal(x)['distance']>1.10*CLOSE
    assert np.array_equal(x,decode(encode([x]))[0])

def test_radial_map_monotonic():
    # Fixed theta in bottom region: radial order preserved.
    from smooth_clasp import fold_map
    from near_unknot import params
    base,_=dense_xyz('5_2')
    c,R,_=params(base)
    # Preserve input angle for all vertices, except numeric rounding.
    x,_=fold_map(base,'TIGHT')
    before=np.angle((base[:,0]-c[0])+1j*(base[:,1]-c[1]))
    after=np.angle((x[:,0]-c[0]*30)+1j*(x[:,1]-c[1]*30))
    assert np.max(np.abs(np.angle(np.exp(1j*(after-before)))))<1e-9

def test_user_preset_is_nondestructive():
    s=script_preset()
    for v in ('show backdrop','mode cbf','bradius = 0.2','cradius = 0.1',
              'tanf = on','tanmag = 9','stusplit = 0','dstep = 1',
              'close = 0.20','max-dr = 0.02'):
        assert v in s
    assert 'fitto' not in s
    assert MAX_DR<CLOSE

def test_segment_distance_crossing_and_nonlocal():
    a=np.array([0.,0.,0.]);b=np.array([1.,0.,0.])
    c=np.array([.5,-1.,.1]);d=np.array([.5,1.,.1])
    assert abs(_segment_distance(a,b,c,d)-.1)<1e-10

def test_rounded_lift_reduces_max_curvature_for_both():
    from near_unknot import annulus_squeeze,params
    from tikz_roundfold import resample3
    for label in ['5_2','6_1']:
        older,_=dense_xyz(label,width=.011,height=.10)
        c,R,_=params(older)
        old=resample3(annulus_squeeze(older,.12,2.50,c,R),512)*12
        candidate,_=fold_map(dense_xyz(label,width=.020,height=.10)[0],'BALANCED')
        new=resample_periodic_c2(candidate,512)
        assert approximate_curvature(new).max() < approximate_curvature(old).max()

def test_rc_aliases_are_unique_and_patched():
    import re
    rc=(ROOT/'presets/knotplotrc_v023_COMPLETE.kps').read_text()
    assert 'SST-SMOOTHCLASP-v0.2.3 BEGIN' in rc
    defined=re.findall(r'^alias\s+([^ ]+)\s+',rc,flags=re.M)
    assert len(defined)==len(set(defined)), 'Duplicate aliases could silently shadow the new version'
    for name in ['52S512','52B512','52Q512','61S512','61B512','61Q512','52N512','61T512']:
        assert name in defined
    assert 'NearUnknot_5_2_NEAR_UNKNOT_N0512' not in rc


def test_generated_kpc_files_preserve_scale_and_setting():
    # The complete release is built before packaging. Verify generated entrypoints.
    for label in ['5_2','6_1']:
        for profile in PROFILES:
            name=f'SmoothClasp_{label}_{profile}_N0512'
            d=ROOT/'output/individual'/name
            kpc=(d/f'{name}_LOAD.kpc').read_text()
            for s in ['reset all','show backdrop','mode cbf',
                      'close = 0.20','max-dr = 0.02',f'load output/individual/{name}/{name}.kpt']:
                assert s in kpc
            assert 'fitto' not in kpc
            assert (d/f'{name}_GO32.kpc').read_text().strip()=='go 32'