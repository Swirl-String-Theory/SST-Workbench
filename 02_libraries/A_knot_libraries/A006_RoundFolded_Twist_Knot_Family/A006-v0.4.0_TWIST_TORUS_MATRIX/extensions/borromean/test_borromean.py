"""Self-tests; does not claim physical or triple-link certification."""
import argparse,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_borromean import encode,decode,skeleton,locate_seed,gauss,geometry

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);x=p.parse_args()
    q=skeleton(n_event=32)
    assert len(q)==3 and all(len(s)==192 for s in q)
    assert all(np.array_equal(a,b) for a,b in zip(q,decode(encode(q))))
    link=[gauss(q[i],q[j]) for i,j in ((0,1),(0,2),(1,2))]
    assert max(map(abs,link))<.025,link
    for knot in ('5_2','6_1'):
        arr,source=locate_seed(x.root,knot,1024)
        assert len(arr)==1024,source
    print('PASS: KPT codec, 3-braid closure, numerical pairwise linking, native v0.4.0 seed discovery')
    print('NOT CERTIFIED: independent 5_2/6_1 invariants after splice, Milnor mu123, Euler/PKLSA dynamics')
if __name__=='__main__':main()
