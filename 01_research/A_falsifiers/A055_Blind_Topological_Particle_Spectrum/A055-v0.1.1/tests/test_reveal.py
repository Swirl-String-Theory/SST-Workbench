import math
from a055_spectrum.features import FEATURE_REGISTRY
from a055_spectrum.reveal import _null_distribution


def test_feature_domains():
    assert FEATURE_REGISTRY["linking_strength"]["ratio_pools"] == ["links"]
    assert "all" not in FEATURE_REGISTRY["abs_writhe"]["ratio_pools"]
    assert FEATURE_REGISTRY["contact_ratio"]["diagnostic_only"] is True


def test_null_envelope_matches_bruteforce():
    cache=[]
    for j,xs in enumerate([(-2.0,-0.4,2.4),(-1.7,0.2,1.5),(-2.6,0.9,1.7),(-1.2,-0.1,1.3)]):
        xm=sum(xs)/3.0
        c=[x-xm for x in xs]
        cache.append((c[0],c[1],c[2],xm,f"a{j}",f"b{j}",f"c{j}",1.0,2.0,3.0))
    tvals=[i/20.0 for i in range(21)]
    vals,_=_null_distribution(cache,[1.0,7.0,100.0],tvals)
    span=math.log(100.0)
    for t,e in zip(tvals,vals):
        tv=[0.0,t*span,span]
        tm=sum(tv)/3.0
        tc=[x-tm for x in tv]
        brute=min(math.sqrt(sum((c[i]-tc[i])**2 for i in range(3))/3.0) for c in cache)
        assert abs(e-brute)<1e-10
