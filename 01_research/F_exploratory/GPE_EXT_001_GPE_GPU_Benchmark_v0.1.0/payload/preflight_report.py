
"""Fail closed before FREEZE if the preregistered LaTeX report is not compilable.
Do not write into the frozen source or final output directory.
"""
from __future__ import annotations
from pathlib import Path
import sys,tempfile,shutil,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework_bootstrap import load_framework
load_framework()
from sst_falsifier.report import write_auto_science_tex,write_auto_results_tex,compile_report_pdf

def main():
    with tempfile.TemporaryDirectory(prefix='gpe_report_preflight_') as td:
        tmp=Path(td)
        d=tmp/'report';d.mkdir()
        shutil.copyfile(ROOT/'report'/'FALSIFIER_REPORT.tex',d/'FALSIFIER_REPORT.tex')
        write_auto_science_tex(ROOT,d/'AUTO_SCIENCE_CONTRACT.tex')
        # Generate representative automatic tables, including gate ledger and qualification.
        out=tmp/'out';out.mkdir()
        (out/'GATE_LEDGER.json').write_text(json.dumps({'records':[
            {'gate_id':'G2','status':'PASS','question':'Analytic solution check',
             'reason':'Preflight diagnostic','qualification':'QUALIFIED','blocked_by':[]},
            {'gate_id':'G8','status':'UNRESOLVED','question':'External PKLSA comparison',
             'reason':'No comparable field source','qualification':'UNRESOLVED','blocked_by':['G4']}]}),encoding='utf8')
        write_auto_results_tex(ROOT,out,d/'AUTO_RESULTS.tex')
        compiled=compile_report_pdf(d/'FALSIFIER_REPORT.tex',tmp/'preflight.pdf',strict=True)
        print('GPE PDF preflight:',compiled['status'])
if __name__=='__main__':main()
