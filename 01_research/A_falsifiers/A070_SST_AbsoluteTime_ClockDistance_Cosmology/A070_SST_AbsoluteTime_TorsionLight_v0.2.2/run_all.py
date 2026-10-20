import sys
from src.blind_engine import run_blind, verify_lock, selftest
from src.axial_gate import run as run_axial, verify as verify_axial
mode=sys.argv[1].upper() if len(sys.argv)>1 else 'AXIAL'
if mode=='SELFTEST': selftest()
elif mode=='BLIND': print(run_blind())
elif mode=='VERIFY': print(verify_lock())
elif mode=='AXIAL': print(run_axial())
elif mode=='AXIAL_VERIFY': print(verify_axial())
else: raise SystemExit('Usage: python run_all.py SELFTEST|BLIND|VERIFY|AXIAL|AXIAL_VERIFY')
