from sst_qhp_falsifier.analyze import line_crossings


def _row(q,F,Fs,proj=1.0,cond=1.0):
    return {
        'candidate_id':f'c{q}','family_blind':'F','replicate':'0',
        'q':q,'h':0.0,'p':0.0,
        'F_q':F,'F_h':0.0,'F_p':0.0,
        'Fshort_q':Fs,'Fshort_h':0.0,'Fshort_p':0.0,
        'projection_fraction':proj,'short_projection_fraction':proj,
        'basis_correlation_condition_number':cond,
    }


def test_restoring_zero_crossing_requires_actual_short_crossing_and_agreement():
    rr=[_row(-1.0,1.0,0.9),_row(1.0,-1.0,-0.9)]
    z=line_crossings(rr,'q',{'min_projection_fraction':0.05})
    assert len(z)==1
    assert z[0]['restoring']
    assert z[0]['short_sign_crossing']
    assert z[0]['short_restoring']
    assert z[0]['confirmed_restoring']


def test_negative_short_slope_without_short_zero_is_not_confirmation():
    rr=[_row(-1.0,1.0,-1.0),_row(1.0,-1.0,-2.0)]
    z=line_crossings(rr,'q',{'min_projection_fraction':0.05})
    assert len(z)==1
    assert z[0]['restoring']
    assert z[0]['Fshort_slope']<0
    assert not z[0]['short_sign_crossing']
    assert not z[0]['short_restoring']
    assert not z[0]['confirmed_restoring']


def test_low_projection_blocks_crossing_confirmation():
    rr=[_row(-1.0,1.0,1.0,proj=0.01),_row(1.0,-1.0,-1.0,proj=0.01)]
    z=line_crossings(rr,'q',{'min_projection_fraction':0.05})
    assert len(z)==1
    assert z[0]['restoring'] and z[0]['short_restoring']
    assert not z[0]['projection_qualified']
    assert not z[0]['confirmed_restoring']
