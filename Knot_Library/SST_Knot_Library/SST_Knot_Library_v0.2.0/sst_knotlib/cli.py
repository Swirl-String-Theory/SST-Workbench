from __future__ import annotations
import argparse, json
from pathlib import Path
from .geometry import classic_trefoil, shader_track_trefoil, torus_knot, figure8_s3, lissajous_7_4, resample_closed
from .diagnostics import convergence_report, qualify_seed, linking_number
from .frames import thread_bundle
from .io import save_xyz, save_vect
from .formats import load_geometry, save_vect_components
from .blind import make_blind_campaign, verify_blind_campaign
from .runtime import runtime_attestation, write_runtime_attestation
from .registry import KAtlasSnapshot
from .providers import provider_status, crosscheck_reference
from .topology import generate_topology_seed, braid_reference_report
from .records import make_knot_record, write_record
from .dataset import scan_dataset, write_inventory
from .policy import evaluate_record
from .integrity import verify_manifest
from .inventory import inventory_sources
from .library_root import find_knot_library_root, sources_root


def _j(obj): print(json.dumps(obj,indent=2,ensure_ascii=False))

def _write(path, pts):
    path=Path(path)
    if path.suffix.lower()=='.vect': save_vect(path,pts)
    else: save_xyz(path,pts)

def _one_component(path):
    a=load_geometry(path)
    if len(a.components)!=1: raise ValueError(f'expected one component, found {len(a.components)}')
    return a.components[0]


def cmd_generate(a):
    if a.kind=='classic-trefoil': pts=classic_trefoil(a.n,a.scale)
    elif a.kind=='track-trefoil': pts=shader_track_trefoil(a.n,a.R,a.a,a.b,a.offset)
    elif a.kind=='torus': pts=torus_knot(a.p,a.q,a.n,a.R,a.a,a.b)
    elif a.kind=='figure8-s3': pts=figure8_s3(a.n,e=a.e,h=a.h,angle=a.angle,scale=a.scale)
    elif a.kind=='lissajous-7-4': pts=lissajous_7_4(a.n,a.scale)
    else: raise ValueError(a.kind)
    _write(a.out,pts); _j({'out':str(a.out),'N':len(pts),'kind':a.kind})


def cmd_seed_topology(a):
    pts=generate_topology_seed(a.knot_id,method=a.method,n=a.n)
    _write(a.out,pts); _j({'out':a.out,'N':len(pts),'knot_id':a.knot_id,'method':a.method})


def cmd_qualify(a):
    p=_one_component(a.input)
    _j(qualify_seed(p,a.core_radius,a.n,a.min_clearance_core,a.max_kappa_core,a.max_segment_cv))


def cmd_converge(a):
    p=_one_component(a.input); levels=tuple(int(x) for x in a.levels.split(',')); _j(convergence_report(p,levels))


def cmd_bundle(a):
    p=resample_closed(_one_component(a.input),a.n); b=thread_bundle(p,a.threads,a.turns,a.radius,a.phase)
    out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    for i,x in enumerate(b): save_xyz(out/f'thread_{i:03d}.xyz',x)
    L=[]
    for i in range(len(b)):
        for j in range(i+1,len(b)): L.append({'i':i,'j':j,'linking_midpoint':linking_number(b[i],b[j])})
    (out/'bundle_linking.json').write_text(json.dumps(L,indent=2)+'\n',encoding='utf-8',newline='\n')
    _j({'outdir':str(out),'threads':a.threads,'pair_count':len(L)})


def cmd_campaign(a):
    cfg=json.loads(Path(a.config).read_text(encoding='utf-8')); n=int(cfg.get('n',512)); candidates=[]
    for R in cfg['baseR']:
        for ar in cfg['bulge_R']:
            for bz in cfg['z_weave']:
                pts=shader_track_trefoil(n,float(R),float(ar),float(bz),float(cfg.get('plane_offset',-5/(3**0.5))))
                candidates.append((f'track_R{R}_a{ar}_b{bz}',pts,{'family':'track_trefoil','baseR':R,'bulge_R':ar,'z_weave':bz}))
    seed=cfg.get('blind_seed'); commitment=make_blind_campaign(candidates,a.outdir,seed=None if seed is None else int(seed))
    _j({'n_candidates':len(candidates),'outdir':a.outdir,'reveal_commitment_sha256':commitment})


