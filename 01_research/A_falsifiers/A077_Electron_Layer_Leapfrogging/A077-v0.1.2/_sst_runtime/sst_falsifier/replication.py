from __future__ import annotations
from typing import Any, Iterable

EVIDENCE_CLASSES={"synthetic_control","simulation","independent_source","experimental"}
INDEPENDENT_CLASSES={"independent_source","experimental"}
CONTROL_CLASSES={"synthetic_control","simulation"}

class ReplicationEvidenceError(RuntimeError): pass


def _qualified(row: dict[str,Any]) -> bool:
    for key in ("qualified","pass","supported","accepted"):
        if key in row: return bool(row[key])
    status=str(row.get("status","")).upper()
    return status in {"PASS","SUPPORTED","JOINT_SUPPORTED","QUALIFIED"}


def assess_replication(rows: Iterable[dict[str,Any]], *, min_independent_groups: int = 2) -> dict[str,Any]:
    """Separate implementation-control replication from genuine cross-source evidence.

    Different source_group labels are *not* sufficient evidence of independence.
    Cross-source eligibility requires independent/experimental evidence classes and
    distinct independence/provenance families.  Synthetic/simulation rows can
    validate implementation control replication but can never close a scientific
    cross-source replication gate.
    """
    rows=[dict(r) for r in rows]
    invalid=[]
    for i,r in enumerate(rows):
        ec=r.get("evidence_class")
        if ec not in EVIDENCE_CLASSES:
            invalid.append(f"row[{i}] invalid/missing evidence_class={ec!r}")
    if invalid: raise ReplicationEvidenceError("; ".join(invalid))

    q=[r for r in rows if _qualified(r)]
    controls=[r for r in q if r["evidence_class"] in CONTROL_CLASSES]
    independent=[r for r in q if r["evidence_class"] in INDEPENDENT_CLASSES]

    control_groups={str(r.get("source_group") or r.get("independence_family") or "") for r in controls}
    control_groups.discard("")
    control_status="PASS" if len(control_groups)>=2 else ("UNRESOLVED" if controls else "NOT_RUN_PREREQUISITE")

    ind_groups={str(r.get("independence_family") or r.get("source_group") or "") for r in independent}
    ind_groups.discard("")
    prov_groups={str(r.get("provenance_family") or r.get("upstream_provenance_family") or "") for r in independent}
    prov_groups.discard("")
    generators={str(r.get("generator_id") or "") for r in independent}; generators.discard("")

    reasons=[]
    if len(independent)<min_independent_groups:
        reasons.append(f"need >= {min_independent_groups} qualified independent/experimental rows")
    if len(ind_groups)<min_independent_groups:
        reasons.append(f"need >= {min_independent_groups} distinct independence/source groups")
    # When provenance metadata exists, it must independently distinguish the rows.
    if independent and prov_groups and len(prov_groups)<min_independent_groups:
        reasons.append("independent labels share one provenance family")
    # A common explicit synthetic generator is incompatible with a claim of independent source evidence.
    if len(independent)>=min_independent_groups and generators and len(generators)==1:
        reasons.append("independent-labeled rows share one explicit generator_id")

    if not independent:
        cross_status="NOT_RUN_PREREQUISITE"
    elif reasons:
        cross_status="UNRESOLVED"
    else:
        cross_status="PASS"

    return {
        "schema":"SST-REPLICATION-ASSESSMENT-1",
        "qualified_rows":len(q),
        "control_rows":len(controls),
        "independent_rows":len(independent),
        "control_source_groups":sorted(control_groups),
        "independent_groups":sorted(ind_groups),
        "provenance_families":sorted(prov_groups),
        "generator_ids":sorted(generators),
        "G5_CONTROL_REPLICATION":control_status,
        "G5_CROSS_SOURCE_REPLICATION":cross_status,
        "joint_support_eligible":cross_status=="PASS",
        "reasons":reasons,
    }
