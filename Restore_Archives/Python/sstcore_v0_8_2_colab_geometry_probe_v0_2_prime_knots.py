# Generated script from SSTcore v0.8.2 Colab notebook v0.2

try:
    display
except NameError:
    def display(x):
        print(x.to_string() if hasattr(x, 'to_string') else x)

# # SSTcore v0.8.2 — Google Colab Geometry Probe v0.2
# 
# This notebook installs `SSTcore==0.8.2`, checks the available Python/native bindings, computes the canonical SST meson anchor, probes selected knot/link geometries, and optionally appends new sheets to a falsification workbook.
# 
# ## v0.2 additions
# 
# - Adds explicit abstract SST meson test classes:
#   - `OPEN_QQBAR`
#   - `SQUARE_KNOT_TENDENCY = 3_1#mirror(3_1)`
#   - `GRANNY_KNOT_TENDENCY = 3_1#3_1`
# - Adds linked-carrier candidates:
#   - `L2a1` Hopf link
#   - `L4a1` Solomon link
# - Adds all first prime-knot table targets up to 10 crossings by default:
#   - \(3_1,\ldots,10_{165}\)
#   - SSTcore AB-style IDs are generated as `n:i:1`, e.g. `3:1:1`, `8:17:1`, `10:165:1`.
# 
# **Scope.** This notebook does **not** assign final SST particle topologies. It only prepares the computational layer needed for a falsification matrix.
# 
# Recommended runtime: **Google Colab CPU**.

#@title 1. Install SSTcore and dependencies
# Install manually if needed:
# python -m pip install --upgrade SSTcore==0.8.2 pandas openpyxl matplotlib


#@title 2. Imports and environment report
import sys, platform, re, math
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


#@title 3. Canonical SST constants and meson anchor

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


#@title 4. Inspect available SSTcore API

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


#@title 5. Resource-path sanity checks

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


#@title 6. Candidate generators: meson classes + first prime knots

# "First prime knots" here means the standard prime knot table through 10 crossings.
# It gives 249 canonical prime-knot targets:
# 3_1, 4_1, 5_1..5_2, ..., 10_1..10_165.
#
# SSTcore AB-style IDs are generated as:
#   n:i:1
# For example:
#   3_1 -> 3:1:1
#   10_165 -> 10:165:1
#
# Change MAX_PRIME_CROSSING to 8 or 9 if you want a shorter test run.
MAX_PRIME_CROSSING = 10

PRIME_KNOT_COUNTS = {
    3: 1,
    4: 1,
    5: 2,
    6: 3,
    7: 7,
    8: 21,
    9: 49,
    10: 165,
}

def build_prime_knot_targets(max_crossing=10):
    rows = []
    for crossing in sorted(PRIME_KNOT_COUNTS):
        if crossing > max_crossing:
            continue
        for index in range(1, PRIME_KNOT_COUNTS[crossing] + 1):
            rows.append({
                "candidate_family": "prime_knot_table",
                "candidate_topology_id": f"{crossing}:{index}:1",
                "candidate_name": f"{crossing}_{index}",
                "abstract_topology_class": False,
                "component_count_expected": 1,
                "crossing_number_expected": crossing,
                "linking_number_expected": 0,
                "chirality_model": "canonical_orientation_only",
                "sst_role_hint": "generic_prime_knot_candidate",
            })
    return rows

MESON_TEST_CLASSES = [
    {
        "candidate_family": "open_mesonic_carrier",
        "candidate_topology_id": "OPEN_QQBAR",
        "candidate_name": "open chirality-paired q-qbar carrier",
        "abstract_topology_class": True,
        "component_count_expected": 1,
        "crossing_number_expected": np.nan,
        "linking_number_expected": 0,
        "chirality_model": "opposite_endpoint_chirality",
        "sst_role_hint": "pion_ground_sector_candidate",
    },
    {
        "candidate_family": "connected_sum_candidate",
        "candidate_topology_id": "SQUARE_KNOT_TENDENCY",
        "candidate_name": "square-knot tendency: 3_1#mirror(3_1)",
        "abstract_topology_class": True,
        "component_count_expected": 1,
        "crossing_number_expected": 6,
        "linking_number_expected": 0,
        "chirality_model": "net_chirality_zero",
        "sst_role_hint": "closed_q_qbar_completion_candidate",
    },
    {
        "candidate_family": "connected_sum_candidate",
        "candidate_topology_id": "GRANNY_KNOT_TENDENCY",
        "candidate_name": "granny-knot tendency: 3_1#3_1",
        "abstract_topology_class": True,
        "component_count_expected": 1,
        "crossing_number_expected": 6,
        "linking_number_expected": 0,
        "chirality_model": "same_chirality_pair",
        "sst_role_hint": "diquark_or_exotic_candidate_not_primitive_meson",
    },
]

