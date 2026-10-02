# # SSTcore v0.8.2 — Google Colab Geometry Probe
# 
# This notebook installs `SSTcore==0.8.2`, checks the available Python/native bindings, computes the canonical SST meson anchor, probes selected knot/link geometries, and optionally appends a new `SSTcore_Geometry_Probe` sheet to an uploaded falsification workbook.
# 
# **Scope.** This notebook does **not** assign final SST particle topologies. It only prepares the computational layer needed for a falsification matrix.
# 
# Recommended runtime: **Google Colab CPU**.
# In a notebook/Colab run: %pip install -q --upgrade SSTcore==0.8.2 pandas openpyxl numpy matplotlib

import sys
import platform
import re
import math
from pathlib import Path
from pprint import pprint

import numpy as np
import pandas as pd
import importlib.metadata as md

import SSTcore as sst

print("Python:", sys.version)
print("Platform:", platform.platform())
print("SSTcore distribution version:", md.version("SSTcore"))
print("SSTcore module path:", getattr(sst, "__file__", None))


# Canonical constants used in the current SST meson / mass-functional work.
c = 299_792_458.0  # m/s

v_swirl = 1.09384563e6                 # m/s
r_c = 1.40897017e-15                  # m
rho_f = 7.0e-7                        # kg/m^3
rho_core = 3.8934358266918687e18      # kg/m^3
rho_E = 3.49924562e35                 # J/m^3

J_per_MeV = 1.602176634e-13

omega_c = v_swirl / r_c
Gamma0 = 2.0 * math.pi * r_c * v_swirl
alpha_swirl = 2.0 * v_swirl / c

E_core_J = math.pi * rho_E * r_c**3
E_core_MeV = E_core_J / J_per_MeV

E_M0_J = alpha_swirl * E_core_J
E_M0_MeV = E_M0_J / J_per_MeV

constants_df = pd.DataFrame([
    ("|v_swirl|", v_swirl, "m s^-1"),
    ("r_c", r_c, "m"),
    ("rho_f", rho_f, "kg m^-3"),
    ("rho_core", rho_core, "kg m^-3"),
    ("rho_E", rho_E, "J m^-3"),
    ("omega_c = |v_swirl| / r_c", omega_c, "s^-1"),
    ("Gamma0 = 2*pi*r_c*|v_swirl|", Gamma0, "m^2 s^-1"),
    ("alpha_swirl = 2|v_swirl|/c", alpha_swirl, "dimensionless"),
    ("E_core = pi*rho_E*r_c^3", E_core_MeV, "MeV"),
    ("E_M0 = alpha_swirl*pi*rho_E*r_c^3", E_M0_MeV, "MeV"),
], columns=["quantity", "value", "unit"])

pd.set_option("display.precision", 12)
display(constants_df)

print(f"E_M0 = {E_M0_MeV:.8f} MeV")


public_names = sorted(n for n in dir(sst) if not n.startswith("_"))
print(f"Top-level public names: {len(public_names)}")
for n in public_names:
    print(" ", n)

print("\nNative extension present:", hasattr(sst, "_sst_native"))

if hasattr(sst, "_sst_native"):
    native_names = sorted(n for n in dir(sst._sst_native) if not n.startswith("_"))
    print(f"\nNative public names: {len(native_names)}")
    for n in native_names:
        print(" ", n)

    if hasattr(sst._sst_native, "list_bindings"):
        print("\nNative binding summary:")
        pprint(sst._sst_native.list_bindings())


resource_fns = [
    "get_resources_dir",
    "get_ideal_txt_path",
    "get_knots_fourier_series_dir",
    "get_link_table_path",
]

resource_rows = []
for fn in resource_fns:
    if hasattr(sst, fn):
        try:
            value = getattr(sst, fn)()
            exists = Path(str(value)).exists()
            resource_rows.append((fn, str(value), exists))
        except Exception as exc:
            resource_rows.append((fn, f"ERROR: {type(exc).__name__}: {exc}", False))
    else:
        resource_rows.append((fn, "not exposed", False))

resource_df = pd.DataFrame(resource_rows, columns=["function", "value", "exists"])
display(resource_df)


# These function names are intentionally broad. The notebook tries all functions that may exist
# in different SSTcore releases and records which one worked.
LOOKUP_FUNCTIONS = [
    "get_ideal_ab",
    "get_ideal_link",
    "get_fourier_knot",
    "get_knot",
    "get_knot_by_id",
    "load_knot",
    "load_link",
]

