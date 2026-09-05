from pathlib import Path
import sys,tempfile,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qhp_sweep.model import allocate_beads_by_length,resample_closed_component,write_multicomponent_coords,parse_multicomponent_coords,closed_arclength,topology_list

assert allocate_beads_by_length([1,2],600,12)==[200,400]
assert sum(allocate_beads_by_length([1,1,1],900,12))==900
a=allocate_beads_by_length([1,2,3],900,12)
assert a==[150,300,450],a

tops=topology_list("","7.2.1","",300,None)
assert len(tops)==1 and tops[0].components==2 and tops[0].nbeads==600

# synthetic unequal circles: circumference ratio ~1:2
u=np.linspace(0,2*np.pi,120,endpoint=False)
c1=np.c_[np.cos(u),np.sin(u),np.zeros_like(u)]
c2=np.c_[2*np.cos(u),2*np.sin(u),np.ones_like(u)]
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"x.txt";write_multicomponent_coords(p,[c1,c2])
    cc=parse_multicomponent_coords(p)
    L=[closed_arclength(x) for x in cc]
    alloc=allocate_beads_by_length(L,600,12)
    assert alloc==[200,400],(L,alloc)
print("v0.3.1 BEAD ALLOCATION SELFTEST PASS: 1:2 length -> 200:400 of 600")
print("7.2.1 inferred: 2 components -> total budget 600")