CORE_LINK_AND_KNOT_TARGETS = [
    {
        "candidate_family": "endpoint_knot",
        "candidate_topology_id": "3:1:1",
        "candidate_name": "trefoil",
        "abstract_topology_class": False,
        "component_count_expected": 1,
        "crossing_number_expected": 3,
        "linking_number_expected": 0,
        "chirality_model": "chiral_prime_knot",
        "sst_role_hint": "endpoint_sector_reference",
    },
    {
        "candidate_family": "endpoint_knot",
        "candidate_topology_id": "4:1:1",
        "candidate_name": "figure-eight",
        "abstract_topology_class": False,
        "component_count_expected": 1,
        "crossing_number_expected": 4,
        "linking_number_expected": 0,
        "chirality_model": "achiral_prime_knot",
        "sst_role_hint": "achiral_reference_candidate",
    },
    {
        "candidate_family": "minimal_linked_carrier",
        "candidate_topology_id": "L2a1",
        "candidate_name": "Hopf link",
        "abstract_topology_class": False,
        "component_count_expected": 2,
        "crossing_number_expected": 2,
        "linking_number_expected": 1,
        "chirality_model": "two_component_link",
        "sst_role_hint": "minimal_linked_q_qbar_candidate",
    },
    {
        "candidate_family": "double_linked_carrier",
        "candidate_topology_id": "L4a1",
        "candidate_name": "Solomon link",
        "abstract_topology_class": False,
        "component_count_expected": 2,
        "crossing_number_expected": 4,
        "linking_number_expected": 2,
        "chirality_model": "two_component_double_link",
        "sst_role_hint": "double_protected_linked_mesonic_resonance_candidate",
    },
]

prime_knot_targets = build_prime_knot_targets(MAX_PRIME_CROSSING)

all_targets = []
seen = set()
for row in MESON_TEST_CLASSES + CORE_LINK_AND_KNOT_TARGETS + prime_knot_targets:
    tid = row["candidate_topology_id"]
    if tid in seen:
        continue
    seen.add(tid)
    all_targets.append(row)

targets_df = pd.DataFrame(all_targets)
print("Total candidate targets:", len(targets_df))
print("Prime-knot targets:", len(prime_knot_targets))
display(targets_df.head(20))
display(targets_df.tail(10))


#@title 7. Robust topology lookup helpers

LOOKUP_FUNCTIONS = [
    "get_ideal_ab",
    "get_ideal_link",
    "get_fourier_knot",
    "get_knot",
    "get_knot_by_id",
    "load_knot",
    "load_link",
]

FALLBACK_GEOMETRY = {
    "3:1:1": {"name": "trefoil", "component_count": 1, "crossing_number": 3, "linking_number": 0, "ropelength": 16.371637},
    "4:1:1": {"name": "figure-eight", "component_count": 1, "crossing_number": 4, "linking_number": 0, "ropelength": 21.043322},
    "L2a1": {"name": "Hopf link", "component_count": 2, "crossing_number": 2, "linking_number": 1, "ropelength": 12.566370},
    "L4a1": {"name": "Solomon link", "component_count": 2, "crossing_number": 4, "linking_number": 2, "ropelength": 20.009315},
}

def safe_to_dict(obj):
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

def find_topology(topology_id, abstract_topology_class=False):
    if abstract_topology_class:
        return {
            "topology_id": topology_id,
            "sstcore_found": False,
            "lookup_function": "abstract_SST_class",
            "object_type": "abstract",
            "object_preview": "Abstract SST class; no direct SSTcore resource lookup expected.",
            "object": None,
            "errors": "",
        }
    errors = []
    for fn in LOOKUP_FUNCTIONS:
        if not hasattr(sst, fn):
            continue
        try:
            obj = getattr(sst, fn)(topology_id)
            found = obj is not None
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


