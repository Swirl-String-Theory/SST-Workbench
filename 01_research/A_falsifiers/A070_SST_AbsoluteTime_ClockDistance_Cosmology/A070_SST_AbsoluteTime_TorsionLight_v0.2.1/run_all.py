import sys
from src.blind_engine import run_blind, verify_lock, selftest
mode=sys.argv[1].upper() if len(sys.argv)>1 else 'BLIND'
if mode=='SELFTEST': selftest()
elif mode=='BLIND': print(run_blind())
elif mode=='VERIFY': print(verify_lock())
else: raise SystemExit('Usage: python run_all.py SELFTEST|BLIND|VERIFY')
