import json, zipfile
from pathlib import Path
from sst_blind.spectral_extension import evaluate_triplet, load_v047_k16_baseline

POL={
 'growth_threshold':0.12,'tail_contraction_ratio_max':0.75,'spectral_relative_tail_max':0.03,
 'dominant_kmax_boundary_weight_max':0.10,'high_k_fraction':0.75,'high_k_fraction_within_kelvin_max':0.05,
 'kelvin_total_weight_min_for_tail_gate':0.05,'extrapolation_p_min':0.25,'extrapolation_p_max':6.0,'extrapolation_p_grid':101,
 'spectral_nyquist_fraction_max':0.75,
}

def R(g,k,boundary=0.005,high=0.001,nyq=0.3):
    # total Kelvin mass 0.5, with tiny high-k tail
    weights={'2':0.20,'3':0.15,'4':0.149}
    weights[str(k)]=boundary
    if k>=8: weights[str(int(0.75*k))]=high
    return {'metrics':{'normalized_growth':g,'spectral_nyquist_fraction':nyq,'spectral_nyquist_safe':nyq<=0.75},
            'dominant_mode_diagnostics':{'requested_k_max':k,'configured_k_max':k,'kmax_basis_present':True,'kmax_boundary_weight':boundary,'kelvin_k_weight':weights}}

def test_resolves_contracting_tail():
    d=evaluate_triplet([16,24,32],[R(.080,16),R(.073,24),R(.070,32)],POL)
    assert d['resolved']
    assert d['growth_verdict']=='PASS'
    assert d['spectral_nyquist_safe']

def test_rejects_high_k_tail():
    a=R(.080,16); b=R(.073,24); c=R(.070,32,boundary=.04,high=.25)
    # ensure high k energy is substantial in the last quarter
    c['dominant_mode_diagnostics']['kelvin_k_weight']['28']=.20
    d=evaluate_triplet([16,24,32],[a,b,c],POL)
    assert not d['resolved']
    assert 'high_k_mode_tail_not_decayed' in d['reasons']

def test_rejects_nyquist_guard():
    d=evaluate_triplet([32,48,64],[R(.080,32),R(.073,48),R(.070,64,nyq=.80)],POL)
    assert not d['resolved']
    assert 'spectral_nyquist_guard_failed' in d['reasons']

def test_v047_zip_baseline_loader(tmp_path):
    root='outputs_hr_ladder_dd32_test/04_R4_N720_K16_SPECTRAL/'
    zpath=tmp_path/'base.zip'
    mapping={'B01':{'source':'knotplot:knot_3.1','sha256':'abc','topology_class':'knot','canonical_id':'3_1'}}
    result={'metrics':{'normalized_growth':.1,'jacobian_reference_eps':.004},'dominant_mode_diagnostics':{'requested_k_max':16},'meta':{'normalized_component_counts':[720]}}
    with zipfile.ZipFile(zpath,'w') as z:
        z.writestr(root+'unblind_manifest.json',json.dumps(mapping))
        z.writestr(root+'pre_unblind/B01_analysis.json',json.dumps(result))
    d=load_v047_k16_baseline(zpath)
    assert d['knotplot:knot_3.1']['result']['metrics']['normalized_growth']==.1