def cmd_verify_campaign(a):
    rep=verify_blind_campaign(a.outdir,require_private=a.require_private); _j(rep)
    if not rep['pass']: raise SystemExit(2)


def cmd_runtime_info(a):
    info=write_runtime_attestation(a.out) if a.out else runtime_attestation(); _j(info)
    if a.require_native and not info.get('native_backend_imported',False): raise SystemExit(2)
    if a.require_openmp and not info.get('openmp_enabled',False): raise SystemExit(3)


def cmd_registry(a):
    r=KAtlasSnapshot()
    if a.knot_id: _j(r.get(a.knot_id).to_dict())
    else: _j(r.report())


def cmd_providers(a): _j(provider_status())

def cmd_crosscheck(a): _j(crosscheck_reference(a.knot_id))

def cmd_braid_info(a): _j(braid_reference_report(a.knot_id))


def cmd_inspect(a):
    levels=tuple(int(x) for x in a.levels.split(','))
    comps,rec=make_knot_record(a.input,expected_topology=a.topology,core_radius=a.core_radius,n=a.n,
        normalize_length=a.normalize_length,topology_provider=a.provider,convergence_levels=levels,format=a.format)
    obj=rec.to_dict()
    obj['entry_policy']=evaluate_record(obj,a.policy)
    if a.out: write_record(a.out,obj)
    _j(obj)
    if a.require_certified and obj['topology_certification'].get('status')!='CERTIFIED': raise SystemExit(4)
    if a.require_geometry_pass and obj.get('qualification') and not obj['qualification'].get('pass',False): raise SystemExit(5)
    if a.require_policy_pass and not obj['entry_policy']['pass']: raise SystemExit(6)


def cmd_integrity(a):
    rep=verify_manifest(a.root,a.manifest); _j(rep)
    if a.require_pass and not rep.get('pass',False): raise SystemExit(7)


def cmd_scan(a):
    root=a.root if a.root else None
    rep=scan_dataset(root,n_hash=a.n,certify=a.certify,provider=a.provider)
    if a.out: write_inventory(a.out,rep)
    _j({'root':rep['root'],'file_count':rep['file_count'],'out':a.out,'load_errors':sum(x.get('load_status')=='ERROR' for x in rep['files']),
        'certified':sum(x.get('topology_certification',{}).get('status')=='CERTIFIED' for x in rep['files'])})


def cmd_inventory(a):
    rep=inventory_sources(write=not a.no_write)
    _j({'out':rep.get('out'),'file_count':rep['file_count'],'moved':rep['moved'],
        'counts_by_provider':rep['counts_by_provider'],'scanned_roots':rep['scanned_roots']})
    if a.require_no_move and rep.get('moved'): raise SystemExit(8)


