from __future__ import annotations
from pathlib import Path
import json, shutil, sys
from .config import load_instance_config
from .protocol import freeze_protocol,assert_frozen
from .science_contract import assert_science_contract
from .report import assert_report,write_auto_science_tex,write_auto_results_tex,publish_instance_report
from .gates import GateLedger,load_gate_plan
from .source_registry import resolve_source_contract
from .environment import write_environment
from .util import write_json,canonical_json_sha256
from .outputs import pack_blind,pack_revealed,make_output_manifest,verify_output_manifest
from .blind import blind_terms_commitment,reveal_commitment,verify_reveal,verify_blind_terms


def _project(cfg): return cfg["project"]

def instance_output_root(root: Path,cfg: dict):
    p=_project(cfg); return root/f"{p['name']}_{p['version']}-outputs"


def _render_report_pdf(root: Path, cfg: dict, tex_path: Path, out: Path):
    rcfg=cfg.get("report",{})
    if not bool(rcfg.get("compile_pdf",True)):
        return {"success":False,"status":"SKIP","reason":"report.compile_pdf=false"}
    result=publish_instance_report(root,tex_path,strict=bool(rcfg.get("pdf_required",False)))
    write_json(out/"REPORT_RENDER.json",result)
    if result.get("success"):
        print(f"FALSIFIER report PDF: {result['destination']}")
    else:
        print(f"FALSIFIER report PDF: {result.get('status','SKIP')} - {result.get('error',result.get('reason','unknown'))}")
    return result


def _write_blind_run_artifacts(root: Path, cfg: dict, out: Path, frozen_payload: dict, mode: str):
    write_auto_science_tex(root,out/"report"/"AUTO_SCIENCE_CONTRACT.tex")
    write_environment(out/"ENVIRONMENT_PUBLIC.json")
    resolve_source_contract(root/"source_contract.json",out_path=out/"SOURCE_MANIFEST.json")
    defs=load_gate_plan(root/"gate_plan.json")
    from dataclasses import replace
    cpp_enabled=bool(cfg.get("backends",{}).get("cpp",{}).get("enabled",False))
    sycl_enabled=bool(cfg.get("backends",{}).get("sycl",{}).get("enabled",False))
    multi_enabled=bool(cfg.get("sources",{}).get("multilibrary_required",False))
    confirm_enabled=bool(cfg.get("sources",{}).get("independent_confirmation_required",False))
    remap={"G4":confirm_enabled,"G5":cpp_enabled,"G6":sycl_enabled,"G7":multi_enabled}
    defs=[replace(d,enabled=(d.enabled and remap.get(d.gate_id,True))) for d in defs]
    ledger=GateLedger(defs)
    if str(root) not in sys.path: sys.path.insert(0,str(root))
    from experiment.pipeline import run_scientific_pipeline
    backend_manifest=run_scientific_pipeline(root,cfg,ledger,mode)
    if "G9" in ledger.defs and ledger.status("G9") is None:
        ledger.record("G9","DEFERRED",reason="Reveal is a separate, commitment-verified phase and is not executed during blind runs.")
    ledger.write(out/"GATE_LEDGER.json"); write_json(out/"BACKEND_MANIFEST.json",backend_manifest or {})
    summary={"schema":"SST-RUN-SUMMARY-2","mode":mode,"protocol_bundle_sha256":frozen_payload.get("bundle_sha256"),"gate_ledger_sha256":ledger.to_dict().get("ledger_sha256"),"revealed":False}
    write_json(out/"RUN_SUMMARY.json",summary)
    make_output_manifest(out,out/"OUTPUT_MANIFEST.json")
    write_auto_results_tex(root,out,out/"report"/"AUTO_RESULTS.tex")
    (out/"report").mkdir(parents=True,exist_ok=True); shutil.copy2(root/"report"/"FALSIFIER_REPORT.tex",out/"report"/"FALSIFIER_REPORT.tex")
    _render_report_pdf(root,cfg,out/"report"/"FALSIFIER_REPORT.tex",out)
    make_output_manifest(out,out/"OUTPUT_MANIFEST.json")
    return ledger


