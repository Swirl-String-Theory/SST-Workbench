from __future__ import annotations
from pathlib import Path
from typing import Any
from a055_science.pipeline_core import run

def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    return run(root,cfg,ledger,mode)
