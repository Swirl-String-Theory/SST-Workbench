from maxwell_sst.audits import run_demo
from native_ext import backend_info
r=run_demo(); print(backend_info()); print({x['id']:x['status'] for x in r})
