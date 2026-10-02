from pathlib import Path
import json
import os
import numpy as np

from sst_triadic import reference, backend

if backend.backend_name() != "native":
    raise SystemExit("SST_BACKEND=native is required for parity qualification")

ROOT = Path(__file__).resolve().parent
BLIND = ROOT.parent / "A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs" / "BLIND"
CFG = json.loads((ROOT / "configs" / "default.json").read_text(encoding="utf-8"))
tol = float(CFG["tolerances"]["backend_parity_max_abs"])

rng = np.random.default_rng(int(CFG["seed"]) + 991)
grad = rng.normal(size=(257, 3, 3))
grad[:, 2, 2] = -(grad[:, 0, 0] + grad[:, 1, 1])
u = rng.normal(size=(257, 3))

s_ref, w_ref, d_ref = reference.decompose_gradient(grad)
s_nat, w_nat, d_nat = backend.decompose_gradient(grad)
i_ref = reference.invariants(u, w_ref, s_ref)
i_nat = backend.invariants(u, w_nat, s_nat)

kernel_errors = {
    "strain_max_abs": float(np.max(np.abs(s_nat - s_ref))),
    "vorticity_max_abs": float(np.max(np.abs(w_nat - w_ref))),
    "divergence_max_abs": float(np.max(np.abs(d_nat - d_ref))),
}
for k in i_ref:
    kernel_errors[f"invariant_{k}_max_abs"] = float(np.max(np.abs(i_nat[k] - i_ref[k])))

py_summary = json.loads((BLIND / "python_backend" / "blind_summary.json").read_text(encoding="utf-8"))
nat_summary = json.loads((BLIND / "native_backend" / "blind_summary.json").read_text(encoding="utf-8"))

# Compare common scalar measurements recursively, excluding backend label.
def flatten_numeric(obj, prefix=""):
    out = {}
    if isinstance(obj, bool):
        out[prefix] = float(obj)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out[prefix] = float(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k == "backend":
                continue
            p = f"{prefix}.{k}" if prefix else k
            out.update(flatten_numeric(v, p))
    return out

fp = flatten_numeric(py_summary)
fn = flatten_numeric(nat_summary)
common = sorted(set(fp) & set(fn))
summary_errors = {k: abs(fp[k] - fn[k]) for k in common}
summary_max = max(summary_errors.values(), default=0.0)
max_kernel = max(kernel_errors.values(), default=0.0)
status = "PASS" if max(max_kernel, summary_max) <= tol else "FAIL"

result = {
    "status": status,
    "tolerance_max_abs": tol,
    "python_status": py_summary["overall_status"],
    "native_status": nat_summary["overall_status"],
    "kernel_errors": kernel_errors,
    "summary_numeric_max_abs": summary_max,
    "summary_numeric_compared_count": len(common),
}
(BLIND / "backend_parity_summary.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8"
)
print(json.dumps(result, indent=2))
if status != "PASS":
    raise SystemExit(1)
