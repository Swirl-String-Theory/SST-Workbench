"""v0.4 blind gates: orbit first, true Floquet second, alpha never imported here."""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np

from .backend import load_backend
from .core import DEFAULT_DATA, prepare_centerline, write_csv, write_json
from .dynamics import pair_rhs
from .geometry import make_counter_channels, rigid_rotation_matrix
from .orbit import (search_relative_periodic_orbit, scan_rpo_seeds, pair_rhs_hat,
                    rk4_step, best_relative_alignment)
from .monodromy import full_relative_monodromy_fd, kelvin_restricted_true_monodromy


def _gate(name, passed, metrics, criterion, note=""):
    if passed is None:
        return {"name":name,"status":"SKIP","pass":None,"metrics":metrics,"criterion":criterion,"note":note}
    return {"name":name,"status":"PASS" if passed else "FAIL","pass":bool(passed),"metrics":metrics,"criterion":criterion,"note":note}


def _blind_source_check() -> dict:
    here=Path(__file__).resolve().parent
    files=[here/"orbit.py",here/"monodromy.py",here/"blind_gates.py"]
    bad=[]
    for p in files:
        t=p.read_text(encoding="utf-8")
        if ("137."+"035") in t or ("ALPHA_INV"+"_BENCHMARK") in t:
            bad.append(p.name)
    return {"files":[p.name for p in files],"violations":bad}


def _integrate(center, D, *, dt, T, force_python, skip_build=True, scale=1.0):
    p,m,_,_=make_counter_channels(center,.5*D)
    x=np.stack((p,m),axis=0)
    backend,_=load_backend(force_python=force_python,skip_build=skip_build)
    rhs=lambda z: pair_rhs_hat(z,D=D,gamma_plus=1.0,gamma_minus=-1.0,eps_over_D=.05,backend=backend)
    n=max(1,int(round(T/dt))); h=T/n
    for _ in range(n): x=rk4_step(x,h,rhs)
    return x


def _complex_conjugate_pair_error(vals: np.ndarray) -> float:
    v=list(np.asarray(vals,dtype=complex))
    if not v: return float("inf")
    worst=0.0
    for z in v:
        err=min(abs(np.conjugate(z)-w) for w in v)
        worst=max(worst,float(err/max(1.0,abs(z))))
    return worst


