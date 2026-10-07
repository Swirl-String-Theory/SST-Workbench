from dataclasses import dataclass, asdict
from .util import write_json
TERMINAL={"PASS","FAIL","UNRESOLVED","NOT_RUN_PREREQUISITE"}
@dataclass
class GateRecord:
    gate_id:str; status:str; question:str; metrics:dict; reason:str=""
    def __post_init__(self):
        if self.status not in TERMINAL: raise ValueError(self.status)
class GateLedger:
    def __init__(self): self.records=[]
    def add(self,rec): self.records.append(rec); return rec
    def status(self,gid):
        for r in reversed(self.records):
            if r.gate_id==gid: return r.status
        return None
    def write(self,path): write_json(path,{"schema":"SST-GATE-LEDGER-1","records":[asdict(r) for r in self.records]})
