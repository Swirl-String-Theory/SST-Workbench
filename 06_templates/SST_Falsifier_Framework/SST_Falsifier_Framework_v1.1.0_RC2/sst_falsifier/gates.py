from __future__ import annotations
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
import json
from .util import write_json, canonical_json_sha256

TERMINAL={"PASS","FAIL","UNRESOLVED","NOT_RUN_PREREQUISITE","NOT_APPLICABLE","DEFERRED"}

class GateError(RuntimeError): pass
class GateDependencyError(GateError): pass
class GateAlreadyRecordedError(GateError): pass
class GateInputsUnavailable(GateError):
    """A scientific evaluator lacks physical inputs it cannot synthesize."""


@dataclass(frozen=True)
class GateDefinition:
    gate_id: str
    question: str
    requires: tuple[str,...]=()
    enabled: bool=True

@dataclass(frozen=True)
class GateRecord:
    gate_id: str
    status: str
    question: str
    metrics: dict[str,Any]=field(default_factory=dict)
    reason: str=""
    requested_backend: str|None=None
    actual_backend: str|None=None
    authority: str|None=None
    execution_status: str="NOT_RECORDED"
    def __post_init__(self):
        if self.status not in TERMINAL: raise ValueError(f"invalid gate status: {self.status}")
        if self.execution_status not in {"EXECUTED", "NOT_EXECUTED", "NOT_RECORDED", "DEFERRED", "DISABLED"}: raise ValueError("invalid execution_status")



def validate_gate_plan(path: str|Path) -> list[str]:
    d=json.loads(Path(path).read_text(encoding="utf-8")); errors=[]
    if d.get("schema")!="SST-GATE-PLAN-2": errors.append("gate plan schema must be SST-GATE-PLAN-2")
    gates=d.get("gates",[]); ids=[g.get("gate_id") for g in gates]
    if len(ids)!=len(set(ids)): errors.append("duplicate gate_id")
    known=set(ids)
    for i,g in enumerate(gates):
        if not g.get("gate_id") or not g.get("question"): errors.append(f"gates[{i}] requires gate_id and question")
        for req in g.get("requires",[]):
            if req not in known: errors.append(f"{g.get('gate_id')} requires unknown gate {req}")
            if req==g.get("gate_id"): errors.append(f"{g.get('gate_id')} depends on itself")
    graph={g.get("gate_id"):list(g.get("requires",[])) for g in gates}
    visiting=set();done=set()
    def visit(n):
        if n in done:return
        if n in visiting:
            errors.append(f"gate dependency cycle involving {n}");return
        visiting.add(n)
        for q in graph.get(n,[]):visit(q)
        visiting.remove(n);done.add(n)
    for n in graph:visit(n)
    return errors

def assert_gate_plan(path: str|Path) -> None:
    errors=validate_gate_plan(path)
    if errors: raise GateError("gate plan invalid:\n- "+"\n- ".join(errors))

def load_gate_plan(path: str|Path) -> list[GateDefinition]:
    d=json.loads(Path(path).read_text(encoding="utf-8"))
    return [GateDefinition(x["gate_id"],x["question"],tuple(x.get("requires",[])),bool(x.get("enabled",True))) for x in d["gates"]]

