"""Evidence-aware replication accounting.

This module is the A056 consumer backport of the proposed Framework v1.0.3
Gate-5 fix.  It prevents multiple synthetic cases from one generator, or many
runs of one simulation solver, from masquerading as independent physical
source replication.
"""
from __future__ import annotations
from collections import defaultdict

PHYSICAL_CROSS_SOURCE_CLASSES={"independent_source","experimental"}
CONTROL_CLASS="synthetic_control"
SIMULATION_CLASS="simulation"


def replication_group(record):
    ec=record.get("evidence_class")
    if ec==CONTROL_CLASS:
        # Distinct synthetic seeds/cases from the same generator are one
        # implementation-control provenance family.
        return record.get("generator_id") or record.get("solver_id") or "SYNTHETIC_GENERATOR_UNSPECIFIED"
    if ec==SIMULATION_CLASS:
        # Multiple parameter points/seeds from one solver are not independent.
        return record.get("simulation_independence_group") or record.get("solver_id") or "SIMULATION_SOLVER_UNSPECIFIED"
    return record.get("replication_group") or record.get("source_group") or "UNSPECIFIED"


def _groups(records):
    return sorted({replication_group(r) for r in records if replication_group(r)!="UNSPECIFIED"})


def assess_replication(records, min_independent_groups=2):
    buckets=defaultdict(list)
    for r in records:
        buckets[r.get("evidence_class","UNSPECIFIED")].append(r)
    control_groups=_groups(buckets[CONTROL_CLASS])
    simulation_groups=_groups(buckets[SIMULATION_CLASS])
    physical=[]
    for ec in PHYSICAL_CROSS_SOURCE_CLASSES:
        physical.extend(buckets[ec])
    physical_groups=_groups(physical)
    return {
      "schema":"SST-REPLICATION-ASSESSMENT-1",
      "min_independent_groups":int(min_independent_groups),
      "control_groups":control_groups,
      "simulation_groups":simulation_groups,
      "physical_groups":physical_groups,
      "control_recovered":len(control_groups)>=1,
      "cross_source_pass":len(physical_groups)>=int(min_independent_groups),
      "physical_evidence_present":bool(physical_groups),
      "counts_by_evidence_class":{k:len(v) for k,v in sorted(buckets.items())},
    }


def gate5_statuses(assessment):
    """Return fail-closed framework statuses for the split Gate-5 semantics."""
    control_status = "PASS" if assessment.get("control_recovered") else "NOT_RUN_PREREQUISITE"
    if assessment.get("cross_source_pass"):
        cross_status = "PASS"
    elif assessment.get("physical_evidence_present"):
        cross_status = "UNRESOLVED"
    else:
        cross_status = "NOT_RUN_PREREQUISITE"
    return {"G5_CONTROL_REPLICATION":control_status,"G5_CROSS_SOURCE_REPLICATION":cross_status}
