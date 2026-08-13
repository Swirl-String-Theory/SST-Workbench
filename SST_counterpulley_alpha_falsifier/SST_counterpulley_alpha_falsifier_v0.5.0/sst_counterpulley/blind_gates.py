"""v0.5 blind gates: gauge audit -> seed search -> Newton--Krylov multiple shooting -> true Floquet.

The numerical fine-structure constant is neither imported nor stored here.  The
post-hoc benchmark remains software-gated until H18 passes.
"""
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
from .rpo_solver import (fractional_channel_relabel, newton_krylov_multiple_shooting)
from .monodromy import full_relative_monodromy_fd, kelvin_restricted_true_monodromy


def _gate(name, passed, metrics, criterion, note=""):
    if passed is None:
        return {"name":name,"status":"SKIP","pass":None,"metrics":metrics,"criterion":criterion,"note":note}
    return {"name":name,"status":"PASS" if passed else "FAIL","pass":bool(passed),"metrics":metrics,"criterion":criterion,"note":note}


def _blind_source_check() -> dict:
    here=Path(__file__).resolve().parent
    files=[here/"orbit.py",here/"rpo_solver.py",here/"monodromy.py",here/"blind_gates.py"]
    bad=[]
    for p in files:
        t=p.read_text(encoding="utf-8")
        if ("137."+"035") in t or ("ALPHA_INV"+"_BENCHMARK") in t:
            bad.append(p.name)
    return {"files":[p.name for p in files],"violations":bad}


def _integrate(center,D,*,dt,T,force_python,skip_build=True):
    p,m,_,_=make_counter_channels(center,.5*D); x=np.stack((p,m),axis=0)
    backend,_=load_backend(force_python=force_python,skip_build=skip_build)
    rhs=lambda z: pair_rhs_hat(z,D=D,gamma_plus=1.0,gamma_minus=-1.0,eps_over_D=.05,backend=backend)
    n=max(1,int(round(T/dt))); h=T/n
    for _ in range(n): x=rk4_step(x,h,rhs)
    return x


def _complex_conjugate_pair_error(vals: np.ndarray) -> float:
    v=list(np.asarray(vals,dtype=complex)); worst=0.0
    if not v: return float("inf")
    for z in v:
        err=min(abs(np.conjugate(z)-w) for w in v); worst=max(worst,float(err/max(1.0,abs(z))))
    return worst


def _fractional_relabel_rhs_error(center,D,*,nshift=.137,force_python=False):
    p,m,_,_=make_counter_channels(center,.5*D); x=np.stack((p,m),axis=0)
    back,_=load_backend(force_python=force_python,skip_build=True)
    eps=.05*D
    v0=np.asarray(pair_rhs(x[0],x[1],1.0,-1.0,eps,backend=back)).reshape((2,len(center),3))
    xs=fractional_channel_relabel(x,nshift,channel=1)
    vs=np.asarray(pair_rhs(xs[0],xs[1],1.0,-1.0,eps,backend=back)).reshape((2,len(center),3))
    # Compare the + channel at identical physical probe points.  It is induced by
    # the same closed - curve up to finite-N interpolation error.
    return float(np.linalg.norm(vs[0]-v0[0])/max(np.linalg.norm(v0[0]),1e-30))


