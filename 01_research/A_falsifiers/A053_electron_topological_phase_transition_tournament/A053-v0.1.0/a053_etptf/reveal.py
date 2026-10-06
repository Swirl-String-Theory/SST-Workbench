from __future__ import annotations
import json, hashlib
from pathlib import Path

def reveal(summary_path, config_path):
    s=json.loads(Path(summary_path).read_text(encoding='utf-8'))
    c=json.loads(Path(config_path).read_text(encoding='utf-8'))
    if s.get('blind') is not True: raise ValueError('summary is not blind')
    if c.get('enabled') is not True: raise ValueError('reveal config must set enabled=true')
    # Deliberately attaches constants only. No blind metric is recomputed.
    return {'schema':'A053-REVEAL-RESULT-v1','blind_summary_sha256':hashlib.sha256(Path(summary_path).read_bytes()).hexdigest(),'blind_verdict':s.get('verdict'),'blind_survivors':s.get('survivors',[]),'constants':c.get('constants',{}),'electron':c.get('electron',{}),'note':'Interpretive attachment only; no blind scientific metric recomputed.'}
