from pathlib import Path
import csv
import hashlib
import json
import math
import numpy as np

from .backend import energy_ratio_general, filament_energy, backend_name
from .reference import (
    fit_even_energy_coefficient,
    isotropy_tensor,
    transverse_residual,
    energy_ratio_helicity_pair,
    transverse_wave_ratio_from_A2,
    linearized_rest_euler_frequency,
)
from .sampling import paired_transverse_samples, rotation_matrix, shear_matrix
from .filaments import (
    quasi_uniform_rotations,
    hopf_cell,
    rotate_cell,
    affine_cell,
    rk4_step,
    gauss_linking_number,
    orientation_tensor,
    segment_length_cv,
    shape_relative_rms,
)

THEORY_A2 = 2.0/15.0


def _load_config(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_csv(path, rows):
    if not rows:
        return
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def verify_seal(blind_dir):
    blind = Path(blind_dir); seal = blind/"BLIND_SEAL_SHA256.txt"
    if not seal.exists(): return False,["BLIND_SEAL_SHA256.txt missing"]
    errors=[]
    for line in seal.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        digest,rel=line.split("  ",1); p=blind/rel
        if not p.exists(): errors.append(f"missing:{rel}")
        elif _sha256(p)!=digest: errors.append(f"hash:{rel}")
    return not errors,errors


def _static_born_campaign(cfg):
    gammas=np.asarray(cfg["strain_amplitudes"],dtype=float)
    planes=list(cfg["shear_planes"])
    n_pair,w_pair,n_base,e1,e2=paired_transverse_samples(cfg["n_directions"])
    rows=[]; fits={}; max_odd=0.0; max_helicity=0.0
    for plane in planes:
        rp=[]; rm=[]
        for g in gammas:
            fp=shear_matrix(+g,plane); fm=shear_matrix(-g,plane)
            ap=energy_ratio_general(n_pair,w_pair,fp); am=energy_ratio_general(n_pair,w_pair,fm)
            hp,hm=energy_ratio_helicity_pair(n_base,e1,e2,fp)
            rp.append(ap); rm.append(am); max_odd=max(max_odd,abs(0.5*(ap-am))); max_helicity=max(max_helicity,abs(hp-hm))
            rows.append({"plane":plane,"gamma":float(g),"R_plus":ap,"R_minus":am,"even_delta":0.5*(ap+am)-1.0,"odd_component":0.5*(ap-am)})
        fit=fit_even_energy_coefficient(gammas,rp,rm)
        fit["relative_error_vs_2_over_15"]=abs(fit["A2"]-THEORY_A2)/THEORY_A2
        fit["candidate_cT_over_urms"]=transverse_wave_ratio_from_A2(fit["A2"])
        fits[plane]=fit
    vals=np.array([fits[p]["A2"] for p in planes])
    A2=float(vals.mean())
    return {
        "rows":rows,
        "transverse_residual":transverse_residual(n_pair,w_pair),
        "orientation_isotropy_fro":float(np.linalg.norm(isotropy_tensor(n_base)-np.eye(3)/3.0)),
        "A2_mean":A2,
        "A2_plane_relative_spread":float((vals.max()-vals.min())/abs(A2)),
        "candidate_cT_over_urms":math.sqrt(max(A2,0.0)),
        "max_odd_energy_component":max_odd,
        "helicity_split_max_abs":max_helicity,
        "plane_fits":fits,
    }


def _ensemble_energy(cells,circs,core):
    return float(sum(filament_energy(c,circs,core) for c in cells))


def _modulus_scan(cells,cfg,spacing_over_R=None):
    fc=cfg["filament"]; R=float(fc["radius"]); core=float(fc["core_radius"]); circs=fc["circulations"]
    spacing=float(spacing_over_R if spacing_over_R is not None else fc["packing_spacing_over_R"])
    Vcell=(spacing*R)**3; V=len(cells)*Vcell
    gammas=np.asarray(fc["modulus_gammas"],dtype=float)
    E0=_ensemble_energy(cells,circs,core)
    rows=[]; plane={}
    for pname in cfg["shear_planes"]:
        ys=[]
        for g in gammas:
            ep=_ensemble_energy([affine_cell(c,shear_matrix(+g,pname)) for c in cells],circs,core)
            em=_ensemble_energy([affine_cell(c,shear_matrix(-g,pname)) for c in cells],circs,core)
            even=0.5*(ep+em)-E0; odd=0.5*(ep-em)
            ys.append(even)
            rows.append({"plane":pname,"gamma":float(g),"E_plus_over_rho":ep,"E_minus_over_rho":em,"E0_over_rho":E0,"even_excess_over_rho":even,"odd_over_rho":odd})
        X=np.column_stack((gammas**2,gammas**4)); a2,a4=np.linalg.lstsq(X,np.asarray(ys),rcond=None)[0]
        mu_over_rho=float(2.0*a2/V)
        plane[pname]={"a2_energy_over_rho":float(a2),"a4_energy_over_rho":float(a4),"mu_over_rho":mu_over_rho,"cT":math.sqrt(max(mu_over_rho,0.0))}
    mus=np.array([plane[p]["mu_over_rho"] for p in cfg["shear_planes"]],dtype=float)
    mu=float(np.mean(mus)); spread=float((mus.max()-mus.min())/max(abs(mu),1e-300))
    Gamma=abs(float(circs[0])); vref=Gamma/(2.0*math.pi*core)
    return {
        "spacing_over_R":spacing,"cell_volume":Vcell,"total_volume":V,"E0_over_rho":E0,"rows":rows,"plane_fits":plane,
        "mu_over_rho_mean":mu,"mu_plane_spread_relative":spread,"candidate_cT":math.sqrt(max(mu,0.0)),
        "reference_speed":vref,"candidate_cT_over_reference_speed":math.sqrt(max(mu,0.0))/vref,
    }


def _stress(cells,cfg,plane,delta):
    fc=cfg["filament"]; R=float(fc["radius"]); spacing=float(fc["packing_spacing_over_R"]); V=len(cells)*(spacing*R)**3
    circs=fc["circulations"]; core=float(fc["core_radius"])
    ep=_ensemble_energy([affine_cell(c,shear_matrix(+delta,plane)) for c in cells],circs,core)
    em=_ensemble_energy([affine_cell(c,shear_matrix(-delta,plane)) for c in cells],circs,core)
    return float((ep-em)/(2.0*delta*V))


def _build_cells(cfg,linked=True):
    fc=cfg["filament"]
    base=hopf_cell(fc["radius"],fc["points_per_loop"],linked=linked)
    rots=quasi_uniform_rotations(fc["orientation_count"],fc["orientation_offset"])
    return [rotate_cell(base,Q) for Q in rots],rots


def _topological_dynamic_campaign(cfg):
    fc=cfg["filament"]; tol=cfg["tolerances"]
    circs=fc["circulations"]; core=float(fc["core_radius"]); dt=float(fc["dt"]); tf=float(fc["t_final"])
    cells0,rots=_build_cells(cfg,linked=True); unlinked,_=_build_cells(cfg,linked=False)
    M0,iso0=orientation_tensor(cells0)
    lk0=np.array([gauss_linking_number(c[0],c[1]) for c in cells0])
    lk_un=np.array([gauss_linking_number(c[0],c[1]) for c in unlinked])

    static_linked=_modulus_scan(cells0,cfg)
    static_unlinked=_modulus_scan(unlinked,cfg)
    topo_excess=(static_linked["mu_over_rho_mean"]-static_unlinked["mu_over_rho_mean"])/max(abs(static_unlinked["mu_over_rho_mean"]),1e-300)

    # Objectivity: Q(Fx) and (QFQ^T)(Qx) must have identical Hamiltonian energy.
    q=rotation_matrix(int(cfg["seed"])+811); gobj=float(fc["objectivity_gamma"]); F=shear_matrix(gobj,"xy")
    c0=cells0[0]; left=rotate_cell(affine_cell(c0,F),q); right=affine_cell(rotate_cell(c0,q),q@F@q.T)
    eleft=filament_energy(left,circs,core); eright=filament_energy(right,circs,core)
    objectivity_rel=abs(eleft-eright)/max(abs(eleft),1e-300)

    # Canonical linked cell: all unsheared orientation copies evolve by rotational equivariance.
    base=hopf_cell(fc["radius"],fc["points_per_loop"],linked=True)
    ebase0=filament_energy(base,circs,core); lkbase0=gauss_linking_number(base[0],base[1])
    one=rk4_step(base,dt,circs,core); half=rk4_step(base,0.5*dt,circs,core); two=rk4_step(half,0.5*dt,circs,core)
    rk_rel=shape_relative_rms(one,two)

    sample_times=sorted(float(t) for t in fc["sample_times"]); sample_steps={int(round(t/dt)):t for t in sample_times}
    steps=int(round(tf/dt)); x=base.copy(); dynamic_rows=[]; modulus_rows=[]; max_segcv=segment_length_cv(x)
    energy_samples=[]; link_samples=[]; mu_samples=[]; spread_samples=[]
    for step in range(steps+1):
        if step in sample_steps:
            t=sample_steps[step]
            cells=[rotate_cell(x,Q) for Q in rots]
            scan=_modulus_scan(cells,cfg)
            e=filament_energy(x,circs,core); lk=gauss_linking_number(x[0],x[1]); _,isot=orientation_tensor(cells)
            energy_samples.append(e); link_samples.append(lk); mu_samples.append(scan["mu_over_rho_mean"]); spread_samples.append(scan["mu_plane_spread_relative"])
            dynamic_rows.append({"time":t,"cell_energy_over_rho":e,"energy_rel_vs_t0":e/ebase0-1.0,"linking_number":lk,"link_change":lk-lkbase0,"orientation_isotropy_fro":isot,"mu_over_rho":scan["mu_over_rho_mean"],"mu_rel_vs_t0":scan["mu_over_rho_mean"]/static_linked["mu_over_rho_mean"],"mu_plane_spread_relative":scan["mu_plane_spread_relative"],"segment_length_cv":segment_length_cv(x)})
            for p,fit in scan["plane_fits"].items(): modulus_rows.append({"time":t,"plane":p,"mu_over_rho":fit["mu_over_rho"],"cT":fit["cT"]})
        if step<steps:
            x=rk4_step(x,dt,circs,core); max_segcv=max(max_segcv,segment_length_cv(x))

    energy_drift=max(abs(np.asarray(energy_samples)-ebase0))/abs(ebase0)
    link_change=max(abs(np.asarray(link_samples)-lkbase0))
    mu0=mu_samples[0]; persistence=min(mu_samples)/max(mu0,1e-300)
    spread_max=max(spread_samples)

    # Forward/backward reversibility on the same Hamiltonian filament ODE.
    xr=base.copy(); rev_steps=int(round(float(fc["reversibility_t_final"])/dt))
    for _ in range(rev_steps): xr=rk4_step(xr,dt,circs,core)
    for _ in range(rev_steps): xr=rk4_step(xr,-dt,circs,core)
    reversal=shape_relative_rms(xr,base)

    # Direct shear relaxation: +gamma and -gamma ensembles are evolved and the odd macroscopic stress is tracked.
    plane=str(fc["shear_relaxation_plane"]); g0=float(fc["shear_relaxation_gamma"]); dprobe=float(fc["stress_probe_delta"])
    plus=[affine_cell(c,shear_matrix(+g0,plane)) for c in cells0]; minus=[affine_cell(c,shear_matrix(-g0,plane)) for c in cells0]
    base_ref=base.copy()
    stress_rows=[]; stress0=None; stored0=None; plusE0=_ensemble_energy(plus,circs,core); minusE0=_ensemble_energy(minus,circs,core); baseE0=_ensemble_energy(cells0,circs,core)
    for step in range(steps+1):
        if step in sample_steps:
            t=sample_steps[step]
            tau=0.5*(_stress(plus,cfg,plane,dprobe)-_stress(minus,cfg,plane,dprobe))
            ep=_ensemble_energy(plus,circs,core); em=_ensemble_energy(minus,circs,core)
            # Unsheared reference evolves simultaneously; rotational copies have identical energy.
            ebase_t=float(fc["orientation_count"])*filament_energy(base_ref,circs,core)
            stored=0.5*(ep+em)-ebase_t
            if stress0 is None: stress0=tau; stored0=stored
            stress_rows.append({"time":t,"odd_shear_stress_over_rho":tau,"stress_persistence_ratio":tau/stress0,"even_stored_shear_energy_over_rho":stored,"stored_energy_ratio":stored/max(stored0,1e-300),"plus_energy_drift_rel":ep/plusE0-1.0,"minus_energy_drift_rel":em/minusE0-1.0,"base_reference_energy_drift_rel":ebase_t/baseE0-1.0})
        if step<steps:
            plus=[rk4_step(c,dt,circs,core) for c in plus]
            minus=[rk4_step(c,dt,circs,core) for c in minus]
            base_ref=rk4_step(base_ref,dt,circs,core)
    stress_persistence=min(r["stress_persistence_ratio"] for r in stress_rows)
    stored_drift=max(abs(r["stored_energy_ratio"]-1.0) for r in stress_rows)

    packing=[]
    for s in fc["packing_sweep_over_R"]:
        sc=_modulus_scan(cells0,cfg,spacing_over_R=float(s))
        packing.append({"spacing_over_R":float(s),"mu_over_rho":sc["mu_over_rho_mean"],"candidate_cT_over_reference_speed":sc["candidate_cT_over_reference_speed"]})
    target=float(cfg["master_factor_wave_gate"]["target_cT_over_reference_speed"])
    dense_ratio=packing[0]["candidate_cT_over_reference_speed"]
    required_spacing=float(fc["packing_spacing_over_R"])*(dense_ratio/target)**(2.0/3.0) if dense_ratio>0 else math.inf

    return {
        "orientation_tensor":M0.tolist(),"orientation_isotropy_fro":iso0,
        "initial_linking_mean":float(np.mean(lk0)),"initial_linking_abs_error_max":float(np.max(np.abs(np.abs(lk0)-1.0))),
        "unlinked_control_link_abs_max":float(np.max(np.abs(lk_un))),
        "static_linked":{k:v for k,v in static_linked.items() if k!="rows"},
        "static_unlinked":{k:v for k,v in static_unlinked.items() if k!="rows"},
        "linked_static_rows":static_linked["rows"],
        "unlinked_static_rows":static_unlinked["rows"],
        "topological_linking_excess_fraction":float(topo_excess),
        "objectivity_energy_relative_error":objectivity_rel,
        "rk4_one_step_vs_two_half_shape_rel":rk_rel,
        "base_energy_drift_rel_max":float(energy_drift),"link_change_abs_max":float(link_change),
        "max_segment_length_cv":float(max_segcv),"modulus_persistence_ratio_min":float(persistence),
        "modulus_plane_spread_relative_max":float(spread_max),"reversibility_shape_relative":float(reversal),
        "shear_stress_persistence_ratio_min":float(stress_persistence),"stored_shear_energy_relative_drift_max":float(stored_drift),
        "dynamic_rows":dynamic_rows,"modulus_rows":modulus_rows,"stress_rows":stress_rows,"packing_sweep":packing,
        "required_spacing_over_R_for_master_target_by_density_scaling":required_spacing,
        "geometric_nonoverlap_min_spacing_over_R":3.0,
    }


def run_blind_campaign(config_path,out_dir):
    cfg=_load_config(config_path); out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); tol=cfg["tolerances"]
    born=_static_born_campaign(cfg); top=_topological_dynamic_campaign(cfg)
    kprobe=np.array([1.,2.,-3.]); uprobe=np.cross(kprobe,np.array([.3,-.4,.8])); uprobe/=np.linalg.norm(uprobe)
    rest_accel,rest_trans=linearized_rest_euler_frequency(kprobe,uprobe)

    qualification={
      "Q01_STATIC_TRANSVERSE_SAMPLING": born["transverse_residual"]<tol["static_transverse_max_abs"],
      "Q02_STATIC_A2_RECOVERY": abs(born["A2_mean"]-THEORY_A2)/THEORY_A2<tol["static_A2_relative_error_max"],
      "Q03_FILAMENT_ORIENTATION_ISOTROPY": top["orientation_isotropy_fro"]<tol["orientation_isotropy_fro_max"],
      "Q04_INITIAL_HOPF_LINKING": top["initial_linking_abs_error_max"]<tol["initial_link_abs_error_max"],
      "Q05_UNLINKED_CONTROL": top["unlinked_control_link_abs_max"]<tol["unlinked_link_abs_max"],
      "Q06_HAMILTONIAN_ENERGY_DRIFT": top["base_energy_drift_rel_max"]<tol["energy_drift_rel_max"],
      "Q07_RK4_LOCAL_CONVERGENCE": top["rk4_one_step_vs_two_half_shape_rel"]<tol["rk4_local_convergence_rel_max"],
      "Q08_TIME_REVERSIBILITY": top["reversibility_shape_relative"]<tol["reversibility_shape_rel_max"],
      "Q09_OBJECTIVITY": top["objectivity_energy_relative_error"]<tol["objectivity_energy_rel_max"],
      "Q10_FILAMENT_RESOLUTION": top["max_segment_length_cv"]<tol["segment_length_cv_max"],
      "Q11_BARE_REST_EULER_NO_WAVE": rest_accel<1e-15,
    }; qualification={k:bool(v) for k,v in qualification.items()}

    linked_mu=top["static_linked"]["mu_over_rho_mean"]
    hypothesis={
      "H01_NONZERO_LINKED_FILAMENT_SHEAR_MODULUS": linked_mu>tol["modulus_min"],
      "H02_MODULUS_PERSISTS_UNDER_BIOT_SAVART": top["modulus_persistence_ratio_min"]>=tol["modulus_persistence_ratio_min"],
      "H03_MACRO_SHEAR_STRESS_PERSISTS": top["shear_stress_persistence_ratio_min"]>=tol["shear_stress_persistence_ratio_min"],
      "H04_TOPOLOGY_PRESERVED": top["link_change_abs_max"]<tol["link_change_abs_max"],
      "H05_TRANSVERSE_STIFFNESS_ISOTROPIC_AT_TESTED_ORDER": top["modulus_plane_spread_relative_max"]<=tol["modulus_plane_spread_rel_max"],
      "H06_CONSERVATIVE_REVERSIBLE_DYNAMICS": top["base_energy_drift_rel_max"]<tol["energy_drift_rel_max"] and top["stored_shear_energy_relative_drift_max"]<tol["stored_shear_energy_relative_drift_max"] and top["reversibility_shape_relative"]<tol["reversibility_shape_rel_max"],
      "H07_LINKING_IS_SPECIFIC_SOURCE_OF_MODULUS": abs(top["topological_linking_excess_fraction"])>=0.05,
    }; hypothesis={k:bool(v) for k,v in hypothesis.items()}

    core_set=all(hypothesis[k] for k in ["H01_NONZERO_LINKED_FILAMENT_SHEAR_MODULUS","H02_MODULUS_PERSISTS_UNDER_BIOT_SAVART","H03_MACRO_SHEAR_STRESS_PERSISTS","H04_TOPOLOGY_PRESERVED","H05_TRANSVERSE_STIFFNESS_ISOTROPIC_AT_TESTED_ORDER","H06_CONSERVATIVE_REVERSIBLE_DYNAMICS"])
    pipeline="PIPELINE_QUALIFIED" if all(qualification.values()) else "PIPELINE_FAILED"
    if pipeline!="PIPELINE_QUALIFIED": research="INCONCLUSIVE_NUMERICAL_QUALIFICATION_FAILED"
    elif core_set: research="SUPPORTED_FOR_REGULARIZED_LINKED_FILAMENT_MICROCELL_ENSEMBLE"
    else: research="NOT_SUPPORTED_FOR_V0.3.0_LINKED_FILAMENT_MICROCELL_ENSEMBLE"

    target=float(cfg["master_factor_wave_gate"]["target_cT_over_reference_speed"]); mtol=float(cfg["master_factor_wave_gate"]["absolute_tolerance"])
    ratio=top["static_linked"]["candidate_cT_over_reference_speed"]
    mf_mod="PASS" if abs(ratio-target)<=mtol else "FAIL"
    mf_persist="PASS" if hypothesis["H02_MODULUS_PERSISTS_UNDER_BIOT_SAVART"] and hypothesis["H03_MACRO_SHEAR_STRESS_PERSISTS"] else "FAIL"
    mf_geom="PASS" if top["required_spacing_over_R_for_master_target_by_density_scaling"]>=top["geometric_nonoverlap_min_spacing_over_R"] else "FAIL_TARGET_REQUIRES_CELL_OVERLAP"
    # A modulus supplies a conditional transverse-wave speed, but v0.3 does not claim an independently observed propagating pole.
    mf_wave="NOT_REACHED_NO_INDEPENDENT_BULK_WAVE_POLE_TEST"
    master="PASS" if mf_mod=="PASS" and mf_persist=="PASS" and mf_geom=="PASS" and mf_wave=="PASS" else "NOT_CLOSED"

    summary={
      "catalog_id":"A049","falsifier":"A049_isotropic_euler_vortex_shear_modulus_falsifier","version":cfg["version"],"blind":True,"backend":backend_name(),
      "pipeline_status":pipeline,"research_question_status":research,
      "scope_guard":"v0.3.0 replaces the random spectral background by explicit closed finite-core regularized Biot-Savart vortex filaments. The ensemble consists of independent Hopf-linked microcells with a preregistered effective cell volume; it is not yet a connected continuum vortex network. Positive shear curvature and stress persistence therefore qualify this microcell model, not all Euler fluids.",
      "static_born_carry_forward":born,"topological_filament_campaign":{k:v for k,v in top.items() if k not in ["dynamic_rows","modulus_rows","stress_rows","linked_static_rows","unlinked_static_rows"]},
      "qualification_gates":qualification,"hypothesis_gates":hypothesis,
      "linking_specific_interpretation":"NOT_SUPPORTED" if not hypothesis["H07_LINKING_IS_SPECIFIC_SOURCE_OF_MODULUS"] else "SUPPORTED",
      "master_factor_wave_gate":{"target_cT_over_reference_speed":target,"absolute_tolerance":mtol,"reference_speed_definition":cfg["master_factor_wave_gate"]["reference_speed_definition"],"MF01_PERSISTENT_MODULUS_SPEED_RATIO":mf_mod,"measured_cT_over_reference_speed":ratio,"MF02_PERSISTENCE":mf_persist,"MF03_NONOVERLAP_GEOMETRY":mf_geom,"required_spacing_over_R_for_target":top["required_spacing_over_R_for_master_target_by_density_scaling"],"minimum_nonoverlap_spacing_over_R":top["geometric_nonoverlap_min_spacing_over_R"],"MF04_INDEPENDENT_BULK_WAVE_POLE":mf_wave,"overall":master}
    }
    (out/"blind_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    _write_csv(out/"static_born_scan.csv",born["rows"])
    _write_csv(out/"linked_filament_static_shear_scan.csv",top["linked_static_rows"])
    _write_csv(out/"unlinked_filament_static_shear_scan.csv",top["unlinked_static_rows"])
    _write_csv(out/"filament_dynamic_persistence.csv",top["dynamic_rows"])
    _write_csv(out/"filament_modulus_by_plane.csv",top["modulus_rows"])
    _write_csv(out/"shear_relaxation_stress.csv",top["stress_rows"])
    _write_csv(out/"packing_sweep.csv",top["packing_sweep"])

    report=["# A049 v0.3.0 blind report","",f"Backend: **{summary['backend']}**",f"Pipeline: **{pipeline}**",f"Research question: **{research}**",f"Master-Factor Wave Closure: **{master}**","","## Explicit linked-filament microstructure","",f"- orientation isotropy Frobenius residual = {top['orientation_isotropy_fro']:.6e}",f"- initial Hopf |Lk|-1 max error = {top['initial_linking_abs_error_max']:.6e}",f"- link change max = {top['link_change_abs_max']:.6e}",f"- Hamiltonian energy drift = {top['base_energy_drift_rel_max']:.6e}",f"- forward/backward shape residual = {top['reversibility_shape_relative']:.6e}",f"- linked mu/rho = {linked_mu:.12e}",f"- c_T/v_ref = {ratio:.12e}",f"- max tested shear-plane spread = {top['modulus_plane_spread_relative_max']:.6e}",f"- modulus persistence min ratio = {top['modulus_persistence_ratio_min']:.6e}",f"- applied-shear stress persistence min ratio = {top['shear_stress_persistence_ratio_min']:.6e}",f"- stored shear-energy relative drift max = {top['stored_shear_energy_relative_drift_max']:.6e}",f"- linked-vs-unlinked modulus excess fraction = {top['topological_linking_excess_fraction']:.6e}","","## Master-Factor Wave Closure","",f"- MF01 persistent modulus speed ratio: {mf_mod}",f"- measured c_T/v_ref = {ratio:.12e}; target = {target:.12e}",f"- MF02 persistence: {mf_persist}",f"- MF03 non-overlap geometry: {mf_geom}",f"- target density scaling requires spacing/R = {top['required_spacing_over_R_for_master_target_by_density_scaling']:.6e}; non-overlap minimum = {top['geometric_nonoverlap_min_spacing_over_R']:.6e}",f"- MF04 independent bulk-wave pole: {mf_wave}",f"- overall: {master}","","## Qualification gates",""]
    for k,v in qualification.items(): report.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    report += ["","## Hypothesis gates",""]
    for k,v in hypothesis.items(): report.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    report += ["","## Scope guard","",summary["scope_guard"]]
    (out/"blind_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    return summary