# Conservative fallback reference values from the SSTcore resource probe layer.
# They are used only when SSTcore finds an object but its ropelength is not easily parseable,
# or when you want a placeholder geometry row for notebook testing.
FALLBACK_GEOMETRY = {
    "3:1:1": {"name": "trefoil", "component_count": 1, "crossing_number": 3, "linking_number": 0, "ropelength": 16.371637},
    "4:1:1": {"name": "figure-eight", "component_count": 1, "crossing_number": 4, "linking_number": 0, "ropelength": 21.043322},
    "L2a1": {"name": "Hopf link", "component_count": 2, "crossing_number": 2, "linking_number": 1, "ropelength": 12.566370},
    "L4a1": {"name": "Solomon link", "component_count": 2, "crossing_number": 4, "linking_number": 2, "ropelength": 20.009315},
}

def safe_to_dict(obj):
    """Best-effort object-to-dict conversion."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "_asdict"):
        try:
            return dict(obj._asdict())
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            return dict(obj.__dict__)
        except Exception:
            pass
    return {}

def extract_numeric_geometry(obj):
    """Extract likely geometric values from dict-like objects or strings."""
    out = {}
    d = safe_to_dict(obj)

    key_aliases = {
        "ropelength": ["ropelength", "rope_length", "L", "length", "L_total", "ltot", "Ltot"],
        "crossing_number": ["crossing_number", "crossings", "C", "c"],
        "component_count": ["component_count", "components", "n_components", "num_components"],
        "linking_number": ["linking_number", "lk", "Lk", "linking"],
        "writhe": ["writhe", "Wr"],
        "helicity": ["helicity", "H"],
    }

    for canonical, aliases in key_aliases.items():
        for k in aliases:
            if k in d:
                try:
                    out[canonical] = float(d[k])
                except Exception:
                    out[canonical] = d[k]
                break

    text = str(obj)
    if "ropelength" not in out:
        # Try patterns like L = 16.37, ropelength: 16.37, L_total = 12.56.
        patterns = [
            r"\bropelength\b\s*[:=]\s*([-+0-9.eE]+)",
            r"\brope[_ -]?length\b\s*[:=]\s*([-+0-9.eE]+)",
            r"\bL(?:_total|tot)?\b\s*[:=]\s*([-+0-9.eE]+)",
            r"\blength\b\s*[:=]\s*([-+0-9.eE]+)",
        ]
        for pat in patterns:
            m = re.search(pat, text, flags=re.I)
            if m:
                try:
                    out["ropelength"] = float(m.group(1))
                    break
                except Exception:
                    pass

    return out

def find_topology(topology_id):
    """Try known SSTcore lookup functions and return a structured result."""
    errors = []
    for fn in LOOKUP_FUNCTIONS:
        if not hasattr(sst, fn):
            continue
        try:
            obj = getattr(sst, fn)(topology_id)
            found = obj is not None
            # Treat empty strings/lists/dicts as not found.
            if obj == "" or obj == [] or obj == {}:
                found = False
            if found:
                return {
                    "topology_id": topology_id,
                    "sstcore_found": True,
                    "lookup_function": fn,
                    "object_type": type(obj).__name__,
                    "object_preview": str(obj)[:400],
                    "object": obj,
                    "errors": "",
                }
        except Exception as exc:
            errors.append(f"{fn}: {type(exc).__name__}: {exc}")
    return {
        "topology_id": topology_id,
        "sstcore_found": False,
        "lookup_function": "",
        "object_type": "",
        "object_preview": "",
        "object": None,
        "errors": " | ".join(errors[:5]),
    }


topology_targets = [
    {"candidate_family": "endpoint_knot", "candidate_topology_id": "3:1:1", "candidate_name": "trefoil"},
    {"candidate_family": "endpoint_knot", "candidate_topology_id": "4:1:1", "candidate_name": "figure-eight"},
    {"candidate_family": "minimal_linked_carrier", "candidate_topology_id": "L2a1", "candidate_name": "Hopf link"},
    {"candidate_family": "double_linked_carrier", "candidate_topology_id": "L4a1", "candidate_name": "Solomon link"},
]

records = []
for target in topology_targets:
    tid = target["candidate_topology_id"]
    lookup = find_topology(tid)
    geom = extract_numeric_geometry(lookup["object"])

    fallback = FALLBACK_GEOMETRY.get(tid, {})
    merged = dict(fallback)
    merged.update({k: v for k, v in geom.items() if v not in [None, ""]})

    ropelength = merged.get("ropelength", np.nan)
    component_count = merged.get("component_count", np.nan)
    linking_number = merged.get("linking_number", np.nan)
    crossing_number = merged.get("crossing_number", np.nan)

    records.append({
        **target,
        "sstcore_found": lookup["sstcore_found"],
        "lookup_function": lookup["lookup_function"],
        "object_type": lookup["object_type"],
        "component_count": component_count,
        "crossing_number": crossing_number,
        "linking_number": linking_number,
        "ropelength": ropelength,
        "geometry_source": "SSTcore_extracted" if geom else ("fallback_reference" if fallback else "none"),
        "E_M0_MeV": E_M0_MeV,
        "length_scaled_anchor_MeV": ropelength * E_M0_MeV if pd.notna(ropelength) else np.nan,
        "status": "geometry_probe_only",
        "notes": "No final particle assignment. Use as candidate topology input only.",
        "object_preview": lookup["object_preview"],
        "errors": lookup["errors"],
    })

geometry_probe_df = pd.DataFrame(records)
display(geometry_probe_df)


# This is a sandbox only. It does not represent a finalized SST mass prediction.
# It helps test whether a candidate topology is plausibly too light/heavy under simple loading assumptions.

def linked_energy_estimate(E0_MeV, component_count=2, linking_number=0, lambda_link=0.0, B_chi_MeV=0.0, E_dress_MeV=0.0):
    """
    Toy linked-carrier energy:
        E = (component_count + lambda_link*abs(linking_number)) E0 - B_chi + E_dress
    """
    return (component_count + lambda_link * abs(linking_number)) * E0_MeV - B_chi_MeV + E_dress_MeV

sandbox_rows = []
for _, row in geometry_probe_df.iterrows():
    for lambda_link in [0.0, 0.25, 0.5, 1.0]:
        E_est = linked_energy_estimate(
            E_M0_MeV,
            component_count=int(row["component_count"]) if pd.notna(row["component_count"]) else 1,
            linking_number=float(row["linking_number"]) if pd.notna(row["linking_number"]) else 0.0,
            lambda_link=lambda_link,
            B_chi_MeV=0.0,
            E_dress_MeV=0.0,
        )
        sandbox_rows.append({
            "candidate_topology_id": row["candidate_topology_id"],
            "candidate_name": row["candidate_name"],
            "component_count": row["component_count"],
            "linking_number": row["linking_number"],
            "lambda_link": lambda_link,
            "B_chi_MeV": 0.0,
            "E_dress_MeV": 0.0,
            "toy_energy_MeV": E_est,
            "toy_energy_over_E_M0": E_est / E_M0_MeV,
            "status": "toy_sandbox_not_claim",
        })

energy_sandbox_df = pd.DataFrame(sandbox_rows)
display(energy_sandbox_df)


# Run this cell if you want to append the SSTcore geometry probe to your existing workbook.
# You can upload, for example:
#   PDG_2025_particle_catalog_SST_falsification_skeleton.xlsx

from google.colab import files

uploaded = files.upload()

xlsx_files = [name for name in uploaded.keys() if name.lower().endswith(".xlsx")]
if not xlsx_files:
    raise RuntimeError("No .xlsx file uploaded. Upload the falsification skeleton workbook.")

input_xlsx = xlsx_files[0]
output_xlsx = input_xlsx.replace(".xlsx", "_with_SSTcore_Geometry_Probe.xlsx")

xls = pd.ExcelFile(input_xlsx)

with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
    for sheet in xls.sheet_names:
        df = pd.read_excel(input_xlsx, sheet_name=sheet)
        # Excel sheet names are limited to 31 chars.
        df.to_excel(writer, sheet_name=sheet[:31], index=False)

    geometry_probe_df.to_excel(writer, sheet_name="SSTcore_Geometry_Probe", index=False)
    energy_sandbox_df.to_excel(writer, sheet_name="Energy_Sandbox", index=False)
    constants_df.to_excel(writer, sheet_name="SST_Colab_Constants", index=False)

print("Wrote:", output_xlsx)
files.download(output_xlsx)


standalone_xlsx = "SSTcore_v0_8_2_Colab_Geometry_Probe.xlsx"

with pd.ExcelWriter(standalone_xlsx, engine="openpyxl") as writer:
    constants_df.to_excel(writer, sheet_name="SST_Constants", index=False)
    geometry_probe_df.to_excel(writer, sheet_name="SSTcore_Geometry_Probe", index=False)
    energy_sandbox_df.to_excel(writer, sheet_name="Energy_Sandbox", index=False)

print("Wrote:", standalone_xlsx)

try:
    from google.colab import files
    files.download(standalone_xlsx)
except Exception:
    print("Not running in Colab; file is available locally:", standalone_xlsx)

# ## Interpretation rule
# 
# Use this notebook in three passes:
# 
# 1. **API pass:** verify `SSTcore==0.8.2`, resource paths, and native bindings.
# 2. **Geometry pass:** extract or reference candidate knot/link geometry for `3:1:1`, `L2a1`, `L4a1`, etc.
# 3. **Falsification pass:** append results to the workbook, then later add fixed SST assignment rules and SSTcore energy functionals.
# 
# Do not treat the toy energy sandbox as a final SST mass prediction. It is only a dimensional and organizational scaffold.
