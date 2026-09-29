from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, shutil

from .dataset import collect_candidates
from .blind import prepare_blind
from .analysis import run_blind
from .reveal import reveal
from .package_outputs import package
from .phase_data import (
    reconstruct_phase_from_population,
    digitize_fig2_population,
    digitize_fig3_experimental_phase,
    specific_action_from_cubic,
)
from .fluid_data import prepare_fluid_measurement

def load_cfg(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def _dump(path: Path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")

def prepare_qgi(root: Path, cfg: dict) -> dict:
    out=root/f"{cfg['project_name']}-outputs"/"blind"/"qgi_phase"
    out.mkdir(parents=True,exist_ok=True)
    qcfg=cfg["qgi_phase_data"]
    raw=root/qcfg["raw_population_csv"]
    pdf=root/qcfg["public_pdf"]
    g_eff=float(qcfg["g_eff_m_s2"])
    sigma_g=qcfg.get("sigma_g_eff_m_s2")
    sigma_g=None if sigma_g in (None,"") else float(sigma_g)

    if raw.exists():
        fit=reconstruct_phase_from_population(
            raw,out,
            envelope_degree=int(qcfg.get("envelope_degree",7)),
            phase_degree=3,
            exclude_edge_cycles=int(qcfg.get("exclude_edge_cycles",1)),
        )
        sa=specific_action_from_cubic(fit["cubic_coeff_rad_s3_inv"],g_eff,fit.get("sigma_cubic_coeff_rad_s3_inv"),sigma_g)
        result={
            "format":"SST-QGI-SPECIFIC-ACTION-DATA-2.0",
            "status":"READY",
            "source_grade":"RAW_POPULATION_CSV",
            "input":str(raw.relative_to(root)),
            "input_sha256":sha256_file(raw),
            **sa,
            "phase_reconstruction":fit,
            "note":(
                "Phase reconstructed in-pipeline from population-vs-2T data. "
                "No Planck target and no particle mass are used in the specific-action inference."
            ),
        }
    elif pdf.exists() and bool(qcfg.get("allow_public_figure_fallback",True)):
        # Preferred public fallback: digitize Fig.2 population markers and rerun
        # the published-style phase extraction ourselves.
        try:
            pop_csv=out/"figure2_population_digitized.csv"
            dig=digitize_fig2_population(
                pdf,pop_csv,
                page_index=int(qcfg.get("figure2_page_index",11)),
                x_min_ms=float(qcfg.get("figure2_x_min_ms",0.35)),
                x_max_ms=float(qcfg.get("figure2_x_max_ms",2.40)),
                y_min_percent=float(qcfg.get("figure2_y_min_percent",10.0)),
                y_max_percent=float(qcfg.get("figure2_y_max_percent",90.0)),
                axes_bbox_norm=tuple(qcfg.get("figure2_axes_bbox_norm",[0.170,0.091,0.785,0.297])),
            )
            _dump(out/"figure2_digitization.json",dig)
            fit=reconstruct_phase_from_population(
                pop_csv,out,
                envelope_degree=int(qcfg.get("envelope_degree",7)),
                phase_degree=3,
                exclude_edge_cycles=int(qcfg.get("exclude_edge_cycles",1)),
            )
            sa=specific_action_from_cubic(fit["cubic_coeff_rad_s3_inv"],g_eff,fit.get("sigma_cubic_coeff_rad_s3_inv"),sigma_g)
            result={
                "format":"SST-QGI-SPECIFIC-ACTION-DATA-2.0",
                "status":"READY",
                "source_grade":"PUBLISHED_FIGURE2_POPULATION_DIGITIZED",
                "input":str(pdf.relative_to(root)),
                "input_sha256":sha256_file(pdf),
                **sa,
                "digitization":dig,
                "phase_reconstruction":fit,
                "note":(
                    "Public-data fallback: population markers digitized from Fig.2, then phase "
                    "recomputed in-pipeline. This is closer to the raw observable than Fig.3, "
                    "but it is still not author-level numerical raw data and remains CONDITIONAL."
                ),
            }
        except Exception as fig2_exc:
            # Secondary fallback: use the published experimental phase-fit line.
            digitized=out/"figure3_experimental_phase_digitized.csv"
            fit=digitize_fig3_experimental_phase(
                pdf,digitized,
                page_index=int(qcfg.get("figure3_page_index",12)),
                x_min_ms=float(qcfg.get("figure3_x_min_ms",0.25)),
                x_max_ms=float(qcfg.get("figure3_x_max_ms",2.50)),
                y_min_rad=float(qcfg.get("figure3_y_min_rad",0.0)),
                y_max_rad=float(qcfg.get("figure3_y_max_rad",100.0)),
                axes_bbox_norm=tuple(qcfg.get("figure3_axes_bbox_norm",[0.173,0.089,0.745,0.292])),
            )
            _dump(out/"figure3_digitization.json",fit)
            sa=specific_action_from_cubic(fit["cubic_coeff_rad_s3_inv"],g_eff,None,sigma_g)
            result={
                "format":"SST-QGI-SPECIFIC-ACTION-DATA-2.0",
                "status":"READY",
                "source_grade":"PUBLISHED_FIGURE3_DATA_FIT_DIGITIZED",
                "input":str(pdf.relative_to(root)),
                "input_sha256":sha256_file(pdf),
                **sa,
                "digitization":fit,
                "figure2_failure":f"{type(fig2_exc).__name__}: {fig2_exc}",
                "note":(
                    "Secondary public-data fallback: digitized from the experimental-data fit line "
                    "in Fig.3A because Fig.2 population digitization did not qualify. "
                    "This is not raw author numerical data and remains CONDITIONAL."
                ),
            }
    else:
        result={
            "format":"SST-QGI-SPECIFIC-ACTION-DATA-2.0",
            "status":"NOT_RUN",
            "source_grade":None,
            "mass_used":False,
            "planck_target_used":False,
            "kg_unit_used":False,
            "note":(
                "No machine-readable raw population CSV is bundled because none was identified in the "
                "paper/supplement. Put author/raw data at the configured raw_population_csv path, or "
                "run run_fetch_qgi_public_pdf.cmd for the published-figure fallback."
            ),
        }
    _dump(out/"qgi_specific_action.json",result)
    return result

def prepare_fluid(root: Path, cfg: dict) -> dict:
    fcfg=cfg["fluid_action_data"]
    loop=root/fcfg["raw_circulation_loop_csv"]
    prov=root/fcfg["circulation_provenance_json"]
    prepared=root/fcfg["prepared_circulation_json"]
    status_path=root/f"{cfg['project_name']}-outputs"/"blind"/"fluid_action"/"fluid_prepare_status.json"
    if loop.exists() and prov.exists():
        result=prepare_fluid_measurement(loop,prov,prepared)
        status={"status":"READY",**result}
    else:
        # Never allow a stale prepared circulation result to survive after its
        # raw/provenance inputs have been removed.
        if prepared.exists():
            prepared.unlink()
        status={
            "status":"NOT_RUN",
            "raw_loop_exists":loop.exists(),
            "provenance_exists":prov.exists(),
            "note":(
                "Provide a raw velocity-loop CSV and an explicit provenance declaration. "
                "Canonical SST Gamma0 is intentionally not substituted into the primary gate."
            ),
        }

    # Optional absolute geometry/fluid scale. This never upgrades the primary
    # specific-action gate because SI kg-based absolute action is metrology dependent.
    raw_abs=root/fcfg.get("raw_absolute_scale_json","data/fluid/raw/absolute_fluid_scale.json")
    prepared_abs=root/fcfg.get("absolute_scale_json","data/fluid/prepared/absolute_fluid_scale.json")
    if raw_abs.exists():
        obj=json.loads(raw_abs.read_text(encoding="utf-8"))
        required=("rho_kg_m3","a_core_m","status","depends_on_h","depends_on_hbar",
                  "depends_on_compton_radius","depends_on_electron_mass","depends_on_alpha")
        missing=[k for k in required if k not in obj]
        if missing:
            raise ValueError(f"Absolute fluid scale missing fields: {missing}")
        prepared_abs.parent.mkdir(parents=True,exist_ok=True)
        prepared_abs.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")
        status["absolute_scale_prepared"]=True
    else:
        if prepared_abs.exists():
            prepared_abs.unlink()
        status["absolute_scale_prepared"]=False

    _dump(status_path,status)
    return status

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)

    for name in ("prepare","prepare-qgi","prepare-fluid","basic","extended","reveal"):
        p=sub.add_parser(name)
        p.add_argument("--config",default="configs/basic.json")
    p=sub.add_parser("package")
    p.add_argument("--config",default="configs/basic.json")
    p=sub.add_parser("clean")
    p.add_argument("--config",default="configs/basic.json")

    args=ap.parse_args()
    root=Path.cwd()
    cfg=load_cfg(args.config)
    out=root/f"{cfg['project_name']}-outputs"

    if args.cmd=="prepare":
        # Preserve independently prepared QGI/fluid stage outputs if rerunning geometry prepare.
        saved_qgi=None
        saved_fluid=None
        if (out/"blind"/"qgi_phase").exists():
            saved_qgi=root/"._qgi_phase_tmp"
            if saved_qgi.exists(): shutil.rmtree(saved_qgi)
            shutil.copytree(out/"blind"/"qgi_phase",saved_qgi)
        if (out/"blind"/"fluid_action").exists():
            saved_fluid=root/"._fluid_action_tmp"
            if saved_fluid.exists(): shutil.rmtree(saved_fluid)
            shutil.copytree(out/"blind"/"fluid_action",saved_fluid)

        if (out/"blind").exists():
            shutil.rmtree(out/"blind")
        if (root/"private").exists():
            shutil.rmtree(root/"private")
        candidates,audit=collect_candidates(cfg)
        manifest=prepare_blind(candidates,out/"blind",root/"private",audit)

        if saved_qgi and saved_qgi.exists():
            shutil.copytree(saved_qgi,out/"blind"/"qgi_phase",dirs_exist_ok=True)
            shutil.rmtree(saved_qgi)
        if saved_fluid and saved_fluid.exists():
            shutil.copytree(saved_fluid,out/"blind"/"fluid_action",dirs_exist_ok=True)
            shutil.rmtree(saved_fluid)

        print(json.dumps({
            "format":manifest["format"],
            "n_candidates":manifest["n_candidates"],
            "n_blind_strata":manifest["n_blind_strata"],
            "private_key_commitment_sha256":manifest["private_key_commitment_sha256"],
            "source_identity_read":False,
        },indent=2))
    elif args.cmd=="prepare-qgi":
        print(json.dumps(prepare_qgi(root,cfg),indent=2))
    elif args.cmd=="prepare-fluid":
        print(json.dumps(prepare_fluid(root,cfg),indent=2))
    elif args.cmd in ("basic","extended"):
        r=run_blind(cfg,root,args.cmd)
        print(json.dumps({
            "mode":args.cmd,
            "backend":r["backend"],
            "n_candidates":r["n_candidates"],
            "blind_verdict":r["blind_verdict"],
            "source_identity_read":False,
        },indent=2))
    elif args.cmd=="reveal":
        r=reveal(root,cfg)
        print(json.dumps(r,indent=2))
    elif args.cmd=="package":
        a,b=package(root,cfg["project_name"])
        print(a)
        if b is not None: print(b)
    elif args.cmd=="clean":
        if out.exists(): shutil.rmtree(out)
        if (root/"private").exists(): shutil.rmtree(root/"private")
        print("cleaned")

if __name__=="__main__":
    main()
