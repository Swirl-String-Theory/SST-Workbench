"""Separate comparison lanes, NEVER included in A054 admission decisions."""
import pathlib,json,hashlib,sys,numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from screen import run_case,sha256_bytes,serialize
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'REFERENCE_OVERLAYS.jsonl'
rows=[]
def scan(id_,comps,meta):
    b=('\n\n'.join('\n'.join(' '.join(format(v,'.17g') for v in row) for row in comp) for comp in comps)+'\n').encode('utf8')
    rec={'source_case_id':id_,'source_kind':meta['source_family'],'knotplot_catalog_id':id_,
         'roles':['REFERENCE_ONLY'],'torus':None}
    res=run_case(rec,b,True,2)
    res['overlay_metadata']=meta
    rows.append(res)
    print(id_,res['arms']['native']['hessian'].get('last_pair_rel_l2'),flush=True)
for p in sorted((ROOT/'inputs'/'reference_a054').glob('*.npz')):
    z=np.load(p,allow_pickle=False);comps=[z[k] for k in sorted(z.files)]
    scan('E013_'+p.name.split('__')[0],comps,{'source_family':'E013_GILBERT_REFERENCE',
      'original_npz_sha256':sha256_bytes(p.read_bytes()),'npz_name':p.name,
      'independent_upstream_provider':False,'admission':'REFERENCE_ONLY_NO_HANDOFF'})
for p in sorted((ROOT/'inputs'/'relaxed_examples').glob('*.txt')):
    from screen import parse_native
    scan('AGO_'+p.name.split('_ago')[0].replace('.','p'),parse_native(p.read_bytes()),
         {'source_family':'KNOTPLOT_AGO_BUILD_REFERENCE','original_txt_sha256':sha256_bytes(p.read_bytes()),
         'filename':p.name,'independent_upstream_provider':False,'admission':'REFERENCE_ONLY_NO_HANDOFF'})
OUT.write_text(''.join(serialize(x)+'\n' for x in rows),encoding='utf8')
print('overlay_completed',len(rows),flush=True)
