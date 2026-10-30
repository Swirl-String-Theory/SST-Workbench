"""Science-backend implementation hook. BLOCKED until 2 distinct real kernels exist.

Record schema for each implemented category (py / cpp / gpu):
  executed: true
  actual_backend: python | pybind11 | torch_xpu | torch_cuda
  source_path: path to actually executed scientific implementation under instance root
  source_sha256: SHA-256 of source_path
  evidence_path: relative to run output root, e.g. backend_science/py.json
  evidence_sha256: SHA-256 of the freshly written JSON evidence file
  input_sha256: exact hash of shared initial conditions / geometry / solver config
  observable: finite numeric vector, identical to evidence['observable']
Evidence JSON must also include actual_backend, executed, input_sha256,
precision, physical_final_time (null for static geometry diagnostics).
C++ additionally needs evidence.compiled_binary_sha256 matching a preflight-discovered
pybind11 native module. GPU evidence needs device_type: xpu or cuda.

The framework checks file hashes and identity. Scientific correctness, convergence,
and independent cross-source evidence still need falsifier-specific gates.
Never return pre-filled PASS or simulate native/GPU execution from Python.
"""
from sst_falsifier import progress

def run_backend_matrix(*,root,cfg,mode,output_dir,devices):
    # Replace each body with an ACTUAL scientific kernel and signed execution
    # evidence before freezing. Placeholders are always unqualified.
    records = {}
    for index,kind in enumerate(('py','cpp','gpu'),start=1):
        with progress.phase('BACKEND',completed=index-1,total=3,backend=kind):
            records[kind]={'executed':False,'reason':'scientific kernel not implemented'}
    return records
