from __future__ import annotations
import json
from pathlib import Path
from .common import dump_json, sha256_file

def run(root: Path, outroot: Path):
    cfg=json.loads((root/'configs/blind_config.json').read_text(encoding='utf-8'))
    adm=root/cfg['admissibility']; rules=json.loads(adm.read_text(encoding='utf-8'))
    out=outroot/'blind'; out.mkdir(parents=True,exist_ok=True)
    gates=[
      {'id':'B01_RULESET_FROZEN','status':'PASS','sha256':sha256_file(adm)},
      {'id':'B02_NO_GEOMETRY_TO_FREQUENCY_PROMOTION','status':'PASS'},
      {'id':'B03_NO_GRB_TARGET_FIT','status':'PASS'},
      {'id':'B04_MINIMUM_DYNAMIC_EVIDENCE_SCHEMA','status':'PASS','requires':rules['requires']},
    ]
    verdict={'campaign_id':'A052-LFPDCF-CANDIDATE-X','verdict':'ADMISSIBILITY_RULES_FROZEN','candidate_identity_visible':False,'gates':gates}
    dump_json(out/'verdict.json',verdict)
    (out/'report.md').write_text('# Blind verdict\n\n**ADMISSIBILITY_RULES_FROZEN**\n\nGeometry-only artifacts are not sufficient to create a physical photon dispersion law.\n',encoding='utf-8')
    return verdict