def main():
    ap=argparse.ArgumentParser(prog='sst-knotlib',description='SST falsifier-grade knot geometry + topology umbrella library')
    sp=ap.add_subparsers(dest='cmd',required=True)
    g=sp.add_parser('generate'); g.add_argument('kind',choices=['classic-trefoil','track-trefoil','torus','figure8-s3','lissajous-7-4']); g.add_argument('--out',required=True); g.add_argument('-n',type=int,default=512); g.add_argument('--scale',type=float,default=0.55); g.add_argument('-p',type=int,default=2); g.add_argument('-q',type=int,default=3); g.add_argument('-R',type=float,default=10/(6**0.5)); g.add_argument('-a',type=float,default=2.0); g.add_argument('-b',type=float,default=3.8); g.add_argument('--offset',type=float,default=-5/(3**0.5)); g.add_argument('-e',type=float,default=0.16); g.add_argument('-H','--h',type=float,default=0.25); g.add_argument('--angle',type=float,default=0.35); g.set_defaults(fn=cmd_generate)
    st=sp.add_parser('seed-from-topology'); st.add_argument('knot_id'); st.add_argument('--method',choices=['auto','classic','s3','lissajous','braid'],default='auto'); st.add_argument('--out',required=True); st.add_argument('-n',type=int,default=512); st.set_defaults(fn=cmd_seed_topology)
    q=sp.add_parser('qualify'); q.add_argument('input'); q.add_argument('--core-radius',type=float,required=True); q.add_argument('-n',type=int,default=512); q.add_argument('--min-clearance-core',type=float,default=2.2); q.add_argument('--max-kappa-core',type=float,default=0.35); q.add_argument('--max-segment-cv',type=float,default=0.03); q.set_defaults(fn=cmd_qualify)
    c=sp.add_parser('converge'); c.add_argument('input'); c.add_argument('--levels',default='256,512,1024'); c.set_defaults(fn=cmd_converge)
    b=sp.add_parser('bundle'); b.add_argument('input'); b.add_argument('--outdir',required=True); b.add_argument('--threads',type=int,default=6); b.add_argument('--turns',type=float,default=3.0); b.add_argument('--radius',type=float,default=0.1); b.add_argument('--phase',type=float,default=0.0); b.add_argument('-n',type=int,default=512); b.set_defaults(fn=cmd_bundle)
    m=sp.add_parser('campaign'); m.add_argument('config'); m.add_argument('--outdir',required=True); m.set_defaults(fn=cmd_campaign)
    v=sp.add_parser('verify-campaign'); v.add_argument('outdir'); v.add_argument('--require-private',action='store_true'); v.set_defaults(fn=cmd_verify_campaign)
    r=sp.add_parser('runtime-info'); r.add_argument('--out'); r.add_argument('--require-native',action='store_true'); r.add_argument('--require-openmp',action='store_true'); r.set_defaults(fn=cmd_runtime_info)
    kr=sp.add_parser('registry'); kr.add_argument('knot_id',nargs='?'); kr.set_defaults(fn=cmd_registry)
    pr=sp.add_parser('providers'); pr.set_defaults(fn=cmd_providers)
    cr=sp.add_parser('crosscheck-reference'); cr.add_argument('knot_id'); cr.set_defaults(fn=cmd_crosscheck)
    bi=sp.add_parser('braid-info'); bi.add_argument('knot_id'); bi.set_defaults(fn=cmd_braid_info)
    ins=sp.add_parser('inspect'); ins.add_argument('input'); ins.add_argument('--topology'); ins.add_argument('--provider',default='auto'); ins.add_argument('--format',default='auto'); ins.add_argument('--core-radius',type=float); ins.add_argument('-n',type=int,default=512); ins.add_argument('--normalize-length',type=float); ins.add_argument('--levels',default='256,512,1024'); ins.add_argument('--out'); ins.add_argument('--policy',choices=['strict','audit','geometry-only'],default='audit'); ins.add_argument('--require-certified',action='store_true'); ins.add_argument('--require-geometry-pass',action='store_true'); ins.add_argument('--require-policy-pass',action='store_true'); ins.set_defaults(fn=cmd_inspect)
    iv=sp.add_parser('verify-integrity'); iv.add_argument('--root',default='.'); iv.add_argument('--manifest',default='MANIFEST_SHA256.txt'); iv.add_argument('--require-pass',action='store_true'); iv.set_defaults(fn=cmd_integrity)
    sc=sp.add_parser('scan-dataset'); sc.add_argument('root',nargs='?',default=None,help='Dataset root (default: Knot_Library/Sources)'); sc.add_argument('--out'); sc.add_argument('-n',type=int,default=512); sc.add_argument('--certify',action='store_true'); sc.add_argument('--provider',default='auto'); sc.set_defaults(fn=cmd_scan)
    inv=sp.add_parser('inventory-sources'); inv.add_argument('--no-write',action='store_true'); inv.add_argument('--require-no-move',action='store_true'); inv.set_defaults(fn=cmd_inventory)
    a=ap.parse_args(); a.fn(a)

if __name__=='__main__': main()
