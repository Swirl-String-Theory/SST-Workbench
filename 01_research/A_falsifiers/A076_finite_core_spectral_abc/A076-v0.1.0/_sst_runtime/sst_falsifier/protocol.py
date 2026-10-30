from __future__ import annotations
from pathlib import Path
import time
from typing import Iterable
from .util import sha256_file, sha256_bytes, canonical_json_sha256, write_json, read_json
from .science_contract import assert_science_contract
from .report import assert_report
from .source_registry import assert_source_contract
from .gates import assert_gate_plan

SCHEMA="SST-FALSIFIER-PROTOCOL-2"
DEFAULT_PROTOCOL_FILES=(
    "falsifier.toml", "science_contract.json", "source_contract.json", "gate_plan.json", "blind_policy.json",
    "preregistration/BLIND_TERMS_COMMITMENT.json", "preregistration/REVEAL_COMMITMENT.json",
    "report/FALSIFIER_REPORT.tex"
)

class ProtocolError(RuntimeError): pass
class ProtocolAlreadyFrozenError(ProtocolError): pass
class ProtocolMismatchError(ProtocolError): pass


def portable_protocol_fingerprint(instance_root: str | Path, files: Iterable[str]=DEFAULT_PROTOCOL_FILES) -> dict:
    """Additional cross-platform *diagnostic* digest: normalize UTF-8 CRLF/LF only.

    Never substitute this for the byte-exact frozen bundle SHA or commitment.
    """
    root = Path(instance_root)
    rows = []
    for rel in files:
        name = Path(rel).as_posix()
        data = (root / rel).read_bytes()
        # The preregistration file set is textual. An undecodable input fails closed.
        text = data.decode("utf-8-sig")
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        rows.append({"path": name, "normalized_sha256": sha256_bytes(normalized),
                     "normalized_size": len(normalized)})
    return {"portable_schema": "SST-PROTOCOL-PORTABLE-DIAGNOSTIC-1",
            "portable_files": rows,
            "portable_bundle_sha256": canonical_json_sha256({"files": rows})}


def build_protocol_bundle(instance_root: str | Path, files: Iterable[str]=DEFAULT_PROTOCOL_FILES) -> dict:
    root=Path(instance_root)
    files=tuple(files)
    entries=[]
    for rel in files:
        p=root/rel
        if not p.exists(): raise ProtocolError(f"required protocol file missing: {rel}")
        entries.append({"path":Path(rel).as_posix(),"size":p.stat().st_size,"sha256":sha256_file(p)})
    bundle_core={"files":entries}
    payload = {"schema": SCHEMA, "files": entries,
               "bundle_sha256": canonical_json_sha256(bundle_core)}
    payload.update(portable_protocol_fingerprint(root, files))
    return payload


def freeze_protocol(instance_root: str | Path, frozen_path: str | Path, *, require_complete: bool=True) -> dict:
    root=Path(instance_root); frozen=Path(frozen_path)
    # Create-once semantics take precedence over all later validation. Once frozen,
    # any byte change in the protocol bundle is a versioning error, not an invitation
    # to overwrite the preregistration.
    if frozen.exists():
        candidate=build_protocol_bundle(root)
        existing=read_json(frozen)
        if existing.get("bundle_sha256")==candidate.get("bundle_sha256"):
            return existing
        raise ProtocolAlreadyFrozenError(
            "protocol is already frozen and current inputs differ; create a new falsifier version/campaign instead of overwriting preregistration"
        )
    if require_complete:
        science=assert_science_contract(root/"science_contract.json")
        assert_source_contract(root/"source_contract.json")
        assert_gate_plan(root/"gate_plan.json")
        assert_report(root/"report"/"FALSIFIER_REPORT.tex", require_complete=True)
        policy=read_json(root/"blind_policy.json")
        required_policy=("private_forbidden_terms_path","private_nonce_path","commitment_path","private_reveal_path","reveal_commitment_path")
        missing=[k for k in required_policy if not policy.get(k)]
        if missing: raise ProtocolError(f"blind policy missing fields: {missing}")
        for rel in (policy["private_forbidden_terms_path"],policy["private_nonce_path"],policy["commitment_path"],policy["private_reveal_path"],policy["reveal_commitment_path"]):
            if not (root/rel).exists(): raise ProtocolError(f"blind policy path missing at freeze: {rel}")
        gate_ids={g["gate_id"] for g in read_json(root/"gate_plan.json")["gates"]}
        bad=[st.get("gate") for st in science.get("steps",[]) if st.get("gate") not in gate_ids]
        if bad: raise ProtocolError(f"science steps reference gates absent from gate_plan.json: {bad}")
    candidate=build_protocol_bundle(root)
    candidate["frozen_unix_time"] = int(time.time())
    write_json(frozen,candidate)
    return candidate


def verify_frozen(instance_root: str | Path, frozen_path: str | Path) -> tuple[bool, dict]:
    frozen=Path(frozen_path)
    if not frozen.exists(): return False,{"error":"missing frozen protocol"}
    expected=read_json(frozen)
    actual=build_protocol_bundle(instance_root)
    ok=expected.get("bundle_sha256")==actual.get("bundle_sha256")
    if "portable_bundle_sha256" in expected:
        ok = ok and expected["portable_bundle_sha256"] == actual["portable_bundle_sha256"]
    return ok,{"expected":expected.get("bundle_sha256"),"actual":actual.get("bundle_sha256"),"files_expected":expected.get("files"),"files_actual":actual.get("files"),"portable_expected":expected.get("portable_bundle_sha256"),"portable_actual":actual.get("portable_bundle_sha256")}


def assert_frozen(instance_root: str | Path, frozen_path: str | Path) -> dict:
    ok, detail=verify_frozen(instance_root,frozen_path)
    if not ok: raise ProtocolMismatchError(f"frozen protocol verification failed: {detail}")
    return read_json(frozen_path)