def run_blind_gates(*, out_dir="audit_out_blind", data_path=DEFAULT_DATA,
                    force_python=False, force_build=False, build_verbose=False, quick=False) -> dict:
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    gates=[]

    # H0 source-level alpha blindness.
    s0=_blind_source_check(); h0=not s0["violations"]
    gates.append(_gate("H0_alpha_blindness",h0,s0,"orbit/monodromy/gates contain no alpha benchmark literal"))

    # H1 native/Python RHS parity on identical physical state.
    n1=24 if quick else 48; c1,m1=prepare_centerline(data_path=data_path,n=n1); D=float(m1["D_metadata"])
    p1,q1,_,_=make_counter_channels(c1,.5*D)
    py,_=load_backend(force_python=True,skip_build=True)
    vp=np.asarray(pair_rhs(p1,q1,1,-1,.05*D,backend=py))
    native,nname=load_backend(force_python=force_python,skip_build=False,force_build=force_build,build_verbose=build_verbose)
    vn=np.asarray(pair_rhs(p1,q1,1,-1,.05*D,backend=native))
    e1=float(np.linalg.norm(vn-vp)/max(np.linalg.norm(vp),1e-30))
    h1=e1<2e-11
    gates.append(_gate("H1_native_python_rhs_parity",h1,{"backend":nname,"relative_error":e1},"relative RHS error <2e-11"))

    # H2 RK4 convergence at fixed short time. Compare aligned numerical solutions.
    n2=16 if quick else 20; c2,m2=prepare_centerline(data_path=data_path,n=n2); D2=float(m2["D_metadata"])
    # The filament ODE is stiff at the canonical finite core.  Test RK4 inside its
    # observed asymptotic regime rather than using production search time steps.
    T2=.04
    dts=[.002,.001,.0005]
    sols=[_integrate(c2,D2,dt=d,T=T2,force_python=force_python,skip_build=True) for d in dts]
    ecm=best_relative_alignment(sols[2],sols[0],D=D2)["rms_over_D"]
    emf=best_relative_alignment(sols[2],sols[1],D=D2)["rms_over_D"]
    ratio=ecm/max(emf,1e-30)
    h2=emf<1e-3 and ratio>10.0
    gates.append(_gate("H2_time_integrator_convergence",h2,{"dt_hat":dts,"coarse_vs_fine":ecm,"medium_vs_fine":emf,"error_ratio":ratio},
                       "RK4 medium/fine mismatch <1e-3 D and coarse/fine-to-medium/fine error ratio >10"))

    # H3 SE(3) quotient correctness: a known transformed state must align to machine precision.
    R=rigid_rotation_matrix(); t=np.array([.37,-.19,.23])*D
    xref=np.stack(make_counter_channels(c1,.5*D)[:2],axis=0)
    xmov=xref@R.T+t
    a3=best_relative_alignment(xref,xmov,D=D)
    h3=a3["rms_over_D"]<5e-12 and abs(a3["det_rotation"]-1)<1e-12
    gates.append(_gate("H3_relative_SE3_quotient",h3,{"rms_over_D":a3["rms_over_D"],"det_rotation":a3["det_rotation"]},
                       "known rigid transform removed to <5e-12 D"))

    # H4 dimensionless scale collapse of evolved shape recurrence.
    n4=20 if quick else 28; c4,m4=prepare_centerline(data_path=data_path,n=n4); D4=float(m4["D_metadata"])
    x4=_integrate(c4,D4,dt=.02,T=.4,force_python=force_python)
    sc=2.731; xs=_integrate(c4*sc,D4*sc,dt=.02,T=.4,force_python=force_python)
    # Scale back and align to suppress roundoff rigid drift.
    e4=best_relative_alignment(x4,xs/sc,D=D4)["rms_over_D"]
    h4=e4<2e-8
    gates.append(_gate("H4_scale_collapse",h4,{"scale":sc,"shape_error_over_D":e4},"dimensionless orbit invariant under X,D -> lambda(X,D)"))

    # H5 canonical recurrence search: this is descriptive, not yet the acceptance gate.
    nc=32 if quick else 48; cc,mc=prepare_centerline(data_path=data_path,n=nc); Dc=float(mc["D_metadata"])
    canon=search_relative_periodic_orbit(cc,D=Dc,dt_hat=.005 if quick else .003,
                max_time_hat=1.0 if quick else 2.0,min_time_hat=.2,snapshot_stride=10 if quick else 10,
                recurrence_tol_over_D=.06 if quick else .035,force_python=force_python,skip_build=True)
    cand=canon["candidate"]
    write_csv(out/"canonical_recurrence_trace.csv",canon["recurrence_trace"])
    h5=np.isfinite(cand["recurrence_rms_over_D"]) and cand["period_hat"]>0
    gates.append(_gate("H5_recurrence_search_wellposed",h5,{k:cand[k] for k in ["period_hat","recurrence_rms_over_D","shift","pair_min_distance_over_D","segment_max_over_min"]},
                       "finite nonzero recurrence minimum exists", f"trajectory termination: {canon.get('termination_reason')} at tau={canon.get('termination_time_hat'):.6g}"))

    # H6 canonical RPO closure.
    tol=.06 if quick else .035
    h6=bool(cand["recurrence_rms_over_D"]<tol)
    gates.append(_gate("H6_canonical_RPO_closure",h6,{"recurrence_rms_over_D":cand["recurrence_rms_over_D"],"period_hat":cand["period_hat"]},f"best relative recurrence <{tol} D"))

    # H7 vector-field endpoint compatibility under the same fixed group element.
    vtol=.15 if quick else .08
    h7=bool(cand["endpoint_vectorfield_error"]<vtol)
    gates.append(_gate("H7_RPO_tangent_compatibility",h7,{"endpoint_vectorfield_error":cand["endpoint_vectorfield_error"]},f"relative vector-field mismatch <{vtol}"))

    # H8 alpha-blind physical seed campaign. Select on recurrence only.
    n8=24 if quick else 32; c8,m8=prepare_centerline(data_path=data_path,n=n8); D8=float(m8["D_metadata"])
    if quick:
        seedrows=scan_rpo_seeds(c8,D=D8,offsets=(.35,.5,.65),eps_values=(.05,.10),phases=(0.0,math.pi/2),
                               dt_hat=.006,max_time_hat=.9,min_time_hat=.18,snapshot_stride=5,force_python=force_python,skip_build=True)
        seedtol=.08
    else:
        seedrows=scan_rpo_seeds(c8,D=D8,offsets=(.30,.40,.55,.70),eps_values=(.035,.065,.10),
                               phases=(0.0,math.pi/2,math.pi),dt_hat=.004,max_time_hat=1.2,
                               min_time_hat=.20,snapshot_stride=5,force_python=force_python,skip_build=True)
        seedtol=.05
    write_csv(out/"rpo_seed_scan.csv",seedrows)
    bestseed=seedrows[0]
    h8=bool(bestseed["recurrence_rms_over_D"]<seedtol and bestseed["endpoint_vectorfield_error"]<2*seedtol
            and bestseed["segment_max_over_min"]<8.0 and bestseed["pair_min_distance_over_D"]>bestseed["eps_over_D"])
    gates.append(_gate("H8_blind_RPO_seed_search",h8,{"best":bestseed,"seed_count":len(seedrows)},
                       f"some predeclared alpha-blind seed closes to <{seedtol} D with compatible endpoint field"))

    # H9-H13 are scientifically forbidden unless an actual RPO has survived H6-H8.
    # The canonical seed may fail while another alpha-blind physical seed succeeds.
    # H8 is therefore the existence gate; H6/H7 remain canonical controls.
    orbit_ready=bool(h8)
    mon=None; kres=None
    if orbit_ready:
        # Re-run the winning seed at deliberately small N for full-state monodromy feasibility.
        nm=12 if quick else 16; cm,mm=prepare_centerline(data_path=data_path,n=nm); Dm=float(mm["D_metadata"])
        rr=search_relative_periodic_orbit(cm,D=Dm,offset_over_D=float(bestseed["offset_over_D"]),eps_over_D=float(bestseed["eps_over_D"]),
              channel_phase=float(bestseed["channel_phase_rad"]),dt_hat=.015 if quick else .01,
              max_time_hat=max(2.0,float(bestseed["period_hat"])+.5),min_time_hat=.3,snapshot_stride=2,
              recurrence_tol_over_D=.08 if quick else .05,force_python=force_python,skip_build=True)
        rc=rr["candidate"]
        if rc["accepted"]:
            mon=full_relative_monodromy_fd(rr["initial_state"],D=Dm,period_hat=rc["period_hat"],dt_hat=.015 if quick else .01,
                 shift=rc["shift"],rotation=np.asarray(rc["rotation"]),translation=np.asarray(rc["translation_over_D"])*Dm,
                 eps_over_D=rc["eps_over_D"],fd_step_over_D=2e-5,max_n=24,force_python=force_python,skip_build=True)
            kres=kelvin_restricted_true_monodromy(mon,cm,rr["initial_state"])
    h9=bool(mon is not None)
    gates.append(_gate("H9_true_relative_monodromy_constructed",h9 if orbit_ready else None,
                       {} if mon is None else {"dimension":mon["dimension"],"base_relative_map_residual":mon["base_relative_map_residual"]},
                       "construct full D(g^-1 o phi_T) only on an accepted RPO",
                       "Skipped because the orbit gate is closed." if not orbit_ready else ""))
    if mon is None:
        for name,criterion in [
            ("H10_time_tangent_neutral_multiplier","||M f-f||/||f|| <0.08"),
            ("H11_monodromy_fd_convergence","true multiplier/phase stable under FD refinement"),
            ("H12_real_monodromy_conjugate_pairing","real M spectrum closes under complex conjugation"),
            ("H13_true_Floquet_phase_defined","pre-registered Kelvin readout from true M is finite and low-leakage")]:
            gates.append(_gate(name,None,{},criterion,"Skipped because no scientifically eligible RPO/monodromy exists."))
    else:
        h10=mon["time_tangent_neutral_residual"]<(.12 if quick else .08)
        gates.append(_gate("H10_time_tangent_neutral_multiplier",h10,{"neutral_residual":mon["time_tangent_neutral_residual"]},"||M f-f||/||f|| below threshold"))
        # Second FD monodromy only at tiny accepted orbit; expensive but genuinely tests the full return derivative.
        # If this branch is reached, scientific cost is justified.
        mon2=full_relative_monodromy_fd(rr["initial_state"],D=Dm,period_hat=rc["period_hat"],dt_hat=.015 if quick else .01,
                 shift=rc["shift"],rotation=np.asarray(rc["rotation"]),translation=np.asarray(rc["translation_over_D"])*Dm,
                 eps_over_D=rc["eps_over_D"],fd_step_over_D=1e-5,max_n=24,force_python=force_python,skip_build=True)
        k2=kelvin_restricted_true_monodromy(mon2,cm,rr["initial_state"])
        dp=abs(((kres["true_floquet_phase_turns"]-k2["true_floquet_phase_turns"]+.5)%1)-.5)
        h11=dp<(.03 if quick else .015)
        gates.append(_gate("H11_monodromy_fd_convergence",h11,{"phase_difference_turns":dp},"Kelvin true-Floquet phase stable under factor-two FD refinement"))
        cerr=_complex_conjugate_pair_error(mon["eigenvalues"]); h12=cerr<1e-7
        gates.append(_gate("H12_real_monodromy_conjugate_pairing",h12,{"max_relative_conjugate_pair_error":cerr},"real monodromy spectrum conjugate pairing <1e-7"))
        h13=np.isfinite(kres["true_floquet_phase_turns"]) and kres["kelvin_subspace_leakage"]<.8
        gates.append(_gate("H13_true_Floquet_phase_defined",h13,{"true_floquet_phase_turns":kres["true_floquet_phase_turns"],"kelvin_subspace_leakage":kres["kelvin_subspace_leakage"]},"finite pre-registered Kelvin phase and leakage <0.8"))

    ready=bool(h0 and h1 and h2 and h3 and h4 and orbit_ready and all(g["pass"] is True for g in gates[9:14]))
    gates.append(_gate("H14_ready_for_alpha_unblinding",ready,{"ready":ready},"H0-H13 required gates pass; no skipped Floquet gate"))

    if not h0 or not h1 or not h2 or not h3 or not h4:
        verdict="INCONCLUSIVE_IMPLEMENTATION_OR_NUMERICS"
    elif not orbit_ready:
        verdict="NO_ALPHA_BLIND_RPO_FOUND_IN_PREREGISTERED_WINDOW__TRUE_FLOQUET_GATE_CLOSED"
    elif not ready:
        verdict="RPO_FOUND_BUT_TRUE_MONODROMY_NOT_ROBUST"
    else:
        verdict="SURVIVES_RPO_AND_TRUE_FLOQUET_BLIND_GATES__READY_FOR_POSTHOC_ALPHA"

    summary={"audit_name":"SST counter-pulley RPO + true Floquet falsifier v0.4.0",
             "protocol":"ALPHA_CLOSED_DURING_H0_H14","quick":bool(quick),"verdict":verdict,
             "ready_for_alpha_unblinding":ready,"canonical_n":nc,"canonical_candidate":cand,
             "best_seed":bestseed,"gates":gates,
             "true_monodromy":None if mon is None else {"n":mon["n"],"dimension":mon["dimension"],
                 "period_hat":mon["period_hat"],"base_relative_map_residual":mon["base_relative_map_residual"],
                 "time_tangent_neutral_residual":mon["time_tangent_neutral_residual"],
                 "kelvin_readout":None if kres is None else {k:v for k,v in kres.items() if k not in {"kelvin_block","kelvin_eigenvalues"}}}}
    write_json(out/"blind_audit_summary.json",summary)
    write_json(out/"blind_canonical.json",{"protocol":"ALPHA_BLIND_RPO_ONLY","canonical_candidate":cand,"best_seed":bestseed})
    return summary
