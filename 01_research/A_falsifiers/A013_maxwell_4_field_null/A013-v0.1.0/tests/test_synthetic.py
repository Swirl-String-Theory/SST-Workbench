from maxwell_sst.audits import run_demo

def test_demo_software_controls():
    r={x['id']:x for x in run_demo(None)}
    for k in ['T01','T02','T03','T04','T05','T06']:
        assert r[k]['status']=='PASS', (k,r[k])
    assert r['T07']['status'] in ('REJECTED_NEGATIVE_CONTROL','PASS')
