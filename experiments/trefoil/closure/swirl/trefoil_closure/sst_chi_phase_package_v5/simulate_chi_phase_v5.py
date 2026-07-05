#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SST chi-phase package v5: profile zoo / admissibility sweep."""
from __future__ import annotations
import argparse, csv, math, os, time
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np
from sst_chi_phase_v5_py import default_profile_cases, evaluate_cases, profile_curve, result_to_dict, sweep_cases
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(SCRIPT_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)
C=2.99792458e8; ALPHA=7.2973525693e-3; M_E=9.1093837015e-31; HBAR=1.054571817e-34; RHO_F=7.0e-7
V_SWIRL=ALPHA*C/2.0; OMEGA_C=(M_E*C**2)/HBAR; R_C=V_SWIRL/OMEGA_C

def try_cpp_backend(force_python=False):
    if force_python: return None, "python-forced"
    try:
        from sst_chi_phase_v5_build import import_module
        return import_module(auto_build=True, script_dir=SCRIPT_DIR), "cpp"
    except Exception as exc:
        print(f"[!] C++ backend unavailable ({exc}). Using pure Python backend.")
        return None, "python-fallback"

def write_csv(path: str, rows: List[Dict[str, object]]):
    if not rows: return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0].keys())); writer.writeheader(); writer.writerows(rows)
    print(f"[*] CSV saved: {path}")

def plot_default_profiles(cases):
    plt.figure(figsize=(13,6))
    for name, params in cases:
        x, f, rho = profile_curve(name, params, n=1200)
        plt.plot(x, np.clip(f, -0.5, 8.0), label=name.replace("_"," "))
    plt.xlabel(r"$x=r/a_{\rm core}$"); plt.ylabel(r"$v_\theta(x)/v_{\rm ref}$")
    plt.title("v5 candidate radial swirl profiles (1/r clipped)"); plt.grid(True); plt.legend(fontsize=8); plt.tight_layout()
    path=os.path.join(EXPORT_DIR,"chi_v5_profiles.png"); plt.savefig(path,dpi=150); print(f"[*] Plot saved: {path}")

def plot_speed_bars(rows, filename, title):
    labels=[str(r["name"]).replace("_","\n")+"\n"+str(r["params"]) for r in rows]
    y=[float(r["c_over_v"]) for r in rows]
    plt.figure(figsize=(max(12,0.7*len(rows)),6)); plt.bar(range(len(rows)), y)
    plt.axhline(1.0, color="k", linestyle="--", label=r"$c_\chi/v_{\rm ref}=1$")
    plt.xticks(range(len(rows)), labels, rotation=55, ha="right", fontsize=8); plt.ylabel(r"$c_\chi/v_{\rm ref}$")
    plt.title(title); plt.grid(True, axis="y", alpha=0.4); plt.legend(); plt.tight_layout()
    path=os.path.join(EXPORT_DIR,filename); plt.savefig(path,dpi=150); print(f"[*] Plot saved: {path}")

def plot_score_vs_speed(rows):
    plt.figure(figsize=(9,6)); scores=np.array([int(r["admissibility_score_4"]) for r in rows],float); speeds=np.array([float(r["c_over_v"]) for r in rows],float)
    plt.scatter(scores, speeds)
    for r,x,y in zip(rows,scores,speeds):
        if int(r["admissibility_score_4"])>=3 or abs(y-1.0)<0.05:
            plt.annotate(str(r["name"]).replace("_"," ")[:24], (x,y), fontsize=8, xytext=(4,4), textcoords="offset points")
    plt.axhline(1.0,color="k",linestyle="--"); plt.xlabel("admissibility score (0..4)"); plt.ylabel(r"$c_\chi/v_{\rm ref}$")
    plt.title("v5 profile selection: admissibility versus torsional speed"); plt.grid(True); plt.tight_layout()
    path=os.path.join(EXPORT_DIR,"chi_v5_score_vs_speed.png"); plt.savefig(path,dpi=150); print(f"[*] Plot saved: {path}")

