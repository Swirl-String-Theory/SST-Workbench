from __future__ import annotations
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parent
from framework_bootstrap import load_framework
FRAMEWORK_ROOT=load_framework()
from sst_falsifier.runner import run_mode,instance_output_root
from sst_falsifier.config import load_instance_config
from sst_falsifier.outputs import make_output_manifest,pack_revealed
from sst_falsifier.report import write_auto_results_tex,publish_instance_report
from sst_falsifier.util import write_json

def _refresh_instance_reveal():
    cfg=load_instance_config(ROOT); out=instance_output_root(ROOT,cfg)
    from private.reveal_analysis import run_reveal_analysis
    run_reveal_analysis(ROOT,out)
    make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    write_auto_results_tex(ROOT,out,out/'report'/'AUTO_RESULTS.tex')
    render=publish_instance_report(ROOT,out/'report'/'FALSIFIER_REPORT.tex',strict=False)
    write_json(out/'REPORT_RENDER.json',render)
    make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    z=ROOT.parent/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs_REVEALED.zip"
    pack_revealed(out,z)

def main():
    mode=sys.argv[1].upper() if len(sys.argv)>1 else 'BASIC'
    rc=run_mode(ROOT,mode)
    if rc==0 and mode in {'REVEAL','REVEAL_IF_ALLOWED'}:
        cfg=load_instance_config(ROOT); out=instance_output_root(ROOT,cfg); decision=out/'REVEAL_DECISION.json'
        performed=(mode=='REVEAL')
        if decision.is_file():
            try: performed=bool(json.loads(decision.read_text(encoding='utf-8')).get('performed',False))
            except Exception: performed=False
        if performed: _refresh_instance_reveal()
    return rc
if __name__=='__main__': raise SystemExit(main())
