"""Write a fresh versioned routing diagnostic into one create-only run snapshot."""
from __future__ import annotations
import json
from pathlib import Path
from .numeric_readiness import evaluate
from .runner import run_d01,run_d02,run_d03
from .security import canon


def write(root,qualification):
    root=Path(root)
    # Need the exact reference gates evaluated with the same D01/D02/D03 code.
    gates=[g for r in (run_d01(root),run_d02(root),run_d03(root)) for g in r['gates']]
    record=evaluate(root,gates,qualification,g10_status=qualification['qualification']['refined_discretization'])
    dest=root/'outputs/ROUTING_V033_RESULT.json'
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as fp:fp.write(canon(record))
    return record
