"""Mathematical regression and characterization, not physical validation."""
import numpy as np
from src.filaments import fit,velocity,run_pair
from src.geometry import generate
from src.external_links import generate_imported
from src.qualify_links import qualify_imported

def test_exact_free_translation_rotation():
    pts=generate(2,3,.23,128)
    x=pts[0];cen=x.mean(axis=0);U=np.array([.4,-.2,.7]);omega=np.array([.3,-.7,.6])
    v=[U+np.cross(omega,x-cen)]
    f=fit(pts,v,mode='free',weighting='arclength')
    assert f['relative_residual']<1e-12
    assert np.allclose(f['Omega_vector'],omega,atol=1e-12)
    assert np.allclose(f['U_vector'], U+np.cross(omega,np.asarray(f['weighted_center'])-cen),atol=1e-12)

def test_free_residual_rigid_rotation_invariant():
    parts,_=generate_imported('BORRO_BALANCED',128)
    v=velocity(parts,.04,[1/3]*3)
    p=fit(parts,v,mode='free',weighting='arclength')
    # proper non-axis rotation and translation, same transformed induced velocity
    axis=np.array([1.,2.,-1.]);axis/=np.linalg.norm(axis);theta=.61
    c=np.cos(theta);s=np.sin(theta)
    K=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
    Q=np.eye(3)+s*K+(1-c)*(K@K)
    rotated=[x@Q.T+np.array([1.3,-.7,.1]) for x in parts]
    rv=[w@Q.T for w in v]
    f=fit(rotated,rv,mode='free',weighting='arclength')
    assert abs(f['relative_residual']-p['relative_residual'])<1e-12
    # Compare axial fit is expected not to be rotation-invariant.
    assert abs(fit(rotated,rv,'axial','arclength')['relative_residual']-fit(parts,v,'axial','arclength')['relative_residual'])>1e-4

def test_six_param_never_worse_than_axial_identical_weights():
    parts,_=generate_imported('BORRO_FLAT',128)
    v=velocity(parts,.06,[1/3]*3)
    for wt in ('vertex','arclength'):
        assert fit(parts,v,'free',wt)['relative_residual']<=fit(parts,v,'axial',wt)['relative_residual']+1e-12

def test_mode_axial_legacy_compatibility():
    p=generate(2,3,.21,96);v=velocity(p,.03)
    f=fit(p,v,mode='axial',weighting='vertex')
    x=p[0];vv=v[0]
    A=np.column_stack((np.tile([0,0,1],(len(x),1)).ravel(),np.column_stack((-x[:,1],x[:,0],np.zeros(len(x)))).ravel()))
    a=np.linalg.lstsq(A,vv.ravel(),rcond=None)[0]
    r=np.linalg.norm(A@a-vv.ravel())/np.linalg.norm(vv.ravel())
    assert abs(r-f['relative_residual'])<1e-12

def test_compare_exports_both_fits():
    a,_=generate_imported('BORRO_BALANCED',96)
    b,_=generate_imported('BORRO_BALANCED',96,True)
    r=run_pair(a,b,3.4,points=64,steps=1,T=.0003,fit_mode='compare')
    assert 'init_nominal_axial' in r and 'init_nominal_free' in r
    assert r['fit_mode_selected']=='free'
    assert r['init_nominal_free']<=r['init_nominal_axial']+1e-12
    assert len(r['initial_nominal_fit']['U_vector'])==3

def test_provenance_three_component_qualification():
    q=qualify_imported('BORRO_5_5_6_TIGHT')
    assert q['milnor_mu123']=='UNRESOLVED'
    assert q['sources']['original']['geometry']['point_counts']==[2275,2109,2048]
    assert q['sources']['reference']['geometry']['point_counts']==[1137,1054,1024]
    assert len(q['sources']['original']['pairwise_gauss_N256'])==3
    assert q['source_resolution_comparison']['reference_is_distinct_source']

def test_sparse_source_flagged():
    q=qualify_imported('BORRO_FLAT')
    assert q['sources']['original']['geometry']['point_counts']==[38,34,33]
    assert q['source_resolution_comparison']['status']=='NO_INDEPENDENT_REFERENCE_SOURCE'
