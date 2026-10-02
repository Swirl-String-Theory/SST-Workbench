from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from .geometry import classic_trefoil, shader_track_trefoil, torus_knot, figure8_s3, resample_closed, fourier_smooth
from .diagnostics import convergence_report, qualify_seed, linking_number
from .frames import thread_bundle, ribbon_edges
from .io import save_xyz, load_xyz, save_vect
from .blind import make_blind_campaign, verify_blind_campaign


def _write(path, pts):
    path=Path(path)
    if path.suffix.lower()=='.vect': save_vect(path,pts)
    else: save_xyz(path,pts)


def cmd_generate(a):
    if a.kind=='classic-trefoil': pts=classic_trefoil(a.n,a.scale)
    elif a.kind=='track-trefoil': pts=shader_track_trefoil(a.n,a.R,a.a,a.b,a.offset)
    elif a.kind=='torus': pts=torus_knot(a.p,a.q,a.n,a.R,a.a,a.b)
    elif a.kind=='figure8-s3': pts=figure8_s3(a.n,e=a.e,h=a.h,angle=a.angle,scale=a.scale)
    else: raise ValueError(a.kind)
    _write(a.out,pts)
    print(json.dumps({'out':str(a.out),'N':len(pts),'kind':a.kind},indent=2))


def cmd_qualify(a):
    p=load_xyz(a.input)
    rep=qualify_seed(p,a.core_radius,a.n,a.min_clearance_core,a.max_kappa_core,a.max_segment_cv)
    print(json.dumps(rep,indent=2))


def cmd_converge(a):
    p=load_xyz(a.input)
    levels=tuple(int(x) for x in a.levels.split(','))
    print(json.dumps(convergence_report(p,levels),indent=2))


def cmd_bundle(a):
    p=load_xyz(a.input)
    p=resample_closed(p,a.n)
    b=thread_bundle(p,a.threads,a.turns,a.radius,a.phase)
    out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    for i,x in enumerate(b): save_xyz(out/f'thread_{i:03d}.xyz',x)
    L=[]
    for i in range(len(b)):
        for j in range(i+1,len(b)):
            L.append({'i':i,'j':j,'linking_midpoint':linking_number(b[i],b[j])})
    (out/'bundle_linking.json').write_text(json.dumps(L,indent=2),encoding='utf-8')
    print(json.dumps({'outdir':str(out),'threads':a.threads,'pair_count':len(L)},indent=2))


def cmd_campaign(a):
    cfg=json.loads(Path(a.config).read_text(encoding='utf-8'))
    n=int(cfg.get('n',512)); candidates=[]
    for R in cfg['baseR']:
        for ar in cfg['bulge_R']:
            for bz in cfg['z_weave']:
                pts=shader_track_trefoil(n,float(R),float(ar),float(bz),float(cfg.get('plane_offset',-5/(3**0.5))))
                label=f'track_R{R}_a{ar}_b{bz}'
                candidates.append((label,pts,{'family':'track_trefoil','baseR':R,'bulge_R':ar,'z_weave':bz}))
    seed = cfg.get('blind_seed', None)
    commitment=make_blind_campaign(candidates,a.outdir,seed=None if seed is None else int(seed))
    print(json.dumps({'n_candidates':len(candidates),'outdir':a.outdir,'reveal_commitment_sha256':commitment},indent=2))



def cmd_verify_campaign(a):
    rep=verify_blind_campaign(a.outdir,require_private=a.require_private)
    print(json.dumps(rep,indent=2))
    if not rep['pass']:
        raise SystemExit(2)


def main():
    ap=argparse.ArgumentParser(prog='sst-knotlib')
    sp=ap.add_subparsers(dest='cmd',required=True)
    g=sp.add_parser('generate'); g.add_argument('kind',choices=['classic-trefoil','track-trefoil','torus','figure8-s3']); g.add_argument('--out',required=True); g.add_argument('-n',type=int,default=512); g.add_argument('--scale',type=float,default=0.55); g.add_argument('-p',type=int,default=2); g.add_argument('-q',type=int,default=3); g.add_argument('-R',type=float,default=10/(6**0.5)); g.add_argument('-a',type=float,default=2.0); g.add_argument('-b',type=float,default=3.8); g.add_argument('--offset',type=float,default=-5/(3**0.5)); g.add_argument('-e',type=float,default=0.16); g.add_argument('-H','--h',type=float,default=0.25); g.add_argument('--angle',type=float,default=0.35); g.set_defaults(fn=cmd_generate)
    q=sp.add_parser('qualify'); q.add_argument('input'); q.add_argument('--core-radius',type=float,required=True); q.add_argument('-n',type=int,default=512); q.add_argument('--min-clearance-core',type=float,default=2.2); q.add_argument('--max-kappa-core',type=float,default=0.35); q.add_argument('--max-segment-cv',type=float,default=0.03); q.set_defaults(fn=cmd_qualify)
    c=sp.add_parser('converge'); c.add_argument('input'); c.add_argument('--levels',default='256,512,1024'); c.set_defaults(fn=cmd_converge)
    b=sp.add_parser('bundle'); b.add_argument('input'); b.add_argument('--outdir',required=True); b.add_argument('--threads',type=int,default=6); b.add_argument('--turns',type=float,default=3.0); b.add_argument('--radius',type=float,default=0.1); b.add_argument('--phase',type=float,default=0.0); b.add_argument('-n',type=int,default=512); b.set_defaults(fn=cmd_bundle)
    m=sp.add_parser('campaign'); m.add_argument('config'); m.add_argument('--outdir',required=True); m.set_defaults(fn=cmd_campaign)
    v=sp.add_parser('verify-campaign'); v.add_argument('outdir'); v.add_argument('--require-private',action='store_true'); v.set_defaults(fn=cmd_verify_campaign)
    a=ap.parse_args(); a.fn(a)

if __name__=='__main__': main()