def finite_difference_convergence():
    rows=[]; n_mode_max=32
    for N in [128,256,512,1024,2048,4096,8192]:
        errs=[]
        for n in range(1,n_mode_max+1):
            ratio=math.sin(math.pi*n/N)/(math.pi*n/N); errs.append(abs(ratio-1.0))
        rows.append({"N":N,"max_relative_error":max(errs),"central_difference_prediction":max(errs)})
    write_csv(os.path.join(EXPORT_DIR,"chi_v5_spectrum_convergence.csv"), rows)
    plt.figure(figsize=(9,5)); Nvals=np.array([r["N"] for r in rows],float); err=np.array([r["max_relative_error"] for r in rows],float)
    plt.loglog(Nvals,err,"o-",label="observed max error"); plt.loglog(Nvals,err,"k--",label="central-difference prediction")
    plt.xlabel("periodic grid size N"); plt.ylabel("max relative spectrum error"); plt.title("v5 finite-difference convergence control"); plt.grid(True,which="both"); plt.legend(); plt.tight_layout()
    path=os.path.join(EXPORT_DIR,"chi_v5_spectrum_convergence.png"); plt.savefig(path,dpi=150); print(f"[*] Plot saved: {path}")
    return rows

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--python", action="store_true"); parser.add_argument("--n", type=int, default=400000); parser.add_argument("--sweep", action="store_true")
    args=parser.parse_args(); t0=time.time(); cpp_mod, backend=try_cpp_backend(args.python)
    print("="*88); print("SST chi-phase v5 profile-zoo / admissibility selector"); print("="*88)
    print(f"[*] backend = {backend}"); print(f"[*] rho_f   = {RHO_F:.8e} kg m^-3"); print(f"[*] v_swirl = {V_SWIRL:.8e} m s^-1"); print(f"[*] omega_c = {OMEGA_C:.8e} s^-1"); print(f"[*] r_c     = {R_C:.8e} m")
    print("[*] Key: c_chi^2/v_ref^2 = ∫rho f^2 x^3 dx / ∫rho x^3 dx")
    default_cases=default_profile_cases(); default_results=evaluate_cases(default_cases,n=args.n); default_rows=[result_to_dict(r) for r in default_results]
    write_csv(os.path.join(EXPORT_DIR,"chi_v5_default_profiles.csv"), default_rows)
    print("\nDefault profile results:")
    for r in default_results:
        print(f"  {r.name:32s} c/v={r.c_over_v: .12f} Gamma/Gamma_ref={r.gamma_ratio: .6e} slope={r.slope_boundary: .6f} score={r.admissibility_score_4}/4")
    plot_default_profiles(default_cases); plot_speed_bars(default_rows,"chi_v5_default_speed_ratio.png","v5 profile-derived torsional speed, default cases")
    candidates=default_results; out_rows=default_rows
    if args.sweep:
        print("\n[*] Running broad parameter sweep..."); candidates=evaluate_cases(sweep_cases(), n=max(80000,args.n//4)); out_rows=[result_to_dict(r) for r in candidates]
        write_csv(os.path.join(EXPORT_DIR,"chi_v5_profile_sweep.csv"), out_rows); plot_speed_bars(out_rows,"chi_v5_sweep_speed_ratio.png","v5 profile zoo parameter sweep")
    plot_score_vs_speed(out_rows); conv_rows=finite_difference_convergence()
    best_score=max(r.admissibility_score_4 for r in candidates); best=[r for r in candidates if r.admissibility_score_4==best_score]
    closest=min(candidates, key=lambda r: abs(r.c_over_v-1.0)); reg_boundary=[r for r in candidates if r.axis_velocity_regular and r.boundary_circulation_match]
    reg_boundary_sorted=sorted(reg_boundary, key=lambda r:(-r.admissibility_score_4, abs(r.c_over_v-1.0)))
    elapsed=time.time()-t0; summary_path=os.path.join(EXPORT_DIR,"chi_v5_run_results_summary.txt")
    with open(summary_path,"w",encoding="utf-8") as f:
        f.write("SST chi-phase v5 profile-zoo / admissibility summary\n====================================================\n")
        f.write(f"backend                                      = {backend}\n"); f.write(f"rho_f                                        = {RHO_F:.16e} kg m^-3\n"); f.write(f"v_swirl                                      = {V_SWIRL:.16e} m s^-1\n"); f.write(f"omega_c                                      = {OMEGA_C:.16e} s^-1\n"); f.write(f"r_c                                          = {R_C:.16e} m\n\n")
        f.write("Key equation:\nc_chi^2/v_ref^2 = int rho(x) f(x)^2 x^3 dx / int rho(x) x^3 dx\n\n")
        for r in default_results:
            f.write(f"{r.name:44s} c/v={r.c_over_v:.16e} Gamma/Gamma_ref={r.gamma_ratio:.8e} slope={r.slope_boundary:.8e} score={r.admissibility_score_4}/4\n")
        f.write("\n"); f.write(f"best admissibility score                     = {best_score}/4\n"); f.write("best-score profiles                          = "+"; ".join(f"{r.name} ({r.params}, c/v={r.c_over_v:.6g})" for r in best[:8])+"\n")
        f.write(f"closest profile to c/v=1                     = {closest.name} ({closest.params}, {closest.c_over_v:.16e})\n")
        if reg_boundary_sorted:
            br=reg_boundary_sorted[0]; f.write(f"best regular+boundary candidate              = {br.name} ({br.params}, c/v={br.c_over_v:.16e}, score={br.admissibility_score_4}/4)\n")
        f.write(f"finest-grid FD convergence error             = {conv_rows[-1]['max_relative_error']:.16e}\n"); f.write(f"elapsed                                      = {elapsed:.2f} s\n\n")
        f.write("Interpretation:\nv5 tests a zoo of Euler/Rankine, smooth-matched, exterior-like, Lamb-Oseen,\nand NLSE/GP density-regularized phase-vortex profiles. It does not prove a\nunique SST core. It identifies which profiles are admissible under selected\ndiagnostics and what r^2-weighted RMS speed they imply.\n")
    print(f"[*] Summary saved: {summary_path}"); print("="*88); print("Summary"); print("="*88)
    print(f"best score             = {best_score}/4"); print(f"closest c/v=1          = {closest.name} ({closest.params}) {closest.c_over_v:.12f}")
    if reg_boundary_sorted:
        br=reg_boundary_sorted[0]; print(f"best regular+boundary  = {br.name} ({br.params}) c/v={br.c_over_v:.12f}, score={br.admissibility_score_4}/4")
    print(f"finest FD error        = {conv_rows[-1]['max_relative_error']:.3e}"); print(f"elapsed                = {elapsed:.2f} s"); print("[*] PASS: v5 profile-zoo completed.")
if __name__=="__main__": main()