class GateLedger:
    def __init__(self, definitions: list[GateDefinition], *, strict_dependencies: bool = False):
        self.defs={d.gate_id:d for d in definitions}; self.records: list[GateRecord]=[]
        self.strict_dependencies=strict_dependencies
        for d in definitions:
            for req in d.requires:
                if req not in self.defs: raise GateError(f"gate {d.gate_id} requires unknown gate {req}")
    def status(self, gate_id: str) -> str|None:
        for r in self.records:
            if r.gate_id==gate_id: return r.status
        return None
    def _dependency_satisfied(self, gate_id: str, seen=None) -> bool:
        seen=set() if seen is None else set(seen)
        if gate_id in seen: return False
        seen.add(gate_id)
        st=self.status(gate_id); d=self.defs[gate_id]
        if st=="PASS": return True
        if st=="NOT_APPLICABLE" and not d.enabled:
            return all(self._dependency_satisfied(req,seen) for req in d.requires)
        return False
    def dependencies_pass(self, gate_id: str) -> bool:
        d=self.defs[gate_id]; return all(self._dependency_satisfied(g) for g in d.requires)
    def should_execute(self, gate_id: str) -> bool:
        """Diagnostic scheduling: upstream scientific FAIL is never a skip reason."""
        if gate_id not in self.defs: raise GateError(f"unknown gate: {gate_id}")
        return self.defs[gate_id].enabled and self.status(gate_id) is None and gate_id!="G9"

    def record(self, gate_id: str, status: str, *, metrics=None, reason="", requested_backend=None, actual_backend=None, authority=None, execution_status=None) -> GateRecord:
        if gate_id not in self.defs: raise GateError(f"unknown gate: {gate_id}")
        if self.status(gate_id) is not None: raise GateAlreadyRecordedError(f"gate already recorded: {gate_id}")
        d=self.defs[gate_id]
        if not d.enabled:
            if status!="NOT_APPLICABLE": raise GateError(f"disabled gate {gate_id} must be NOT_APPLICABLE")
        elif self.strict_dependencies and status not in {"NOT_RUN_PREREQUISITE","DEFERRED"} and not self.dependencies_pass(gate_id):
            missing=[g for g in d.requires if not self._dependency_satisfied(g)]
            raise GateDependencyError(f"gate {gate_id} cannot run before PASS prerequisites: {missing}")
        if execution_status is None:
            execution_status=("DISABLED" if not d.enabled else "DEFERRED" if status=="DEFERRED"
                              else "NOT_EXECUTED" if status in {"NOT_RUN_PREREQUISITE","NOT_APPLICABLE"}
                              else "EXECUTED")
        r=GateRecord(gate_id,status,d.question,metrics or {},reason,requested_backend,actual_backend,authority,execution_status)
        self.records.append(r); return r

    def qualification(self, gate_id: str) -> dict[str,Any]:
        """Recompute scientific authority independently from the measured status.

        A failing prerequisite never erases a measured PASS/FAIL; it removes
        downstream claim authority. Transitive prerequisites are checked too.
        """
        if gate_id not in self.defs: raise GateError(f"unknown gate: {gate_id}")
        def evaluate(gid: str, trail: frozenset[str]) -> dict[str,Any]:
            if gid in trail: raise GateDependencyError(f"cycle in gate graph: {gid}")
            d=self.defs[gid]; status=self.status(gid)
            deps={req:evaluate(req,trail|{gid}) for req in d.requires}
            blocked=[req for req,x in deps.items() if not x["allows_dependent_claim"]]
            if not d.enabled:
                quality="NOT_APPLICABLE" if status=="NOT_APPLICABLE" else "INVALID_DISABLED_GATE_RECORD"
                allows=(status=="NOT_APPLICABLE" and not blocked)
            elif status is None:
                quality="NOT_EVALUATED";allows=False
            elif status=="DEFERRED":
                quality="DEFERRED";allows=False
            elif status=="NOT_RUN_PREREQUISITE":
                quality="BLOCKED_PREREQUISITE";allows=False
            elif status=="UNRESOLVED":
                quality="UNRESOLVED" if not blocked else "DIAGNOSTIC_ONLY"
                allows=False
            elif blocked:
                quality="DIAGNOSTIC_ONLY";allows=False
            else:
                quality="QUALIFIED";allows=(status=="PASS")
            return {"qualification":quality,"blocked_by":blocked,
                    "prerequisite_statuses":{k:self.status(k) for k in d.requires},
                    "allows_dependent_claim":allows}
        return evaluate(gate_id,frozenset())

    def run_evaluators(self, evaluators: dict[str,Any]) -> None:
        """Run all implemented and enabled blind evaluators despite upstream FAIL.

        Evaluators are zero-argument callables returning a dict with status and
        optionally metrics/reason/backend metadata. Unimplemented = UNRESOLVED.
        Only GateInputsUnavailable allows NOT_RUN_PREREQUISITE. Unexpected exceptions
        remain real execution failures and are not disguised as scientific FAIL.
        """
        for gid,d in self.defs.items():
            if gid=="G9" or self.status(gid) is not None: continue
            if not d.enabled:
                self.record(gid,"NOT_APPLICABLE",reason="Disabled by framework profile")
                continue
            evaluator=evaluators.get(gid)
            if evaluator is None:
                self.record(gid,"UNRESOLVED",reason="No scientific evaluator implemented for this gate; not executed", execution_status="NOT_EXECUTED")
                continue
            try:
                result=evaluator()
            except GateInputsUnavailable as exc:
                self.record(gid,"NOT_RUN_PREREQUISITE",reason=f"Required scientific inputs unavailable: {exc}")
                continue
            if not isinstance(result,dict) or result.get("status") not in TERMINAL:
                raise GateError(f"evaluator {gid} must return a mapping with a valid status")
            if result["status"] in {"DEFERRED","NOT_APPLICABLE"}:
                raise GateError(f"enabled blind evaluator {gid} cannot return {result['status']}")
            self.record(gid,result["status"],metrics=result.get("metrics"),
                        reason=result.get("reason",""),execution_status="EXECUTED",requested_backend=result.get("requested_backend"),
                        actual_backend=result.get("actual_backend"),authority=result.get("authority"))

    def skip_due_prerequisite(self, gate_id: str, reason="required scientific inputs genuinely unavailable") -> GateRecord:
        """Legacy hook: never skip solely because a preceding gate returned FAIL."""
        return self.record(gate_id,"NOT_RUN_PREREQUISITE",reason=reason)
    @classmethod
    def from_dict(cls, payload: dict):
        defs=[GateDefinition(d["gate_id"],d["question"],tuple(d.get("requires",[])),bool(d.get("enabled",True))) for d in payload.get("definitions",[])]
        led=cls(defs,strict_dependencies=(payload.get("execution_policy")=="STRICT_DEPENDENCY"))
        for r in payload.get("records",[]):
            led.records.append(GateRecord(r["gate_id"],r["status"],r["question"],r.get("metrics",{}),r.get("reason",""),r.get("requested_backend"),r.get("actual_backend"),r.get("authority"),r.get("execution_status","NOT_RECORDED")))
        return led
    def to_dict(self):
        payload={"schema":"SST-GATE-LEDGER-2","execution_policy":("STRICT_DEPENDENCY" if self.strict_dependencies else "FULL_DIAGNOSTIC"),
                 "definitions":[asdict(d) for d in self.defs.values()],
                 "records":[{**asdict(r),**self.qualification(r.gate_id)} for r in self.records]}
        payload["ledger_sha256"]=canonical_json_sha256({k:v for k,v in payload.items() if k!="ledger_sha256"})
        return payload
    def write(self,path): write_json(path,self.to_dict())
