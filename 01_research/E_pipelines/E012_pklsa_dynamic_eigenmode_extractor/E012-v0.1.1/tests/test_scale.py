from e012_dynamic.scale import validate_scale_contract, make_physical_candidate

BRANCH={"samples":[
 {"mode_m":1,"kD":1.0,"omega_hat":2.0},
 {"mode_m":2,"kD":2.0,"omega_hat":4.5},
 {"mode_m":3,"kD":3.0,"omega_hat":7.5},
]}

def test_scale_contract_blocked_when_missing():
    ok,reasons=validate_scale_contract(None,[1,2,3])
    assert not ok and "NO_PHYSICAL_SCALE_CONTRACT" in reasons

def test_physical_candidate_dimensions():
    c={
      "approved":True,
      "derived_without_GRB_target_fit":True,
      "D_m":2.0,
      "Gamma_m2_s":8.0,
      "energy_mapping":[
        {"mode_m":1,"energy_TeV":1.0},
        {"mode_m":2,"energy_TeV":2.0},
        {"mode_m":3,"energy_TeV":3.0},
      ],
      "scale_provenance":"unit-test",
    }
    out,reasons=make_physical_candidate(BRANCH,c)
    assert not reasons
    assert out["k"]==[0.5,1.0,1.5]
    assert len(out["omega"])==3
