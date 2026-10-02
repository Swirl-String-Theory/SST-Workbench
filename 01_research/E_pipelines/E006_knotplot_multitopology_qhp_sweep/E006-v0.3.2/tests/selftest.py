from pathlib import Path
import sys,json,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qhp_sweep.model import *
from qhp_sweep.cli import parser,build
from qhp_sweep.kpc import write_scripts,audit_scripts

tops=topology_list("3.1,5.1,7.1","6.3.3,6.3.1","3.3,3.6,3.9,6.9,6.15,6.21",300,None)
assert len(tops)==11
D={(t.kind,t.spec):(t.components,t.nbeads) for t in tops}
assert D[("knot","3.1")]==(1,300)
assert D[("link","6.3.3")]==(3,900)
assert D[("torus","3.6")]==(3,900)
assert D[("torus","6.9")]==(3,900)
s=qhp_states((42,1.43,6.2),(44,1.47,6.32),"line",20,(5,5,5))
assert len(s)==20
g=qhp_states((1,1,1),(2,2,2),"grid",20,(3,4,5))
assert len(g)==60
cp=auto_checkpoints(100000)
assert cp[0]==0 and cp[-1]==100000 and 10000 in cp
print("MODEL SELFTEST PASS: 11 topologies, 20-line sweep => 220 runs")
print("100k checkpoints:",cp)
