from __future__ import annotations
import json, math, platform, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

from .paths import detect_workbench_root, find_e011_seedset, find_c006_version
from .seed import load_gilbert_anchor, sample_gilbert
from .c006_bridge import import_c006, provenance as c006_provenance
from .scale import load_scale_contract, make_physical_candidate
from .util import dump_json, polygon_length, relative_shift, centered_slopes, sha256_file

def _complex_rows(values):
    return [{"re":float(complex(z).real),"im":float(complex(z).imag)} for z in values]

def run(root: Path, *, workbench_root=None, preset="quick", force_python=False,
        physical_scale_path: Path | None=None):
    root=Path(root).resolve()
    cfg=json.loads((root/"configs/frozen_policy.json").read_text(encoding="utf-8"))
    if preset not in cfg["presets"]:
        raise ValueError("preset must be quick or full")
    pcfg=cfg["presets"][preset]
    workbench=detect_workbench_root(workbench_root)
    out=root/"outputs"
    out.mkdir(parents=True,exist_ok=True)

    seedset=find_e011_seedset(workbench,cfg["topology_id"])
    sel=load_gilbert_anchor(
        seedset,workbench,
        provider_preferences=tuple(cfg["e011_provider_preference"]),
        expected_reference_id=cfg["gilbert_reference_id"],
    )
    model=sel["model"]

    c006_root=find_c006_version(workbench)
    dynamics,spectral=import_c006(c006_root)

    run_context={
        "schema":"E012-RUN-CONTEXT-1.0",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "python":sys.version,
        "platform":platform.platform(),
        "workbench_root":str(workbench),
        "preset":preset,
        "force_python":bool(force_python),
        "frozen_policy_sha256":sha256_file(root/"configs/frozen_policy.json"),
        "e011_seedset_path":str(seedset),
        "e011_seedset_sha256":sha256_file(seedset),
        "c006_root":str(c006_root),
    }
    dump_json(out/"E012_RUN_CONTEXT.json",run_context)

    selected={
        "topology_id":"3_1",
        "static_status":sel["summary"].get("static_status"),
        "static_ready":sel["summary"].get("static_ready"),
        "anchor":sel["anchor"],
        "resolved_source_path":str(sel["source_path"]),
        "resolved_source_sha256":sel["source_sha256"],
        "gilbert_record":{
            "id":model.knot_id,
            "conway":model.conway,
            "L_header":model.L,
            "D_header":model.D,
            "harmonic_count":len(model.harmonics),
        },
    }
    dump_json(out/"E011_SELECTED_SEED.json",selected)
    dump_json(out/"C006_PROVENANCE.json",c006_provenance(c006_root))

    n_ladder=[int(x) for x in pcfg["n_ladder"]]
    mmax=int(pcfg["mode_m_max"])
    reltol=float(pcfg["stable_root_relative_shift_max"])
    levels=[]
    per_mode={m:[] for m in range(1,mmax+1)}
    failures=[]

    for N in n_ladder:
        center=sample_gilbert(model,N)
        L=polygon_length(center)
        for m in range(1,mmax+1):
            try:
                a=dynamics.projected_kelvin_analysis(
                    center,
                    D=float(model.D),
                    offset_over_D=float(cfg["offset_over_D"]),
                    eps_over_D=float(cfg["eps_over_D"]),
                    fd_step_over_D=float(cfg["fd_step_over_D"]),
                    gamma_plus=float(cfg["gamma_plus_hat"]),
                    gamma_minus=float(cfg["gamma_minus_hat"]),
                    channel_phase=float(cfg["channel_phase_rad"]),
                    basis_phase=float(cfg["basis_phase_rad"]),
                    mode_m=m,
                    force_python=bool(force_python),
                    skip_build=True,
                )
                ev=np.asarray(a["eigenvalues"],dtype=complex)
                row={
                    "N":N,
                    "mode_m":m,
                    "L_polygon":L,
                    "D_source":float(model.D),
                    "kD":float(2.0*math.pi*m*model.D/L),
                    "omega_positive_hat":float(a["omega_positive_hat"]),
                    "omega_negative_abs_hat":float(a["omega_negative_abs_hat"]),
                    "lambda_positive_hat":a["lambda_positive_hat"],
                    "lambda_negative_hat":a["lambda_negative_hat"],
                    "positive_quality_re_over_im":float(a["positive_quality_re_over_im"]),
                    "negative_quality_re_over_im":float(a["negative_quality_re_over_im"]),
                    "relative_equilibrium_residual":float(a["rigid"]["relative_equilibrium_residual"]),
                    "backend":str(a["backend"]),
                    "eigenvalues":_complex_rows(ev),
                }
                levels.append(row); per_mode[m].append((row,ev))
            except Exception as exc:
                failures.append({"N":N,"mode_m":m,"error":repr(exc)})

    dump_json(out/"DYNAMIC_EIGENMODE_LEVELS.json",{"levels":levels,"failures":failures})

    mode_reports=[]
    finest_samples=[]
    all_converged=True
    full_spectrum_persistent=True
    for m in range(1,mmax+1):
        rows=per_mode[m]
        if len(rows)!=len(n_ladder):
            mode_reports.append({"mode_m":m,"status":"FAIL_INCOMPLETE_RESOLUTION_LADDER"})
            all_converged=False; full_spectrum_persistent=False
            continue
        tracking=spectral.track_spectrum(
            [{"label":r["N"],"eigenvalues":ev} for r,ev in rows],
            rel_tol=reltol,
        )
        omega=[r["omega_positive_hat"] for r,_ in rows]
        omega_shifts=[relative_shift(omega[i],omega[i+1]) for i in range(len(omega)-1)]
        selected_ok=all(s<=reltol for s in omega_shifts)
        full_ok=bool(tracking.get("ok",False))
        all_converged &= selected_ok
        full_spectrum_persistent &= full_ok
        fine=rows[-1][0]
        finest_samples.append({
            "mode_m":m,
            "N":fine["N"],
            "kD":fine["kD"],
            "omega_hat":fine["omega_positive_hat"],
            "growth_hat":float(complex(fine["lambda_positive_hat"]).real),
            "quality_re_over_im":fine["positive_quality_re_over_im"],
            "relative_equilibrium_residual":fine["relative_equilibrium_residual"],
            "backend":fine["backend"],
        })
        mode_reports.append({
            "mode_m":m,
            "N_ladder":n_ladder,
            "selected_omega_hat":[float(x) for x in omega],
            "selected_frequency_relative_shifts":[float(x) for x in omega_shifts],
            "selected_frequency_converged":bool(selected_ok),
            "full_spectrum_tracking":tracking,
        })

    finest_samples.sort(key=lambda r:r["kD"])
    kD=[r["kD"] for r in finest_samples]
    oh=[r["omega_hat"] for r in finest_samples]
    dim_slopes=centered_slopes(kD,oh)
    min_samples=int(cfg["policy"]["minimum_mode_samples"])
    enough=len(finest_samples)>=min_samples
    branch_ok=bool(enough and all_converged and full_spectrum_persistent and not failures)
    branch={
        "schema":"E012-DIMENSIONLESS-DYNAMIC-EIGENBRANCH-1.0",
        "classification":"FROZEN_LOCAL_KELVIN_EIGENBRANCH",
        "topology_id":"3_1",
        "provider_group":sel["anchor"].get("provider_group"),
        "static_seed_id":sel["anchor"].get("static_seed_id"),
        "source_geometry_sha256":sel["anchor"].get("source_locator",{}).get("geometry_sha256"),
        "source_raw_sha256":sel["anchor"].get("source_locator",{}).get("raw_sha256"),
        "c006_version":"0.3.0",
        "preset":preset,
        "samples":finest_samples,
        "dimensionless_group_slopes":dim_slopes,
        "mode_reports":mode_reports,
        "dimensionless_dynamic_branch_ok":branch_ok,
        "physical_scale_status":"UNRESOLVED_UNLESS_APPROVED_SCALE_CONTRACT",
        "true_floquet_status":"NOT_REQUIRED_IN_V0.1__NO_TRUE_FLOQUET_CLAIM",
        "scientific_boundary":"Frozen-local C006 Kelvin-generator branch only; no photon identity and no SI dispersion without independent scale contract.",
    }
    dump_json(out/"DYNAMIC_EIGENBRANCH.json",branch)

    gates=[
        {"id":"G01_E011_STATIC_READY_PROVENANCE","status":"PASS" if selected["static_ready"] else "FAIL",
         "static_status":selected["static_status"],"provider":sel["anchor"].get("provider_group")},
        {"id":"G02_C006_DYNAMIC_GENERATOR_AVAILABLE","status":"PASS" if levels and not failures else ("PARTIAL" if levels else "FAIL"),
         "c006_version":"0.3.0","level_count":len(levels),"expected_level_count":len(n_ladder)*mmax,"failures":len(failures)},
        {"id":"G03_MINIMUM_K_OMEGA_MODE_SAMPLES","status":"PASS" if enough else "FAIL",
         "count":len(finest_samples),"minimum":min_samples},
        {"id":"G04_SELECTED_FREQUENCY_RESOLUTION_CONVERGENCE","status":"PASS" if all_converged else "FAIL",
         "relative_tolerance":reltol},
        {"id":"G05_FULL_SPECTRUM_ROOT_PERSISTENCE","status":"PASS" if full_spectrum_persistent else "FAIL",
         "relative_tolerance":reltol},
        {"id":"G06_BACKGROUND_RELATIVE_EQUILIBRIUM","status":"DIAGNOSTIC",
         "policy":"NO_NEW_E012_THRESHOLD; preserve C006 frozen-local classification",
         "finest_residuals":[r["relative_equilibrium_residual"] for r in finest_samples]},
        {"id":"G07_TRUE_FLOQUET","status":"NOT_REQUIRED",
         "policy":"No RPO -> no true Floquet claim; v0.1 exports frozen-local spectrum only."},
    ]

    scale_path=Path(physical_scale_path) if physical_scale_path else root/"configs/physical_scale.json"
    scale=load_scale_contract(scale_path)
    scale_candidate,scale_reasons=make_physical_candidate(branch,scale)
    scale_ok=scale_candidate is not None
    candidate=scale_candidate if (scale_ok and branch_ok) else None
    handoff_blockers=[]
    if not branch_ok:
        handoff_blockers.append("DIMENSIONLESS_DYNAMIC_BRANCH_NOT_CONVERGED")
    handoff_blockers.extend(scale_reasons)
    if candidate is not None:
        dump_json(out/"a052_dynamic_candidate.json",candidate)
        handoff_status="A052_PHYSICAL_HANDOFF_READY"
    else:
        handoff_status="A052_PHYSICAL_HANDOFF_BLOCKED"
    gates.append({"id":"G08_PHYSICAL_SCALE_AND_ENERGY_MAPPING","status":"PASS" if scale_ok else "BLOCKED",
                  "reasons":scale_reasons,
                  "contract_path":str(scale_path) if scale_path.exists() else None})
    gates.append({"id":"G09_A052_HANDOFF","status":"PASS" if candidate is not None else "BLOCKED",
                  "candidate_emitted":bool(candidate is not None),
                  "reasons":handoff_blockers})

    if branch_ok and candidate is None:
        verdict="DIMENSIONLESS_DYNAMIC_BRANCH_OK__A052_PHYSICAL_HANDOFF_BLOCKED"
    elif branch_ok and candidate is not None:
        verdict="A052_PHYSICAL_DYNAMIC_CANDIDATE_EMITTED"
    else:
        verdict="DYNAMIC_EIGENBRANCH_NOT_CONVERGED"

    dump_json(out/"GATES.json",{"verdict":verdict,"gates":gates})
    dump_json(out/"A052_HANDOFF_STATUS.json",{
        "verdict":handoff_status,
        "candidate_emitted":bool(candidate is not None),
        "dimensionless_dynamic_branch_ok":branch_ok,
        "blocking_reasons":handoff_blockers,
        "next_action":("Copy outputs/a052_dynamic_candidate.json into A052 private/dynamic_candidate.json and rerun A052."
                       if candidate is not None else
                       "Resolve the listed branch/scale blockers, then rerun E012 before A052."),
    })

    report=[
        "# E012 v0.1.0 run report","",
        f"Verdict: **{verdict}**","",
        f"E011 seed: `{sel['anchor'].get('static_seed_id')}` ({sel['anchor'].get('provider_group')})",
        f"C006: `v0.3.0`",
        f"Preset: `{preset}`",
        f"Resolved mode samples: `{len(finest_samples)}`",
        f"Dimensionless branch converged: `{branch_ok}`",
        "",
        "The branch is a frozen-local C006 Kelvin-generator result.  It is not a true Floquet branch and is not identified as a photon.",
        "",
        f"A052 SI handoff: **{handoff_status}**",
    ]
    if scale_reasons:
        report += ["","Physical handoff blockers:"] + [f"- {r}" for r in scale_reasons]
    (out/"report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    return {"verdict":verdict,"branch_ok":branch_ok,"handoff":handoff_status,"outputs":str(out)}
