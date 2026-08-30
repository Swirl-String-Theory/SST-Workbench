from pathlib import Path
import sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qhp_sweep.model import *
assert is_unlink_control("link","0.2.1")
assert is_unlink_control("link","0.3.1")
assert not is_unlink_control("link","2.2.1")
c,a=synthesize_unlink_components(2,600,12)
assert len(c)==2 and a["allocated_beads"]==[300,300]
c,a=synthesize_unlink_components(3,900,12)
assert len(c)==3 and a["allocated_beads"]==[300,300,300]
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"u.txt"
    write_multicomponent_coords(p,c)
    cc=parse_multicomponent_coords(p)
    assert len(cc)==3
print("v0.3.2.1 UNLINK SELFTEST PASS")