def _verified_blind_state(out: Path):
    """Read blind state and verify ledger/summary/manifest integrity before reveal."""
    summary_path=out/"RUN_SUMMARY.json"; ledger_path=out/"GATE_LEDGER.json"
    if not ledger_path.is_file() or not summary_path.is_file():
        return None,None,{"ok":False,"reason":"REVEAL requires a completed prior blind FULL/CERTIFY run in the canonical output directory"}
    try:
        prior_summary=json.loads(summary_path.read_text(encoding="utf-8"))
        blind_payload=json.loads(ledger_path.read_text(encoding="utf-8"))
        blind_ledger=GateLedger.from_dict(blind_payload)
    except Exception as exc:
        return None,None,{"ok":False,"reason":f"blind state is unreadable: {type(exc).__name__}: {exc}"}

    stored=blind_payload.get("ledger_sha256")
    computed=canonical_json_sha256({k:v for k,v in blind_payload.items() if k!="ledger_sha256"})
    if not stored or stored!=computed:
        return None,None,{"ok":False,"reason":"GATE_LEDGER.json self-hash mismatch","stored_ledger_sha256":stored,"computed_ledger_sha256":computed}
    if prior_summary.get("gate_ledger_sha256")!=computed:
        return None,None,{"ok":False,"reason":"RUN_SUMMARY.json gate_ledger_sha256 does not match GATE_LEDGER.json","summary_gate_ledger_sha256":prior_summary.get("gate_ledger_sha256"),"computed_ledger_sha256":computed}

    manifest_ok,manifest_detail=verify_output_manifest(out,out/"OUTPUT_MANIFEST.json")
    if not manifest_ok:
        return None,None,{"ok":False,"reason":"blind OUTPUT_MANIFEST integrity verification failed","output_manifest":manifest_detail}
    return prior_summary,blind_ledger,{"ok":True,"ledger_sha256":computed,"output_manifest":manifest_detail}


def reveal_eligibility(root: Path, cfg: dict, out: Path, frozen_payload: dict):
    """Return a non-mutating, machine-readable decision for the frozen reveal policy."""
    decision={"schema":"SST-REVEAL-DECISION-2","eligible":False,"performed":False,"reason":""}
    if (out/"RUN_SUMMARY_REVEALED.json").exists() or (out/"revealed").exists():
        decision["reason"]="REVEAL already performed for the current output root; start a new blind run before revealing again"
        return decision

    prior_summary,blind_ledger,integrity=_verified_blind_state(out)
    decision["integrity"]=integrity
    if not integrity.get("ok"):
        decision["reason"]=integrity.get("reason","blind integrity verification failed")
        return decision

    policy=json.loads((root/"blind_policy.json").read_text(encoding="utf-8"))
    decision.update({
        "prior_mode":prior_summary.get("mode"),
        "protocol_bundle_sha256":prior_summary.get("protocol_bundle_sha256"),
        "blind_gate_ledger_sha256":integrity.get("ledger_sha256"),
        "required_gate":policy.get("reveal_requires_gate","G3"),
        "required_gate_statuses":list(policy.get("reveal_requires_gate_status",["PASS","FAIL"])),
        "gate_statuses":{gid:blind_ledger.status(gid) for gid in blind_ledger.defs},
    })
    allowed_modes=set(policy.get("reveal_allowed_after_modes",["FULL","CERTIFY"]))
    if prior_summary.get("mode") not in allowed_modes:
        decision["reason"]=f"REVEAL forbidden after mode={prior_summary.get('mode')}; allowed prior modes={sorted(allowed_modes)}"
        return decision
    if prior_summary.get("protocol_bundle_sha256")!=frozen_payload.get("bundle_sha256"):
        decision["reason"]="REVEAL forbidden: prior blind run used a different frozen protocol hash"
        return decision
    req_gate=decision["required_gate"]; allowed_status=set(decision["required_gate_statuses"]); actual=blind_ledger.status(req_gate)
    if actual not in allowed_status:
        decision["reason"]=f"REVEAL forbidden: {req_gate} status={actual}; requires one of {sorted(allowed_status)}"
        return decision
    if policy.get("block_reveal_on_unresolved",True):
        unresolved=[r.gate_id for r in blind_ledger.records if r.gate_id!="G9" and r.status=="UNRESOLVED"]
        if unresolved:
            decision["unresolved_gates"]=unresolved
            decision["reason"]=f"REVEAL forbidden while blind gates remain UNRESOLVED: {unresolved}"
            return decision
    decision["eligible"]=True
    decision["reason"]="Frozen reveal preconditions and blind-output integrity checks are satisfied; commitment verification may proceed."
    return decision