def run_blind_gates(*,out_dir="audit_out_blind",data_path=DEFAULT_DATA,force_python=False,
                    force_build=False,build_verbose=False,quick=False)->dict:
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); gates=[]

    s0=_blind_source_check(); h0=not s0["violations"]
    gates.append(_gate("H0_alpha_blindness",h0,s0,"RPO solver/monodromy/gates contain no alpha benchmark literal"))

    n1=20 if quick else 40; c1,m1=prepare_centerline(data_path=data_path,n=n1); D=float(m1["D_metadata"])
    p1,q1,_,_=make_counter_channels(c1,.5*D)
    py,_=load_backend(force_python=True,skip_build=True); vp=np.asarray(pair_rhs(p1,q1,1,-1,.05*D,backend=py))
    native,nname=load_backend(force_python=force_python,skip_build=False,force_build=force_build,build_verbose=build_verbose)
    vn=np.asarray(pair_rhs(p1,q1,1,-1,.05*D,backend=native)); e1=float(np.linalg.norm(vn-vp)/max(np.linalg.norm(vp),1e-30))
    h1=e1<2e-11; gates.append(_gate("H1_native_python_rhs_parity",h1,{"backend":nname,"relative_error":e1},"relative RHS error <2e-11"))

    n2=14 if quick else 18; c2,m2=prepare_centerline(data_path=data_path,n=n2); D2=float(m2["D_metadata"])
    T2=.03; dts=[.0015,.00075,.000375]
    sols=[_integrate(c2,D2,dt=d,T=T2,force_python=force_python) for d in dts]
    ecm=best_relative_alignment(sols[2],sols[0],D=D2)["rms_over_D"]; emf=best_relative_alignment(sols[2],sols[1],D=D2)["rms_over_D"]
    ratio=ecm/max(emf,1e-30); h2=emf<1e-3 and ratio>8
    gates.append(_gate("H2_time_integrator_convergence",h2,{"dt_hat":dts,"coarse_vs_fine":ecm,"medium_vs_fine":emf,"error_ratio":ratio},"RK4 in convergent regime"))

    R=rigid_rotation_matrix(); t=np.array([.37,-.19,.23])*D
    xref=np.stack(make_counter_channels(c1,.5*D)[:2],axis=0); xmov=xref@R.T+t
    a3=best_relative_alignment(xref,xmov,D=D); h3=a3["rms_over_D"]<5e-12 and abs(a3["det_rotation"]-1)<1e-12
    gates.append(_gate("H3_relative_SE3_quotient",h3,{"rms_over_D":a3["rms_over_D"],"det_rotation":a3["det_rotation"]},"known SE(3) transform removed to machine precision"))

    n4=18 if quick else 24; c4,m4=prepare_centerline(data_path=data_path,n=n4); D4=float(m4["D_metadata"])
    x4=_integrate(c4,D4,dt=.015,T=.25,force_python=force_python); sc=2.731
    xs=_integrate(c4*sc,D4*sc,dt=.015,T=.25,force_python=force_python); e4=best_relative_alignment(x4,xs/sc,D=D4)["rms_over_D"]
    h4=e4<2e-8; gates.append(_gate("H4_scale_collapse",h4,{"scale":sc,"shape_error_over_D":e4},"dimensionless orbit invariant under uniform scaling"))

    # H5: demonstrate that a pure longitudinal channel offset is a continuum gauge.
    cg1,mg1=prepare_centerline(data_path=data_path,n=32 if quick else 48); Dg=float(mg1["D_metadata"])
    cg2,mg2=prepare_centerline(data_path=data_path,n=64 if quick else 96)
    eg1=_fractional_relabel_rhs_error(cg1,Dg,force_python=force_python); eg2=_fractional_relabel_rhs_error(cg2,float(mg2["D_metadata"]),force_python=force_python)
    h5=eg2<eg1 and (eg2<(.20 if quick else .05))
    gates.append(_gate("H5_longitudinal_shift_is_gauge",h5,{"shift_turns":.137,"coarse_rhs_error":eg1,"fine_rhs_error":eg2,"error_ratio_fine_over_coarse":eg2/max(eg1,1e-30)},"fractional relabelling artifact decreases and is <0.20 (quick) / <0.05 (full)","Delta s_+- is not admitted as a physical rescue parameter in the axisymmetric filament model."))

    nc=28 if quick else 40; cc,mc=prepare_centerline(data_path=data_path,n=nc); Dc=float(mc["D_metadata"])
    canon=search_relative_periodic_orbit(cc,D=Dc,dt_hat=.006 if quick else .004,max_time_hat=.8 if quick else 1.2,
        min_time_hat=.18,snapshot_stride=5,recurrence_tol_over_D=.07 if quick else .05,force_python=force_python,skip_build=True)
    cand=canon["candidate"]; write_csv(out/"canonical_recurrence_trace.csv",canon["recurrence_trace"])
    h6=np.isfinite(cand["recurrence_rms_over_D"]) and cand["period_hat"]>0
    gates.append(_gate("H6_canonical_recurrence_search",h6,{k:cand[k] for k in ["period_hat","recurrence_rms_over_D","endpoint_vectorfield_error","pair_min_distance_over_D"]},"finite recurrence minimum exists"))

    n7=20 if quick else 28; c7,m7=prepare_centerline(data_path=data_path,n=n7); D7=float(m7["D_metadata"])
    if quick:
        seedrows=scan_rpo_seeds(c7,D=D7,offsets=(.30,.45,.60),eps_values=(.05,.10),phases=(0.0,math.pi/2),dt_hat=.008,max_time_hat=.65,min_time_hat=.16,snapshot_stride=4,force_python=force_python,skip_build=True)
    else:
        seedrows=scan_rpo_seeds(c7,D=D7,offsets=(.25,.35,.50,.65),eps_values=(.04,.07,.10),phases=(0.0,math.pi/2,math.pi),dt_hat=.006,max_time_hat=.9,min_time_hat=.18,snapshot_stride=5,force_python=force_python,skip_build=True)
    write_csv(out/"rpo_seed_scan.csv",seedrows); bestseed=seedrows[0]
    h7=np.isfinite(bestseed["recurrence_rms_over_D"])
    gates.append(_gate("H7_alpha_blind_seed_campaign",h7,{"best":bestseed,"seed_count":len(seedrows)},"predeclared seed family ranked only by recurrence"))

    # H8/H9: nonlinear Newton--Krylov multiple shooting from the best blind seed.
    ns=12 if quick else 16; cs,ms=prepare_centerline(data_path=data_path,n=ns); Ds=float(ms["D_metadata"])
    ps,qs,_,_=make_counter_channels(cs,float(bestseed["offset_over_D"])*Ds,phase=float(bestseed["channel_phase_rad"])); xs0=np.stack((ps,qs),axis=0)
    nk=newton_krylov_multiple_shooting(cs,D=Ds,state0=xs0,seed_period_hat=max(float(bestseed["period_hat"]),.12),
        eps_over_D=float(bestseed["eps_over_D"]),segments=3 if quick else 4,basis_cols=8 if quick else 10,
        dt_hat=.012 if quick else .008,max_newton=3 if quick else 5,recurrence_tol_over_D=.08 if quick else .05,
        vf_tol=.16 if quick else .10,force_python=force_python,skip_build=True)
    nr=nk["result"]; write_json(out/"newton_krylov_result.json",{k:v for k,v in nk.items() if k not in {"corrected_initial_state","terminal_state","shooting_vector"}})
    h8=np.isfinite(nr["final_projected_residual"]) and np.isfinite(nr["gmres_last_relative_residual"])
    gates.append(_gate("H8_newton_krylov_solver_wellposed",h8,{k:nr[k] for k in ["initial_projected_residual","final_projected_residual","residual_reduction_factor","initial_max_shooting_defect","max_shooting_defect","full_defect_reduction_factor","iterations","gmres_last_relative_residual"]},"matrix-free Newton--Krylov returns finite residuals and merit history"))
    h9=nr["max_shooting_defect"]<(.45 if quick else .40) and nr["full_defect_reduction_factor"]>(1.01 if quick else 1.05)
    gates.append(_gate("H9_multiple_shooting_full_defect_reduction",h9,{"initial_max_shooting_defect":nr["initial_max_shooting_defect"],"max_shooting_defect":nr["max_shooting_defect"],"full_defect_reduction_factor":nr["full_defect_reduction_factor"],"segments":nk["segments"],"basis_cols":nk["basis_cols"]},"full-state segment defect <0.45 quick / <0.40 full and decreases materially"))

    rtol=.08 if quick else .05; h10=nr["recurrence_rms_over_D"]<rtol
    gates.append(_gate("H10_full_state_RPO_closure",h10,{"recurrence_rms_over_D":nr["recurrence_rms_over_D"],"period_hat":nr["period_hat"],"shift":nr["shift"]},f"full Cartesian relative recurrence <{rtol} D; projected residual alone never counts"))
    vtol=.16 if quick else .10; h11=nr["endpoint_vectorfield_error"]<vtol
    gates.append(_gate("H11_RPO_tangent_compatibility",h11,{"endpoint_vectorfield_error":nr["endpoint_vectorfield_error"]},f"endpoint vector-field mismatch <{vtol}"))

    orbit_ready=bool(nr["accepted"] and h10 and h11)
    resolution_confirmation=None
    if orbit_ready:
        ncf=16 if quick else 20; cf,mf=prepare_centerline(data_path=data_path,n=ncf); Df=float(mf["D_metadata"])
        pf,qf,_,_=make_counter_channels(cf,float(bestseed["offset_over_D"])*Df,phase=float(bestseed["channel_phase_rad"])); xf=np.stack((pf,qf),axis=0)
        nkf=newton_krylov_multiple_shooting(cf,D=Df,state0=xf,seed_period_hat=nr["period_hat"],eps_over_D=float(bestseed["eps_over_D"]),
            segments=3 if quick else 4,basis_cols=8 if quick else 10,dt_hat=.010 if quick else .007,max_newton=3 if quick else 4,
            recurrence_tol_over_D=rtol,vf_tol=vtol,force_python=force_python,skip_build=True)
        resolution_confirmation=nkf["result"]
        h12=bool(resolution_confirmation["accepted"] and abs(resolution_confirmation["period_hat"]-nr["period_hat"])/max(abs(nr["period_hat"]),1e-30)<.15)
        gates.append(_gate("H12_RPO_resolution_confirmation",h12,{"coarse_period_hat":nr["period_hat"],"fine":resolution_confirmation},"accepted RPO survives higher N with period change <15%"))
    else:
        h12=False; gates.append(_gate("H12_RPO_resolution_confirmation",None,{},"accepted RPO survives higher N","Skipped because H10/H11 did not establish an RPO."))

    mon=None; kres=None
    if orbit_ready and h12:
        x0c=np.asarray(nk["corrected_initial_state"]); N=x0c.shape[1]
        mon=full_relative_monodromy_fd(x0c,D=Ds,period_hat=nr["period_hat"],dt_hat=.012 if quick else .008,
            shift=nr["shift"],rotation=np.asarray(nr["rotation"]),translation=np.asarray(nr["translation_over_D"])*Ds,
            eps_over_D=float(bestseed["eps_over_D"]),fd_step_over_D=2e-5,max_n=24,force_python=force_python,skip_build=True)
        kres=kelvin_restricted_true_monodromy(mon,cs,x0c)
    h13=bool(mon is not None)
    gates.append(_gate("H13_true_relative_monodromy_constructed",h13 if (orbit_ready and h12) else None,{} if mon is None else {"dimension":mon["dimension"],"base_relative_map_residual":mon["base_relative_map_residual"]},"construct D(g^-1 o phi_T) only after confirmed RPO","Skipped because confirmed-RPO gate is closed." if mon is None else ""))

    mon2=None; k2=None
    if mon is None:
        for name,criterion in [
            ("H14_time_tangent_neutral_multiplier","||M f-f||/||f|| below threshold"),
            ("H15_monodromy_fd_convergence","true phase stable under FD refinement"),
            ("H16_real_monodromy_conjugate_pairing","real M spectrum closes under conjugation"),
            ("H17_true_Floquet_phase_defined","finite low-leakage Kelvin readout")]:
            gates.append(_gate(name,None,{},criterion,"Skipped because no confirmed RPO/monodromy exists."))
        h14=h15=h16=h17=False
    else:
        h14=mon["time_tangent_neutral_residual"]<(.12 if quick else .08)
        gates.append(_gate("H14_time_tangent_neutral_multiplier",h14,{"neutral_residual":mon["time_tangent_neutral_residual"]},"time tangent is approximately neutral"))
        mon2=full_relative_monodromy_fd(np.asarray(nk["corrected_initial_state"]),D=Ds,period_hat=nr["period_hat"],dt_hat=.012 if quick else .008,
            shift=nr["shift"],rotation=np.asarray(nr["rotation"]),translation=np.asarray(nr["translation_over_D"])*Ds,
            eps_over_D=float(bestseed["eps_over_D"]),fd_step_over_D=1e-5,max_n=24,force_python=force_python,skip_build=True)
        k2=kelvin_restricted_true_monodromy(mon2,cs,np.asarray(nk["corrected_initial_state"]))
        dp=abs(((kres["true_floquet_phase_turns"]-k2["true_floquet_phase_turns"]+.5)%1)-.5); h15=dp<(.03 if quick else .015)
        gates.append(_gate("H15_monodromy_fd_convergence",h15,{"phase_difference_turns":dp},"Kelvin true-Floquet phase stable under factor-two FD refinement"))
        cerr=_complex_conjugate_pair_error(mon["eigenvalues"]); h16=cerr<1e-7
        gates.append(_gate("H16_real_monodromy_conjugate_pairing",h16,{"max_relative_conjugate_pair_error":cerr},"real monodromy spectrum conjugate pairing <1e-7"))
        h17=np.isfinite(kres["true_floquet_phase_turns"]) and kres["kelvin_subspace_leakage"]<.8
        gates.append(_gate("H17_true_Floquet_phase_defined",h17,{"true_floquet_phase_turns":kres["true_floquet_phase_turns"],"kelvin_subspace_leakage":kres["kelvin_subspace_leakage"]},"finite preregistered Kelvin phase and leakage <0.8"))

    ready=bool(h0 and h1 and h2 and h3 and h4 and h5 and h8 and h9 and orbit_ready and h12 and h13 and h14 and h15 and h16 and h17)
    gates.append(_gate("H18_ready_for_alpha_unblinding",ready,{"ready":ready},"all implementation, RPO, resolution and true-Floquet gates pass"))

    if not all([h0,h1,h2,h3,h4]): verdict="INCONCLUSIVE_IMPLEMENTATION_OR_NUMERICS"
    elif not h5: verdict="LONGITUDINAL_SHIFT_NOT_CONFIRMED_AS_GAUGE__MODEL_DISCRETIZATION_REVIEW_REQUIRED"
    elif not h8: verdict="NEWTON_KRYLOV_SOLVER_NUMERICALLY_ILLPOSED"
    elif not orbit_ready: verdict="NO_ALPHA_BLIND_RPO_FOUND_AFTER_NEWTON_KRYLOV_MULTIPLE_SHOOTING__TRUE_FLOQUET_GATE_CLOSED"
    elif not ready: verdict="RPO_CANDIDATE_FOUND_BUT_RESOLUTION_OR_TRUE_MONODROMY_GATES_FAIL"
    else: verdict="SURVIVES_V0_5_RPO_AND_TRUE_FLOQUET_BLIND_GATES__READY_FOR_POSTHOC_ALPHA"

    summary={"audit_name":"SST counter-pulley Newton-Krylov RPO + true Floquet falsifier v0.5.0",
             "protocol":"ALPHA_CLOSED_DURING_H0_H18","quick":bool(quick),"verdict":verdict,
             "ready_for_alpha_unblinding":ready,"canonical_candidate":cand,"best_seed":bestseed,
             "newton_krylov":nr,"resolution_confirmation":resolution_confirmation,"gates":gates,
             "true_monodromy":None if mon is None else {"n":mon["n"],"dimension":mon["dimension"],"period_hat":mon["period_hat"],
                 "base_relative_map_residual":mon["base_relative_map_residual"],"time_tangent_neutral_residual":mon["time_tangent_neutral_residual"],
                 "kelvin_readout":{k:v for k,v in kres.items() if k not in {"kelvin_block","kelvin_eigenvalues"}}}}
    write_json(out/"blind_audit_summary.json",summary)
    write_json(out/"blind_canonical.json",{"protocol":"ALPHA_BLIND_NEWTON_KRYLOV_RPO_ONLY","canonical_candidate":cand,"best_seed":bestseed,"newton_krylov":nr})
    return summary
