from __future__ import annotations
import argparse,json,shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
from .io import resolve_default_input
from .measure import run_measure
from .gates import reveal
from .report import write_report,plots
from .synthetic import generate
from .geometry import cpp_info

def load_cfg(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def default_cfg(name):
    root=Path(__file__).resolve().parents[2];p=root/'config'/f'{name}.json';return p if p.exists() else Path.cwd()/'config'/f'{name}.json'
def stamp(prefix):return Path('outputs')/f'{prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
def cmd_measure(args):
    cfg=load_cfg(args.config);run=Path(args.out) if args.out else stamp(Path(args.config).stem);run.mkdir(parents=True,exist_ok=True);(run/'preregistered_config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');inp=resolve_default_input(args.input,Path.cwd());info=run_measure(inp,run,cfg);(run.parent/'LATEST.txt').write_text(str(run.resolve()),encoding='utf-8');print(json.dumps({'run_dir':str(run.resolve()),**info},indent=2));return run
def cmd_reveal(args):
    run=Path(args.run) if args.run else Path(Path('outputs/LATEST.txt').read_text().strip());cfg=load_cfg(run/'preregistered_config.json');df=pd.read_csv(run/'measurements_blind.csv');rdf,overall=reveal(df,cfg);rdf.to_csv(run/'reveal_gates.csv',index=False);write_report(run,df,rdf,overall);made=plots(df,run);summary={'overall':overall,'n_knots':len(df),'plots':made};(run/'campaign_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps({'run_dir':str(run.resolve()),**summary},indent=2));return overall
def cmd_all(args):run=cmd_measure(args);return cmd_reveal(argparse.Namespace(run=str(run)))
def cmd_selftest(args):
    base=Path(args.out or 'outputs/selftest');shutil.rmtree(base,ignore_errors=True);data=base/'data';generate(data);cfg=load_cfg(args.config);cfg['runtime']['require_cpp']=False;run=base/'run';run.mkdir(parents=True);(run/'preregistered_config.json').write_text(json.dumps(cfg,indent=2));run_measure(data,run,cfg);df=pd.read_csv(run/'measurements_blind.csv');ok=len(df)==2 and (df['status']=='OK').all() and (df['tail_v2_exponent'].astype(float)>2.0).all() and (df['poisson_identity_rel_rms_max'].astype(float)<1e-8).all();res={'ok':bool(ok),'cpp':cpp_info(),'tail_v2_exponents':df['tail_v2_exponent'].tolist()};(base/'SELFTEST.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2));
    if not ok:raise SystemExit(2)
def main():
    ap=argparse.ArgumentParser(description='Einstein-SST emergent metric / Poisson closure blind falsifier');sp=ap.add_subparsers(dest='cmd',required=True)
    for name in ('measure','all'):
        p=sp.add_parser(name);p.add_argument('--input');p.add_argument('--out');p.add_argument('--config',default=str(default_cfg('normal')));p.set_defaults(func=cmd_measure if name=='measure' else cmd_all)
    p=sp.add_parser('reveal');p.add_argument('--run');p.set_defaults(func=cmd_reveal)
    p=sp.add_parser('selftest');p.add_argument('--out',default='outputs/selftest');p.add_argument('--config',default=str(default_cfg('basic')));p.set_defaults(func=cmd_selftest)
    p=sp.add_parser('cpp-info');p.set_defaults(func=lambda a: print(json.dumps(cpp_info(),indent=2)))
    args=ap.parse_args();r=args.func(args);return 0
if __name__=='__main__':raise SystemExit(main())
