from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
from .util import write_json

TERMINAL={"PASS","FAIL","UNRESOLVED","NOT_RUN_PREREQUISITE"}
@dataclass
class GateRecord:
    gate_id: str
    status: str
    question: str
    metrics: dict[str, Any]
    reason: str = ""
    def __post_init__(self):
        if self.status not in TERMINAL: raise ValueError(self.status)

class GateLedger:
    def __init__(self): self.records=[]
    def add(self, rec:GateRecord): self.records.append(rec); return rec
    def status(self, gate_id):
        for r in reversed(self.records):
            if r.gate_id==gate_id: return r.status
        return None
    def require_pass(self,*gate_ids): return all(self.status(g)=="PASS" for g in gate_ids)
    def to_dict(self): return {"schema":"SST-GATE-LEDGER-1","records":[asdict(r) for r in self.records]}
    def write(self,path): write_json(path,self.to_dict())
