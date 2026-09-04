from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
import csv, json, math, os, shutil, time
from typing import Any
import numpy as np

from .geometry import CurveRecord, centered_unit_rms, discover_knot_files, geometry_metrics, load_curves, resample_uniform
from .modes import ModeCandidate, decompose_rigid_velocity, generate_mode_candidates, project_shape_modes
from .native_ext import backend_info, biot_savart_velocity, min_segment_distance, require_native, writhe_midpoint

@dataclass(frozen=True)
class Preset:
    name: str
    resample_n: int
    max_m: int
    orientations_deg: tuple[float,...]
    impact_R: tuple[float,...]
    separations_R: tuple[float,...]
    core_fraction: float
    pairing: str
    max_files: int | None

PRESETS={
    "basic": Preset("basic",300,6,(0.0,),(0.0,),(3.5,),0.075,"self",None),
    "extended": Preset("extended",1200,16,(0.0,45.0,90.0,135.0),(0.0,0.35),(3.0,4.0),0.05,"self",None),
}

def _write_csv(path:Path,rows:list[dict[str,Any]],fieldnames:list[str]|None=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    if fieldnames is None:
        keys=[]; seen=set()
        for r in rows:
            for k in r:
                if k not in seen: seen.add(k); keys.append(k)
        fieldnames=keys
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames,extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def _write_json(path:Path,obj:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")

def _rot_z(points:np.ndarray,deg:float)->np.ndarray:
    a=math.radians(deg); c=math.cos(a); s=math.sin(a)
    R=np.array([[c,-s,0.0],[s,c,0.0],[0.0,0.0,1.0]])
    return np.asarray(points)@R.T

def _place_pair(target:np.ndarray,source:np.ndarray,orientation_deg:float,impact_R:float,separation_R:float):
    A=np.asarray(target,float).copy(); B=_rot_z(np.asarray(source,float),orientation_deg)
    A=A+np.array([-0.5*separation_R,0.0,0.0]); B=B+np.array([0.5*separation_R,impact_R,0.0])
    return A,B

def _writhe_directional_derivative(points:np.ndarray,shape_velocity:np.ndarray,closed:bool=True)->float:
    v=np.asarray(shape_velocity,float); rms=float(np.sqrt(np.mean(np.sum(v*v,axis=1))))
    if rms<=1e-300: return 0.0
    eps=1e-4
    p2=np.asarray(points,float)+(eps/rms)*v
    return (float(writhe_midpoint(p2,closed))-float(writhe_midpoint(points,closed)))/eps

def _curve_key(rec:CurveRecord)->str:
    return rec.knot_id

def _interaction_one(task:tuple,mode_map:dict[str,list[ModeCandidate]],curve_map:dict[str,tuple[np.ndarray,bool]],core_fraction:float)->dict[str,Any]:
    target_id,source_id,ori,impact,sep=task
    A0,closedA=curve_map[target_id]; B0,closedB=curve_map[source_id]
    A,B=_place_pair(A0,B0,ori,impact,sep)
    vel=np.asarray(biot_savart_velocity(B,A,gamma=1.0,core_radius=core_fraction,source_closed=closedB),float)
    dec=decompose_rigid_velocity(A,vel)
    proj=project_shape_modes(dec["v_shape"],mode_map[target_id])
    min_d=float(min_segment_distance(A,B,closedA,closedB))
    wrd=_writhe_directional_derivative(A,dec["v_shape"],closedA) if closedA else float("nan")
    vrms=float(np.sqrt(np.mean(np.sum(vel*vel,axis=1))))
    srms=float(np.sqrt(np.mean(np.sum(dec["v_shape"]**2,axis=1))))
    return {
        "knot_target":target_id,"knot_source":source_id,"orientation_deg":ori,"impact_parameter_R":impact,"separation_R":sep,
        "core_radius_R":core_fraction,"gamma_proxy":1.0,"velocity_rms_proxy":vrms,"shape_velocity_rms_proxy":srms,
        "translation_fraction":dec["translation_fraction"],"rotation_fraction":dec["rotation_fraction"],"shape_fraction":dec["shape_fraction"],
        "mode_capture_fraction":proj["captured_fraction"],"dominant_mode_id":proj["dominant_mode_id"],"dominant_mode_fraction":proj["dominant_mode_fraction"],
        "writhe_directional_response_per_Rrms":wrd,"min_segment_distance_R":min_d,
        "interpretation":"REGULARIZED_BIOT_SAVART_GEOMETRIC_COUPLING_PROXY_NOT_ENERGY_NOT_GAP"
    }

def _make_v01_skeleton(out:Path, mode_rows:list[dict[str,Any]]):
    sk=out/"v01_physical_campaign_skeleton"; sk.mkdir(parents=True,exist_ok=True)
    modes=[]
    for r in mode_rows:
        modes.append({"knot":r["knot"],"mode_id":r["mode_id"],"family":"kelvin","omega_rad_s":"","gap_eV":"","gap_status":"unknown",
                      "coupling_norm":"","tau_s":"","degeneracy":1,"independent_energy_channel":"false",
                      "notes":"v0.2 geometry candidate only; physical omega/gap/coupling must come from declared solver/experiment"})
    _write_csv(sk/"modes.csv",modes,["knot","mode_id","family","omega_rad_s","gap_eV","gap_status","coupling_norm","tau_s","degeneracy","independent_energy_channel","notes"])
    headers={
        "amplitude_scan.csv":["knot","mode_id","amplitude","delta_energy_eV"],
        "encounters.csv":["knot","mode_id","interaction_id","drive_energy_eV","delta_energy_eV","noise_eV","duration_s"],
        "convergence.csv":["knot","mode_id","resolution","omega_rad_s","coupling_norm","gap_eV"],
        "spectroscopy.csv":["observable_id","knot","mode_id","lambda_abs","occupation","delta_energy_eV","empirical_limit_eV"],
        "orientation.csv":["knot","tx","ty","tz","weight"],
        "momenta.csv":["knot","cx","cy","cz","M_kg","number_density_m3","weight"],
        "energy_ledger.csv":["interaction_id","knot_pair","delta_E_CM_eV","delta_E_rot_eV","delta_E_kelvin_eV","delta_E_twist_eV","delta_E_core_eV","total_energy_drift_eV","initial_total_energy_eV","delta_Wr"],
    }
    for name,h in headers.items(): _write_csv(sk/name,[],h)
    cfg={
      "campaign_id":"EDIT_ME_physical_campaign","dataset_kind":"physical","temperature_K":300.0,"observation_time_s":1.0,"drive_energy_eV":0.0,
      "model_capabilities":{"finite_core_resolved":False,"material_frame_resolved":False},
      "thresholds":{"coupling_sigma_threshold":5.0,"min_transfer_fraction":1e-4,"coupling_norm_threshold":1e-4,"gap_abs_floor_eV":1e-12,"gap_rel_intercept_tol":0.05,"convergence_rel_tol":0.02,"energy_conservation_rel_tol":1e-8,"isotropy_Q_frobenius_limit":0.05}
    }
    _write_json(sk/"config.json",cfg)

def run_workflow(knots_dir:Path,out_dir:Path,preset_name:str="basic",threads:int=1,pairing:str|None=None,require_cpp:bool=False,max_files:int|None=None)->dict[str,Any]:
    if preset_name not in PRESETS: raise ValueError(f"Unknown preset {preset_name}")
    pre=PRESETS[preset_name]; pairing=pairing or pre.pairing
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    info=require_native(verbose=True) if require_cpp else backend_info(verbose=False)
    files=discover_knot_files(Path(knots_dir))
    if max_files is None: max_files=pre.max_files
    if max_files is not None: files=files[:max_files]
    if not files: raise RuntimeError(f"No supported knot files found under {knots_dir}")
    discovery=[]; recs=[]; parse_errors=[]
    for p in files:
        try:
            curves=load_curves(p); recs.extend(curves)
            discovery.append({"file":str(p),"status":"OK","components":len(curves)})
        except Exception as exc:
            discovery.append({"file":str(p),"status":"PARSE_FAIL","components":0,"error":str(exc)}); parse_errors.append((str(p),str(exc)))
    if not recs: raise RuntimeError("Files were found but none could be parsed as curves")
    _write_csv(out/"discovered_files.csv",discovery)

    geom_rows=[]; resampled={}; normalized={}; mode_map={}; mode_rows=[]
    for rec in recs:
        row,p=geometry_metrics(rec,pre.resample_n); geom_rows.append(row); resampled[rec.knot_id]=(p,rec.closed)
        q,center,rms=centered_unit_rms(p); normalized[rec.knot_id]=(q,rec.closed)
        modes=generate_mode_candidates(q,pre.max_m); mode_map[rec.knot_id]=modes
        for m in modes:
            mode_rows.append({"knot":rec.knot_id,"mode_id":m.mode_id,"family":m.family,"m":m.m,"phase":m.phase,"polarization":m.polarization,
                              "roughness_lambda_per_R2":m.roughness_lambda,"retained_norm_fraction":m.retained_norm,
                              "omega_rad_s":"","gap_eV":"","status":"GEOMETRY_CANDIDATE_NOT_EIGENMODE"})
        # Persist resampled, unit-RMS centerline for reproducibility.
        rp=out/"resampled_unit_rms"/f"{rec.knot_id}.csv"; rp.parent.mkdir(exist_ok=True)
        _write_csv(rp,[{"x":x,"y":y,"z":z} for x,y,z in q],["x","y","z"])
    _write_csv(out/"geometry_metrics.csv",geom_rows)
    _write_csv(out/"mode_candidates.csv",mode_rows)
    family_rows=[
        {"family":"translation","status":"RESOLVED_KINEMATIC","quantity":"center-of-mass component of induced velocity","gap_status":"NOT_APPLICABLE_AS_INTERNAL_GAP"},
        {"family":"orientation","status":"RESOLVED_KINEMATIC","quantity":"best-fit global angular velocity / rigid rotation","gap_status":"NOT_DERIVED"},
        {"family":"kelvin","status":"GEOMETRY_CANDIDATE_ONLY","quantity":"rigid-projected normal Fourier deformation basis","gap_status":"UNKNOWN_REQUIRES_PHYSICAL_ENERGY_FUNCTIONAL"},
        {"family":"writhe","status":"GEOMETRIC_OBSERVABLE","quantity":"directional writhe response under residual shape velocity","gap_status":"NOT_AN_INDEPENDENT_MODE_BY_DEFAULT"},
        {"family":"twist","status":"UNAVAILABLE_CENTERLINE_ONLY","quantity":"requires resolved material frame","gap_status":"UNKNOWN"},
        {"family":"core","status":"UNAVAILABLE_CENTERLINE_ONLY","quantity":"requires resolved finite-core field","gap_status":"UNKNOWN"},
    ]
    _write_csv(out/"mode_family_capabilities.csv",family_rows)

    ids=sorted(normalized)
    pairs=[]
    if pairing=="self": pairs=[(k,k) for k in ids]
    elif pairing=="all": pairs=[(a,b) for a in ids for b in ids]
    elif pairing=="unique": pairs=[(ids[i],ids[j]) for i in range(len(ids)) for j in range(i,len(ids))]
    else: raise ValueError("pairing must be self, all, or unique")
    tasks=[(a,b,o,imp,sep) for a,b in pairs for o in pre.orientations_deg for imp in pre.impact_R for sep in pre.separations_R]
    interaction=[]; t0=time.perf_counter()
    if threads<=1:
        for task in tasks: interaction.append(_interaction_one(task,mode_map,normalized,pre.core_fraction))
    else:
        with ThreadPoolExecutor(max_workers=threads) as ex:
            futs=[ex.submit(_interaction_one,t,mode_map,normalized,pre.core_fraction) for t in tasks]
            for f in as_completed(futs): interaction.append(f.result())
    interaction.sort(key=lambda r:(r["knot_target"],r["knot_source"],r["orientation_deg"],r["impact_parameter_R"],r["separation_R"]))
    elapsed=time.perf_counter()-t0
    _write_csv(out/"interaction_coupling_proxy.csv",interaction)
    _make_v01_skeleton(out,mode_rows)

    summary={
        "package":"1_Maxwell_SST_Kinetic_Falsifier_v0.2.0","preset":preset_name,"knots_dir":str(knots_dir),"out_dir":str(out),
        "backend":info,"threads":threads,"pairing":pairing,"files_discovered":len(files),"curves_parsed":len(recs),"parse_failures":len(parse_errors),
        "resample_n":pre.resample_n,"max_fourier_m":pre.max_m,"mode_candidates":len(mode_rows),"interaction_probes":len(interaction),
        "interaction_elapsed_s":elapsed,"interpretation_guard":(
            "v0.2 generates geometry candidates and regularized Biot-Savart coupling PROXIES. It does not derive physical mode energies, true gaps, "
            "thermodynamic contributions, or spectroscopic shifts. Those remain inputs to the v0.1-compatible falsifier skeleton from a declared physical solver/experiment."),
        "centerline_capability":"translation + orientation + Kelvin/shape + writhe response available; twist/core unavailable without resolved material frame/finite core"
    }
    _write_json(out/"backend.json",info)
    _write_json(out/"workflow_summary.json",summary)
    (out/"README_RESULTS.md").write_text(
        f"# Maxwell-SST v0.2 workflow results\n\nPreset: `{preset_name}`  \nBackend: `{info['backend']}`  \nCurves: {len(recs)}  \nInteraction probes: {len(interaction)}\n\n"
        "## Interpretation guard\n\n"+summary["interpretation_guard"]+"\n\n"
        "- `geometry_metrics.csv`: resolved centerline geometry and writhe convergence diagnostic.\n"
        "- `mode_candidates.csv`: rigid-projected normal Fourier deformation basis; **not yet physical eigenmodes**.\n"
        "- `interaction_coupling_proxy.csv`: instantaneous regularized Biot-Savart response of a displaced second curve.\n"
        "- `v01_physical_campaign_skeleton/`: blank physical-energy/gap tables for the strict falsifier layer.\n",encoding="utf-8")
    return summary
