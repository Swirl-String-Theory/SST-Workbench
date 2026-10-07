from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json

TERMINAL={"PASS","FAIL","UNRESOLVED","NOT_RUN_PREREQUISITE"}

@dataclass
class GateRecord:
    gate_id: str
    status: str
    question: str
    metrics: dict[str, Any]
    reason: str = ""
    depends_on: tuple[str,...] = ()
    def __post_init__(self):
        if self.status not in TERMINAL:
            raise ValueError(f"invalid gate status: {self.status}")

class GateLedger:
    def __init__(self, schema="SST-GATE-LEDGER-2"):
        self.schema=schema; self.records=[]
    def add(self, rec: GateRecord):
        known={r.gate_id:r.status for r in self.records}
        if rec.depends_on and rec.status not in {"NOT_RUN_PREREQUISITE","UNRESOLVED"}:
            missing=[g for g in rec.depends_on if known.get(g)!="PASS"]
            if missing:
                raise ValueError(f"{rec.gate_id} cannot be {rec.status}: prerequisites not PASS: {missing}")
        self.records.append(rec); return rec
    def status(self, gate_id):
        for r in reversed(self.records):
            if r.gate_id==gate_id: return r.status
        return None
    def require_pass(self,*gate_ids): return all(self.status(g)=="PASS" for g in gate_ids)
    def to_dict(self): return {"schema":self.schema,"records":[asdict(r) for r in self.records]}
    def write(self,path):
        p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(self.to_dict(),indent=2,sort_keys=True)+"\n",encoding="utf-8")
