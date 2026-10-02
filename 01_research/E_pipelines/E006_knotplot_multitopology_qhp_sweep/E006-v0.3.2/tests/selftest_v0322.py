from pathlib import Path
import sys,json,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qhp_sweep.kpc import topology_probe_script
from qhp_sweep.model import topology_list

t=topology_list("","2.2.1","",300,None)[0]
d=t.__dict__
s=topology_probe_script(d)
assert s.count("load 2.2.1")==2
assert "keep 0" in s and "keep 1" in s
assert "__comp000.txt" in s and "__comp001.txt" in s

t=topology_list("","6.3.2","",300,None)[0]
s=topology_probe_script(t.__dict__)
assert s.count("load 6.3.2")==3
assert all(f"keep {i}" in s for i in range(3))
assert all(f"__comp{i:03d}.txt" in s for i in range(3))

t=topology_list("","","6.9",300,None)[0]
s=topology_probe_script(t.__dict__)
assert s.count("torus 6 9 900")==3
assert all(f"keep {i}" in s for i in range(3))

print("v0.3.2.2 COMPONENT PROBE SELFTEST PASS")
print("2.2.1 -> reload/keep/export x2")
print("6.3.2 -> reload/keep/export x3")
print("torus 6.9 -> reconstruct/keep/export x3")