#@title 8. Probe all candidate knot/link classes

records = []
for target in all_targets:
    tid = target["candidate_topology_id"]
    abstract = bool(target.get("abstract_topology_class", False))
    lookup = find_topology(tid, abstract_topology_class=abstract)
    geom = extract_numeric_geometry(lookup["object"])

    fallback = FALLBACK_GEOMETRY.get(tid, {})
    merged = dict(fallback)
    merged.update({k: v for k, v in geom.items() if v not in [None, ""]})

    ropelength = merged.get("ropelength", np.nan)
    component_count = merged.get("component_count", target.get("component_count_expected", np.nan))
    linking_number = merged.get("linking_number", target.get("linking_number_expected", np.nan))
    crossing_number = merged.get("crossing_number", target.get("crossing_number_expected", np.nan))

    if geom:
        geometry_source = "SSTcore_extracted"
    elif fallback:
        geometry_source = "fallback_reference"
    elif abstract:
        geometry_source = "abstract_SST_class"
    else:
        geometry_source = "not_found"

    records.append({
        **target,
        "sstcore_found": lookup["sstcore_found"],
        "lookup_function": lookup["lookup_function"],
        "object_type": lookup["object_type"],
        "component_count": component_count,
        "crossing_number": crossing_number,
        "linking_number": linking_number,
        "ropelength": ropelength,
        "geometry_source": geometry_source,
        "E_M0_MeV": E_M0_MeV,
        "length_scaled_anchor_MeV": ropelength * E_M0_MeV if pd.notna(ropelength) else np.nan,
        "status": "geometry_probe_only",
        "notes": "No final particle assignment. Use as candidate topology input only.",
        "object_preview": lookup["object_preview"],
        "errors": lookup["errors"],
    })

geometry_probe_df = pd.DataFrame(records)

print("Rows:", len(geometry_probe_df))
print("Found by SSTcore:", int(geometry_probe_df["sstcore_found"].sum()))
print("Abstract SST classes:", int((geometry_probe_df["geometry_source"] == "abstract_SST_class").sum()))
print("Not found:", int((geometry_probe_df["geometry_source"] == "not_found").sum()))
display(geometry_probe_df.head(25))
display(geometry_probe_df.tail(10))

status_df = (
    geometry_probe_df
    .groupby(["candidate_family", "geometry_source"], dropna=False)
    .size()
    .reset_index(name="count")
    .sort_values(["candidate_family", "geometry_source"])
)
display(status_df)


#@title 9. Prime-knot lookup summary

prime_probe_df = geometry_probe_df[geometry_probe_df["candidate_family"] == "prime_knot_table"].copy()

prime_summary_df = (
    prime_probe_df
    .groupby(["crossing_number_expected", "geometry_source"], dropna=False)
    .size()
    .reset_index(name="count")
    .sort_values(["crossing_number_expected", "geometry_source"])
)

display(prime_summary_df)

missing_prime_df = prime_probe_df[prime_probe_df["geometry_source"] == "not_found"].copy()
print("Missing prime-knot resources:", len(missing_prime_df))
display(missing_prime_df[["candidate_topology_id", "candidate_name", "crossing_number_expected", "errors"]].head(50))


#@title 10. Optional meson-carrier energy sandbox

def linked_energy_estimate(E0_MeV, component_count=2, linking_number=0, lambda_link=0.0, B_chi_MeV=0.0, E_dress_MeV=0.0):
    return (component_count + lambda_link * abs(linking_number)) * E0_MeV - B_chi_MeV + E_dress_MeV

sandbox_rows = []
sandbox_targets = geometry_probe_df[
    geometry_probe_df["candidate_family"].isin([
        "open_mesonic_carrier",
        "connected_sum_candidate",
        "minimal_linked_carrier",
        "double_linked_carrier",
        "endpoint_knot",
    ])
].copy()

