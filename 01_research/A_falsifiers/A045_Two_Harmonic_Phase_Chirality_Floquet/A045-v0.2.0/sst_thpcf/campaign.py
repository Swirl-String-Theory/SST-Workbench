from __future__ import annotations
import argparse, csv, json, math, os, zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from .geometry import load_curve, prepare_curve, rz, c3_geometry_residual
from .drive import c3_dynamic_symmetry_residual
from .dynamics import evolve
from .metrics import equivariance_residual, shape_metrics, curve_relative_error
from .provenance import anon_id, environment_manifest, source_leakage_audit, sha256_bytes

PACKAGE = "SST_Two_Harmonic_Phase_Chirality_Floquet_Blind_Falsifier"
VERSION = "v0.2.1"


def load_config(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def load_frozen_manifest(root: Path, rel: str) -> dict:
    return json.loads((root/rel).read_text())


def verify_frozen_inputs(root: Path, manifest: dict) -> dict:
    rows=[]
    for s in manifest["seeds"]:
        p=root/s["path"]
        got=sha256_bytes(p.read_bytes()) if p.exists() else None
        rows.append({"opaque_seed_id":s["opaque_seed_id"],"path":s["path"],"expected":s["sha256_raw_npy"],"actual":got,"pass":got==s["sha256_raw_npy"]})
    return {"pass":bool(rows) and all(r["pass"] for r in rows),"files":rows}


def seed_entries(root: Path, cfg: dict, frozen: dict) -> list[dict]:
    by_id={s["opaque_seed_id"]:s for s in frozen["seeds"]}
    ids=cfg.get("seed_ids") or list(by_id)
    out=[]
    for sid in ids:
        if sid not in by_id:
            raise KeyError(f"seed {sid} not in frozen manifest")
        rec=by_id[sid]
        out.append({"seed_id":sid,"path":root/rec["path"],"sha256":rec["sha256_raw_npy"]})
    return out


def condition_records(cfg: dict, seed_count: int) -> list[dict]:
    out=[]
    for seed_index in range(seed_count):
        for core_ratio in cfg["core_radius_over_ds_values"]:
            for chirality in ["COR","CNR"]:
                for phase_index, phase in enumerate(cfg["phases"]):
                    out.append({"seed_index":seed_index,"core_radius_over_ds":float(core_ratio),"chirality":chirality,"phase":float(phase),"phase_index":phase_index})
    return out


def local_cfg(base: dict, rec: dict) -> dict:
    x=dict(base); x.update(rec); return x


def temporal_pair_error(X0: np.ndarray, cfg: dict, duration: float, backend: str) -> float:
    c1=dict(cfg); c2=dict(cfg)
    c2["dt"]=0.5*float(c1["dt"])
    y1=evolve(X0,c1,backend=backend,duration=duration)
    y2=evolve(X0,c2,backend=backend,duration=duration)
    return curve_relative_error(y1-y1.mean(0), y2-y2.mean(0))


def utc_run_id() -> str:
    # Milliseconds plus PID make accidental collisions on rapid local reruns very unlikely.
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")[:18] + "Z"
    return f"{stamp}_p{os.getpid()}"


def allocate_output_dir(root: Path, run_id: str) -> tuple[Path, str]:
    """Allocate an output directory without deleting or mutating prior runs.

    The first run keeps the canonical v0.2.1 output directory.  If that path
    already exists (including a partially synced/locked Google Drive tree), a
    run-suffixed sibling is used.  Existing outputs are never removed.
    """
    canonical=root/f"{PACKAGE}_{VERSION}-outputs"
    if not canonical.exists():
        return canonical, "canonical_fresh"
    base=root/f"{canonical.name}_RUN_{run_id}"
    candidate=base
    n=2
    while candidate.exists():
        candidate=root/f"{base.name}_{n:02d}"
        n+=1
    return candidate, "preserved_existing_fallback"


def reveal_map_path(root: Path, outdir: Path) -> Path:
    return root/'private_reveal'/'reveal_maps'/f"{outdir.name}.json"


def allocate_archive_path(root: Path, suffix: str, run_id: str) -> Path:
    """Return a non-destructive archive path; never overwrite an old ZIP."""
    canonical=root/f"{PACKAGE}_{VERSION}-outputs_{suffix}.zip"
    if not canonical.exists():
        return canonical
    base=root/f"{PACKAGE}_{VERSION}-outputs_{suffix}_RUN_{run_id}.zip"
    candidate=base
    n=2
    while candidate.exists():
        candidate=root/f"{base.stem}_{n:02d}.zip"
        n+=1
    return candidate


def run(cfg_path: str | Path, backend: str = "python", root: str | Path = ".", reveal: bool = False) -> Path:
    root=Path(root).resolve(); cfg=load_config(cfg_path)
    run_id=utc_run_id()
    outdir, allocation_mode=allocate_output_dir(root,run_id)
    for d in ["certification","logs","data","figures"]: (outdir/d).mkdir(parents=True,exist_ok=False)

    frozen=load_frozen_manifest(root,cfg["frozen_manifest"])
    frozen_gate=verify_frozen_inputs(root,frozen)
    seeds=seed_entries(root,cfg,frozen)
    if not frozen_gate["pass"]: raise RuntimeError("frozen input hash gate failed")

    omega=float(cfg["omega"]); T=2*math.pi/omega
    base=dict(cfg); base["total_time"]=float(cfg["n_cycles"])*T; base["dt"]=T/float(cfg["steps_per_cycle"])
    salt=str(cfg["blind_salt"])

    drive_sym={chir:c3_dynamic_symmetry_residual(omega,cfg["a1"],cfg["a2"],0.371,chir) for chir in ["COR","CNR"]}
    rows=[]; reveal_map=[]; seed_descriptors=[]
    prepared=[]
    for s in seeds:
        X=prepare_curve(load_curve(s["path"]),int(cfg["n_points"]))
        prepared.append(X)
        seed_descriptors.append({"seed_token":anon_id({"seed_sha256":s["sha256"]},salt),"c3_geometry_residual":c3_geometry_residual(X),"n_points":len(X)})

    duration=float(cfg["equivariance_duration_cycles"])*T
    for rec in condition_records(cfg,len(prepared)):
        private={**rec,"seed_id":seeds[rec["seed_index"]]["seed_id"],"seed_sha256":seeds[rec["seed_index"]]["sha256"]}
        anon=anon_id(private,salt)
        local=local_cfg(base,rec)
        X0=prepared[rec["seed_index"]]
        R=rz(2*math.pi/3.0)
        Xa=evolve(X0,local,backend=backend,duration=duration,t_origin=0.0)
        X0r=X0@R.T
        Xb=evolve(X0r,local,backend=backend,duration=duration,t_origin=T/3.0)
        equiv=equivariance_residual(Xa,Xb,2*math.pi/3.0)
        m=shape_metrics(X0,Xa)
        rows.append({"anonymous_id":anon,"equivariance_residual":equiv,**m})
        reveal_map.append({"anonymous_id":anon,**private})

    eq=np.array([r["equivariance_residual"] for r in rows],float)
    order=np.argsort(eq); half=len(eq)//2
    low=eq[order[:half]]; high=eq[order[half:]]
    separation=float(np.median(high)/(np.median(low)+1e-30)); low_max=float(np.max(low))

    # Frozen, label-independent numerical check on first seed and a preregistered internal condition.
    cert_cfg=dict(base); cert_cfg.update({"phase":float(cfg["certification_phase"]),"chirality":"CNR","core_radius_over_ds":float(cfg["certification_core_radius_over_ds"])})
    temporal_err=temporal_pair_error(prepared[0],cert_cfg,float(cfg["certification_duration_cycles"])*T,backend)

    audit=source_leakage_audit(root)
    gates={
        "G0_source_leakage":{"pass":audit["pass"],"n_hits":len(audit["hits"])},
        "G1_frozen_input_hashes":{"pass":frozen_gate["pass"],"n":len(frozen_gate["files"])},
        "G2_one_drive_class_exact_C3":{"blind_value_min":float(min(drive_sym.values())),"threshold":cfg["gate_drive_symmetry_residual_max"],"pass":min(drive_sym.values())<=cfg["gate_drive_symmetry_residual_max"]},
        "G3_finite_core_equivariance_low_branch":{"value":low_max,"threshold":cfg["gate_equivariance_residual_max"],"pass":low_max<=cfg["gate_equivariance_residual_max"]},
        "G4_blind_control_separation":{"value":separation,"threshold_min":cfg["gate_control_separation_min"],"pass":separation>=cfg["gate_control_separation_min"]},
        "G5_temporal_refinement":{"value":temporal_err,"threshold":cfg["gate_temporal_pair_error_max"],"pass":temporal_err<=cfg["gate_temporal_pair_error_max"]},
        "G6_length_drift":{"value":float(max(abs(r["length_rel_drift"]) for r in rows)),"threshold":cfg["gate_length_rel_drift_max"],"pass":max(abs(r["length_rel_drift"]) for r in rows)<=cfg["gate_length_rel_drift_max"]},
        "G7_mesh_quality":{"value":float(max(r["segment_cv_final"] for r in rows)),"threshold":cfg["gate_segment_cv_max"],"pass":max(r["segment_cv_final"] for r in rows)<=cfg["gate_segment_cv_max"]},
    }
    numerics="PASS" if all(g["pass"] for g in gates.values()) else "FAIL"
    physics="UNTESTED"
    formal_floquet="SKIP_NO_CERTIFIED_RPO"

    with (outdir/'data'/'blind_metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    (outdir/'data'/'seed_descriptors_blind.json').write_text(json.dumps(seed_descriptors,indent=2))
    (outdir/'certification'/'frozen_input_hash_gate.json').write_text(json.dumps(frozen_gate,indent=2))
    (outdir/'certification'/'leakage_audit.json').write_text(json.dumps(audit,indent=2))

    manifest={
        "package":PACKAGE,"version":VERSION,"backend":backend,"blind":True,"dimensionless":True,
        "sst_constants_used":False,
        "model_scope":"regularized finite-core nonlocal filament surrogate plus two-colour trace-free strain coupling",
        "floquet_claim_authorized":False,
        "run_id":run_id,
        "output_directory":outdir.name,
        "output_allocation_mode":allocation_mode,
        "output_policy":"non-destructive; prior output directories are never removed or overwritten",
        "environment":environment_manifest(),
        "config":{k:v for k,v in cfg.items() if k!="blind_salt"},
    }
    (outdir/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (outdir/'summary.json').write_text(json.dumps({"numerics_verdict":numerics,"physics_verdict":physics,"gates":gates,"formal_floquet":formal_floquet},indent=2))
    report=[f"# {PACKAGE} {VERSION}","",f"Numerics: **{numerics}**",f"Physics: **{physics}**",f"Backend: `{backend}`","","## Gates"]
    report += [f"- {k}: {'PASS' if v['pass'] else 'FAIL'} — {v}" for k,v in gates.items()]
    report += ["","## Floquet gate",formal_floquet,"","No Floquet multipliers are emitted in this release. A certified periodic or relative-periodic orbit is an upstream prerequisite."]
    (outdir/'REPORT.md').write_text("\n".join(report)+"\n")

    seal_entries=[]
    for p in sorted(outdir.rglob('*')):
        if p.is_file(): seal_entries.append({"file":str(p.relative_to(outdir)),"sha256":sha256_bytes(p.read_bytes())})
    (outdir/'BLIND_SEAL.json').write_text(json.dumps({"files":seal_entries},indent=2))

    private=root/'private_reveal'/'reveal_maps'; private.mkdir(parents=True,exist_ok=True)
    rm_path=reveal_map_path(root,outdir)
    rm_path.write_text(json.dumps(reveal_map,indent=2))
    if reveal:
        by_id={m["anonymous_id"]:m for m in reveal_map}
        revealed=[{**r,**{k:v for k,v in by_id[r["anonymous_id"]].items() if k!="anonymous_id"}} for r in rows]
        (outdir/'REVEALED_metrics.json').write_text(json.dumps(revealed,indent=2))
        stats={}
        for chir in ["COR","CNR"]:
            vals=[r["equivariance_residual"] for r in revealed if r["chirality"]==chir]
            stats[chir]={"median_equivariance_residual":float(np.median(vals)),"max":float(np.max(vals)),"min":float(np.min(vals))}
        (outdir/'REVEALED_summary.json').write_text(json.dumps({"arm_stats":stats,"analytic_drive_symmetry_residual":drive_sym},indent=2))

    return outdir


def make_zip(outdir: Path, reveal: bool) -> Path:
    suffix="REVEALED" if reveal else "BLIND"
    run_id=outdir.name.split("_RUN_",1)[1] if "_RUN_" in outdir.name else utc_run_id()
    zpath=allocate_archive_path(outdir.parent,suffix,run_id)
    with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(outdir.rglob('*')):
            if not p.is_file(): continue
            if not reveal and p.name.startswith('REVEALED'): continue
            z.write(p,p.relative_to(outdir.parent))
        if reveal:
            rm=reveal_map_path(outdir.parent,outdir)
            if rm.exists(): z.write(rm,rm.relative_to(outdir.parent))
    (zpath.with_suffix(zpath.suffix+'.sha256')).write_text(sha256_bytes(zpath.read_bytes())+'  '+zpath.name+'\n')
    return zpath


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--backend',choices=['python','native'],default='python'); ap.add_argument('--root',default='.'); ap.add_argument('--reveal',action='store_true'); ap.add_argument('--package',action='store_true')
    a=ap.parse_args(); out=run(a.config,a.backend,a.root,reveal=a.reveal); print(out)
    if a.package:
        print(make_zip(out,False))
        if a.reveal: print(make_zip(out,True))

if __name__=='__main__': main()
