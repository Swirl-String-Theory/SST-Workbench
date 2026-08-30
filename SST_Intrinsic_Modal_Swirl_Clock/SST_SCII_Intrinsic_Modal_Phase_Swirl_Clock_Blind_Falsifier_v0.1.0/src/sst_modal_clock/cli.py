import argparse,json
from .workflow import run_prepare,run_prepare_provenance,run_scan_provenance,run_branch,run_analyze_stage_a,run_analyze_stage_a_gauge,run_analyze_provenance,run_analyze_stage_b,run_analyze_sc2_stage_a,run_analyze_sc2_gauge,run_analyze_sc2_provenance,run_analyze_sc2_stage_b,reveal
from .resolution import compare
from .selftest import run as selftest
from .util import clean_json

def main(argv=None):
    p=argparse.ArgumentParser(prog='sst-modal-clock');s=p.add_subparsers(dest='cmd',required=True)
    a=s.add_parser('prepare');a.add_argument('dataset');a.add_argument('work');a.add_argument('config')
    a=s.add_parser('prepare-provenance');a.add_argument('work');a.add_argument('config');a.add_argument('--libraries',default=None,help='Comma-separated: Fremlin,Gilbert,Katlas,KnotPlot');a.add_argument('--min-carriers',type=int,default=None,help='Minimum distinct source-library families per topology');a.add_argument('--kind',choices=['all','knots','links'],default=None);a.add_argument('--topology',default=None,help='Single topology selector, e.g. 3_1, K3.1, L2a1, L2.2.1')
    a=s.add_parser('scan-provenance');a.add_argument('config');a.add_argument('--libraries',default=None,help='Comma-separated: Fremlin,Gilbert,Katlas,KnotPlot');a.add_argument('--min-carriers',type=int,default=None,help='Minimum distinct source-library families per topology');a.add_argument('--kind',choices=['all','knots','links'],default=None);a.add_argument('--topology',default=None,help='Single topology selector, e.g. 3_1, K3.1, L2a1, L2.2.1')
    a=s.add_parser('run');a.add_argument('work');a.add_argument('config');a.add_argument('--branch',choices=['stage_a','stage_a_gauge_low','stage_a_gauge_high','material','fixed'],required=True);a.add_argument('--limit',type=int)
    a=s.add_parser('analyze-stage-a');a.add_argument('work');a.add_argument('config')
    a=s.add_parser('analyze-stage-a-gauge');a.add_argument('work');a.add_argument('config')
    a=s.add_parser('analyze-provenance');a.add_argument('work');a.add_argument('config')
    a=s.add_parser('analyze-stage-b');a.add_argument('work');a.add_argument('config')
    a=s.add_parser('analyze-sc2-stage-a');a.add_argument('work');a.add_argument('config')
    a=s.add_parser('analyze-sc2-gauge');a.add_argument('work');a.add_argument('config')
    a=s.add_parser('analyze-sc2-provenance');a.add_argument('work');a.add_argument('config')
    a=s.add_parser('analyze-sc2-stage-b');a.add_argument('work');a.add_argument('config')
    a=s.add_parser('reveal');a.add_argument('work')
    a=s.add_parser('resolution');a.add_argument('work64');a.add_argument('work96');a.add_argument('work128');a.add_argument('out')
    s.add_parser('selftest');ns=p.parse_args(argv)
    if ns.cmd=='prepare':o=run_prepare(ns.dataset,ns.work,ns.config)
    elif ns.cmd=='prepare-provenance':o=run_prepare_provenance(ns.work,ns.config,ns.libraries,ns.min_carriers,ns.kind,ns.topology)
    elif ns.cmd=='scan-provenance':o=run_scan_provenance(ns.config,ns.libraries,ns.min_carriers,ns.kind,ns.topology)
    elif ns.cmd=='run':o=run_branch(ns.work,ns.config,ns.branch,ns.limit)
    elif ns.cmd=='analyze-stage-a':o=run_analyze_stage_a(ns.work,ns.config)
    elif ns.cmd=='analyze-stage-a-gauge':o=run_analyze_stage_a_gauge(ns.work,ns.config)
    elif ns.cmd=='analyze-provenance':o=run_analyze_provenance(ns.work,ns.config)
    elif ns.cmd=='analyze-stage-b':o=run_analyze_stage_b(ns.work,ns.config)
    elif ns.cmd=='analyze-sc2-stage-a':o=run_analyze_sc2_stage_a(ns.work,ns.config)
    elif ns.cmd=='analyze-sc2-gauge':o=run_analyze_sc2_gauge(ns.work,ns.config)
    elif ns.cmd=='analyze-sc2-provenance':o=run_analyze_sc2_provenance(ns.work,ns.config)
    elif ns.cmd=='analyze-sc2-stage-b':o=run_analyze_sc2_stage_b(ns.work,ns.config)
    elif ns.cmd=='reveal':o=reveal(ns.work)
    elif ns.cmd=='resolution':o=compare([ns.work64,ns.work96,ns.work128],ns.out)
    else:o=selftest()
    print(json.dumps(clean_json(o),indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