def _published_report_path(root: Path) -> Path:
    return root.parent/f"{root.name}_FALSIFIER_REPORT.pdf"


def _purge_stale_reveal_artifacts(root: Path, cfg: dict, out: Path):
    """A new blind run invalidates reveal/post-reveal artifacts from an older run."""
    for name in ("GATE_LEDGER_REVEALED.json","RUN_SUMMARY_REVEALED.json","REVEAL_VERIFICATION.json","REVEAL_DECISION.json"):
        p=out/name
        if p.exists(): p.unlink()
    post=out/"report"/"POST_RUN_DISCUSSION.tex"
    if post.exists(): post.unlink()
    revdir=out/"revealed"
    if revdir.exists(): shutil.rmtree(revdir)
    p=_project(cfg); z=root.parent/f"{p['name']}_{p['version']}-outputs_REVEALED.zip"
    if z.exists(): z.unlink()
    # Prevent a previous revealed PDF from surviving if a new blind render is skipped/fails.
    published=_published_report_path(root)
    if published.exists(): published.unlink()


def _perform_reveal(root: Path, cfg: dict, out: Path, frozen_payload: dict, decision: dict):
    prior_summary=json.loads((out/"RUN_SUMMARY.json").read_text(encoding="utf-8"))
    policy=json.loads((root/"blind_policy.json").read_text(encoding="utf-8"))
    blind_payload=json.loads((out/"GATE_LEDGER.json").read_text(encoding="utf-8")); blind_ledger=GateLedger.from_dict(blind_payload)
    nonce=root/policy["private_nonce_path"]; reveal=root/policy["private_reveal_path"]
    ok_reveal,detail_reveal=verify_reveal(reveal,nonce,root/policy["reveal_commitment_path"])
    ok_terms,detail_terms=verify_blind_terms(root/policy["private_forbidden_terms_path"],nonce,root/policy["commitment_path"])
    if not (ok_reveal and ok_terms): raise RuntimeError(f"reveal verification failed: reveal={detail_reveal}, blind_terms={detail_terms}")

    revealed=GateLedger(list(blind_ledger.defs.values()))
    for rec in blind_ledger.records:
        if rec.gate_id=="G9": continue
        revealed.records.append(rec)
    if "G9" in revealed.defs:
        d=revealed.defs["G9"]
        revealed.records.append(__import__("sst_falsifier.gates",fromlist=["GateRecord"]).GateRecord("G9","PASS",d.question,{"reveal_commitment_verified":True,"blind_terms_commitment_verified":True},"Reveal prerequisites, blind-output integrity, and both nonced commitments verified."))
    revealed.write(out/"GATE_LEDGER_REVEALED.json")

    revdir=out/"revealed"; revdir.mkdir(parents=True,exist_ok=True)
    shutil.copy2(reveal,revdir/"reveal.json"); shutil.copy2(nonce,revdir/"REVEAL_NONCE.bin")
    shutil.copy2(root/"private"/"OPAQUE_ID_KEY.bin",revdir/"OPAQUE_ID_KEY.bin")
    shutil.copy2(root/policy["private_forbidden_terms_path"],revdir/"blind_forbidden_terms.txt")
    write_json(out/"REVEAL_VERIFICATION.json",{"schema":"SST-REVEAL-VERIFICATION-2","reveal_ok":ok_reveal,"blind_terms_ok":ok_terms,"reveal":detail_reveal,"blind_terms":detail_terms,"blind_integrity":decision.get("integrity",{})})
    post=root/"report"/"POST_RUN_DISCUSSION.tex"
    if post.exists(): shutil.copy2(post,out/"report"/"POST_RUN_DISCUSSION.tex")
    summary={**prior_summary,"reveal_mode":"REVEAL","revealed":True,"revealed_gate_ledger_sha256":revealed.to_dict().get("ledger_sha256")}
    write_json(out/"RUN_SUMMARY_REVEALED.json",summary)
    write_auto_results_tex(root,out,out/"report"/"AUTO_RESULTS.tex")
    _render_report_pdf(root,cfg,out/"report"/"FALSIFIER_REPORT.tex",out)


