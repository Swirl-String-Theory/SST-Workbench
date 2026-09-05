from maxwell_sst.audits import run_demo
def test_demo_discriminates():
    r=run_demo(); s={x['id']:x['status'] for x in r}
    assert s['T01']=='PASS' and s['T02']=='PASS' and s['T03']=='PASS' and s['T04']=='PASS' and s['T05']=='PASS' and s['T06']=='PASS'
    assert s['T07']=='REJECTED_NEGATIVE_CONTROL'
