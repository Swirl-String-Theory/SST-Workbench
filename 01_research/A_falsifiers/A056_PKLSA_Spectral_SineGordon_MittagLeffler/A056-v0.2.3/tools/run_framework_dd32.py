from pathlib import Path
import os,subprocess,sys,shutil
ROOT=Path(__file__).resolve().parents[1]
loc=(ROOT/'.sst_framework_root').read_text(encoding='utf-8').strip(); fw=Path(os.environ.get('SST_FALSIFIER_FRAMEWORK_ROOT','')) if os.environ.get('SST_FALSIFIER_FRAMEWORK_ROOT') else (ROOT/loc).resolve()
py=Path(sys.executable)
cmd=[str(py),str(fw/'tools/backend_selftest.py'),'--allow-sycl-fp32','--skip-cpp','--json',str(ROOT/'build/DD32_PARITY_SMOKE.json')]
raise SystemExit(subprocess.call(cmd,cwd=str(fw)))