def _finalize_reveal(root: Path, cfg: dict, out: Path, decision: dict):
    decision={**decision,"eligible":True,"performed":True,"reason":"Canonical framework REVEAL completed successfully."}
    write_json(out/"REVEAL_DECISION.json",decision)
    make_output_manifest(out,out/"OUTPUT_MANIFEST.json")
    p=_project(cfg); z=root.parent/f"{p['name']}_{p['version']}-outputs_REVEALED.zip"
    pack_revealed(out,z)
    print(f"REVEALED package: {z}")
    return 0


def _run_reveal(root: Path, cfg: dict, out: Path, frozen_payload: dict):
    decision=reveal_eligibility(root,cfg,out,frozen_payload)
    if not decision.get("eligible"):
        raise RuntimeError(decision.get("reason","REVEAL forbidden by frozen policy"))
    _perform_reveal(root,cfg,out,frozen_payload,decision)
    return _finalize_reveal(root,cfg,out,decision)


def run_mode(instance_root: str|Path, mode: str):
    root=Path(instance_root).resolve(); cfg=load_instance_config(root); mode=mode.upper(); out=instance_output_root(root,cfg); out.mkdir(exist_ok=True)
    frozen=root/"preregistration"/"FROZEN_PROTOCOL.json"
    if mode=="FREEZE":
        write_auto_science_tex(root,root/"report"/"AUTO_SCIENCE_CONTRACT.tex")
        policy=json.loads((root/"blind_policy.json").read_text(encoding="utf-8"))
        terms=root/policy["private_forbidden_terms_path"]; nonce=root/policy["private_nonce_path"]; terms_commit=root/policy["commitment_path"]
        reveal=root/policy["private_reveal_path"]; reveal_commit=root/policy["reveal_commitment_path"]
        if not frozen.exists():
            blind_terms_commitment(terms,nonce,terms_commit)
            reveal_commitment(reveal,nonce,reveal_commit)
        payload=freeze_protocol(root,frozen,require_complete=True); print(json.dumps(payload,indent=2)); return 0
    if mode=="SELFTEST":
        import pytest
        fr=Path(__file__).resolve().parents[1]; return int(pytest.main([str(fr/"tests"),"-q"]))
    assert_science_contract(root/"science_contract.json"); assert_report(root/"report"/"FALSIFIER_REPORT.tex",require_complete=True); frozen_payload=assert_frozen(root,frozen)
    if mode=="REVEAL": return _run_reveal(root,cfg,out,frozen_payload)
    if mode=="REVEAL_IF_ALLOWED":
        decision=reveal_eligibility(root,cfg,out,frozen_payload)
        if not decision.get("eligible"):
            write_json(out/"REVEAL_DECISION.json",decision)
            make_output_manifest(out,out/"OUTPUT_MANIFEST.json")
            print("REVEAL withheld (fail-closed): "+decision.get("reason","unknown reason"))
            return 0
        _perform_reveal(root,cfg,out,frozen_payload,decision)
        return _finalize_reveal(root,cfg,out,decision)
    _purge_stale_reveal_artifacts(root,cfg,out)
    _write_blind_run_artifacts(root,cfg,out,frozen_payload,mode)
    p=_project(cfg); z=root.parent/f"{p['name']}_{p['version']}-outputs_BLIND.zip"; pack_blind(root,out,z); print(f"BLIND package: {z}")
    return 0
