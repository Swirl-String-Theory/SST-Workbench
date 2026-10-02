from sst_qhp_falsifier.analyze import line_crossings

def test_restoring_zero_crossing_detected_and_short_confirmed():
    rr=[]
    for q in (-1.0,0.0,1.0):
        # F_q=-q: stable crossing at q=0; short-time estimate same sign.
        rr.append({'candidate_id':f'c{q}','family_blind':'F','replicate':'0','q':q,'h':0.0,'p':0.0,
                   'F_q':-q,'F_h':0.0,'F_p':0.0,'Fshort_q':-.9*q,'Fshort_h':0.0,'Fshort_p':0.0,
                   'projection_fraction':1.0,'short_projection_fraction':1.0})
    z=line_crossings(rr,'q',{})
    assert z
    assert any(abs(x['root_coordinate'])<1e-12 and x['restoring'] and x['short_restoring'] for x in z)
