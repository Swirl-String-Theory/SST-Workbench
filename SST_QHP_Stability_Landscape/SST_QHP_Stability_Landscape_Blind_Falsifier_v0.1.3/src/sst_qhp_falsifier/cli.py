import argparse,json
from pathlib import Path
from .geometry import write_metadata_template, bootstrap_metadata
from .prepare import prepare
from .run import run
from .analyze import analyze
from .reveal import reveal
from .selftest import selftest
from .demo import make_demo

def cfg(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def main(argv=None):
    ap=argparse.ArgumentParser(prog='sst-qhp'); sp=ap.add_subparsers(dest='cmd',required=True)
    p=sp.add_parser('metadata-template'); p.add_argument('root'); p.add_argument('--out')
    p=sp.add_parser('metadata-bootstrap'); p.add_argument('root')
    p=sp.add_parser('prepare'); p.add_argument('root'); p.add_argument('out'); p.add_argument('config'); p.add_argument('--metadata')
    p=sp.add_parser('run'); p.add_argument('prepared'); p.add_argument('out'); p.add_argument('config')
    p=sp.add_parser('analyze'); p.add_argument('blind'); p.add_argument('out'); p.add_argument('config')
    p=sp.add_parser('reveal'); p.add_argument('prepared'); p.add_argument('analysis'); p.add_argument('out')
    p=sp.add_parser('selftest')
    p=sp.add_parser('demo'); p.add_argument('root')
    a=ap.parse_args(argv)
    if a.cmd=='metadata-template': out,n=write_metadata_template(a.root,a.out); z={'path':str(out),'n_rows':n}
    elif a.cmd=='metadata-bootstrap':
        z=bootstrap_metadata(a.root)
        print(json.dumps(z,indent=2,default=str))
        return 0 if z.get('ready') else 2
    elif a.cmd=='prepare': z=prepare(a.root,a.out,cfg(a.config),a.metadata)
    elif a.cmd=='run': z=run(a.prepared,a.out,cfg(a.config))
    elif a.cmd=='analyze': z=analyze(a.blind,a.out,cfg(a.config))
    elif a.cmd=='reveal': z=reveal(a.prepared,a.analysis,a.out)
    elif a.cmd=='selftest': z=selftest()
    elif a.cmd=='demo': z={'n':make_demo(a.root),'root':a.root}
    print(json.dumps(z,indent=2,default=str))
if __name__=='__main__': raise SystemExit(main())