for _, row in sandbox_targets.iterrows():
    for lambda_link in [0.0, 0.25, 0.5, 1.0]:
        comp = row["component_count"] if pd.notna(row["component_count"]) else row.get("component_count_expected", 1)
        lk = row["linking_number"] if pd.notna(row["linking_number"]) else row.get("linking_number_expected", 0)
        try:
            comp = int(comp)
        except Exception:
            comp = 1
        try:
            lk = float(lk)
        except Exception:
            lk = 0.0
        E_est = linked_energy_estimate(E_M0_MeV, component_count=comp, linking_number=lk, lambda_link=lambda_link)
        sandbox_rows.append({
            "candidate_topology_id": row["candidate_topology_id"],
            "candidate_name": row["candidate_name"],
            "candidate_family": row["candidate_family"],
            "component_count": comp,
            "linking_number": lk,
            "lambda_link": lambda_link,
            "B_chi_MeV": 0.0,
            "E_dress_MeV": 0.0,
            "toy_energy_MeV": E_est,
            "toy_energy_over_E_M0": E_est / E_M0_MeV,
            "status": "toy_sandbox_not_claim",
        })

energy_sandbox_df = pd.DataFrame(sandbox_rows)
display(energy_sandbox_df)


#@title 11. Export standalone workbook

standalone_xlsx = "SSTcore_v0_8_2_Colab_Geometry_Probe_v0_2_prime_knots.xlsx"

with pd.ExcelWriter(standalone_xlsx, engine="openpyxl") as writer:
    constants_df.to_excel(writer, sheet_name="SST_Constants", index=False)
    targets_df.to_excel(writer, sheet_name="Candidate_Targets", index=False)
    geometry_probe_df.to_excel(writer, sheet_name="SSTcore_Geometry_Probe", index=False)
    prime_summary_df.to_excel(writer, sheet_name="Prime_Knot_Summary", index=False)
    energy_sandbox_df.to_excel(writer, sheet_name="Energy_Sandbox", index=False)

print("Wrote:", standalone_xlsx)

try:
    from google.colab import files
    files.download(standalone_xlsx)
except Exception:
    print("Not running in Colab; file is available locally:", standalone_xlsx)


#@title 12. Upload falsification workbook, append geometry sheets, and download result

from google.colab import files

uploaded = files.upload()
xlsx_files = [name for name in uploaded.keys() if name.lower().endswith(".xlsx")]
if not xlsx_files:
    raise RuntimeError("No .xlsx file uploaded. Upload the falsification skeleton workbook.")

input_xlsx = xlsx_files[0]
output_xlsx = input_xlsx.replace(".xlsx", "_with_SSTcore_v0_2_Prime_Knots.xlsx")

xls = pd.ExcelFile(input_xlsx)

with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
    for sheet in xls.sheet_names:
        df = pd.read_excel(input_xlsx, sheet_name=sheet)
        df.to_excel(writer, sheet_name=sheet[:31], index=False)

    constants_df.to_excel(writer, sheet_name="SST_Colab_Constants", index=False)
    targets_df.to_excel(writer, sheet_name="Candidate_Targets", index=False)
    geometry_probe_df.to_excel(writer, sheet_name="SSTcore_Geometry_Probe", index=False)
    prime_summary_df.to_excel(writer, sheet_name="Prime_Knot_Summary", index=False)
    energy_sandbox_df.to_excel(writer, sheet_name="Energy_Sandbox", index=False)

print("Wrote:", output_xlsx)
files.download(output_xlsx)


# ## Interpretation rule
# 
# Use this notebook in four passes:
# 
# 1. **API pass:** verify `SSTcore==0.8.2`, resource paths, and native bindings.
# 2. **Geometry pass:** extract or reference candidate knot/link geometry for `3:1:1`, `L2a1`, `L4a1`, and all prime knots through \(10_{165}\).
# 3. **Meson-class pass:** keep `OPEN_QQBAR`, `SQUARE_KNOT_TENDENCY`, and `GRANNY_KNOT_TENDENCY` as abstract SST classes until explicit geometries are generated.
# 4. **Falsification pass:** append results to the workbook, then later add fixed SST assignment rules and SSTcore energy functionals.
# 
# Do not treat the toy energy sandbox as a final SST mass prediction. It is only a dimensional and organizational scaffold.
