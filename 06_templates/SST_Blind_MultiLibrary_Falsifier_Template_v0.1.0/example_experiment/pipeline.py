from pathlib import Path
from sst_falsifier_core.gates import GateLedger,GateRecord
from sst_falsifier_core.protocol import load_config,freeze_protocol
from sst_falsifier_core.source_registry import resolve_sources
from sst_falsifier_core.util import write_json, environment_record

def run(config_path,outdir):
 cfg=load_config(config_path); out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
 freeze_protocol(cfg,out/"FROZEN_PROTOCOL.json"); led=GateLedger(); src=resolve_sources(cfg.get("source_overrides"))
 led.add(GateRecord("G0","PASS","Template infrastructure self-check",{"sources":src},"Example only; not a scientific result."))
 led.write(out/"gate_ledger.json"); write_json(out/"environment.json",environment_record()); return led.to_dict()
