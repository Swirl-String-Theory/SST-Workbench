import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from tikz_roundfold import dense_xyz,resample3,EXPECTED
from knotplot_io import encode,decode
from measure import projection_crossings,lengths,min_nonlocal
ROOT=Path(__file__).resolve().parents[1]

def dump(p,data):p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def export_case(label,n,scale=12.):
    raw,cert=dense_xyz(label)
    p=resample3(raw,n)*scale
    cross=projection_crossings(p)
    lim=min_nonlocal(p,neighbor_skip=max(4,int(n*.005)))
    if len(cross)!=EXPECTED[label][0]:raise RuntimeError('resampled crossing count mismatch')
    clearance=min(abs(c['dz']) for c in cross)
    if lim['distance']<.12 or clearance<.15:raise RuntimeError(f'unsafe clearance at {label} N{n}: {lim},dz={clearance}')
    base=f'TikZRoundFold_{label}_N{n:04d}'
    out=ROOT/'output'/'individual'/base;out.mkdir(parents=True,exist_ok=True)
    data=encode([p]);p2=decode(data)[0]
    assert np.array_equal(p,p2)
    (out/f'{base}.kpt').write_bytes(data)
    np.savetxt(out/f'{base}.xyz',p,fmt='%.17g')
    (out/f'{base}_LOAD.kpc').write_text(f'reset all\nload output/individual/{base}/{base}.kpt\ninformation\nlength\nparameters\n',encoding='ascii')
    (out/f'{base}_GO1.kpc').write_text('go 1\n',encoding='ascii')
    (out/f'{base}_GO32.kpc').write_text('go 32\n',encoding='ascii')
    (out/f'{base}_SNAPSHOT.kpc').write_text(f'coords output/individual/{base}/{base}_AFTER.xyz\n',encoding='ascii')
    report={'version':'0.2.1','status':'STATIC_CANDIDATE','source':'user supplied 14 TikZ control points',
            'case':base,'topology':{k:cert[k] for k in ('label','crossings','alexander_coefficients','determinant')},
            'source_interpolation':cert['interpolant'],'tikz_p10_regularization':cert['regularization_P10_dy'],
            'knotplot_separation_units':lim,'crossing_gap_min':clearance,
            'lengths':lengths(p),'sha256_kpt':hashlib.sha256(data).hexdigest(),
            'limitations':['interpolation is not exactly the Hobby shortcut','KnotPlot go has not run',
                           '3D topology during relaxation is not certified','no Euler/finite-core physics'],
            'gates':{'projection_crossings':'PASS','alexander_determinant':'PASS','kpt_roundtrip':'PASS',
                     'discretized_clearance':'PASS','KnotPlot_runtime':'NOT_TESTED',
                     'ambient_isotopy_continuation':'UNRESOLVED','Euler_PKLSA':'NOT_TESTED'}}
    dump(out/'REPORT.json',report)
    print(base,'min_self',round(lim['distance'],6),'min_crossing_z',round(clearance,6))
    return report

def main():
    a=argparse.ArgumentParser();a.add_argument('--n',type=int,default=512);a.add_argument('--scale',type=float,default=12.);opt=a.parse_args()
    if opt.n<256:raise ValueError('n>=256')
    reports=[export_case(s,opt.n,opt.scale) for s in ('5_2','6_1')]
    skeleton_reference()
    dump(ROOT/'LATEST_BUILD.json',{'status':'STATIC_CANDIDATE','reports':[{'case':r['case'],'status':r['status']} for r in reports]})


def skeleton_reference():
    # Provide a genuine Borromean three-component base; do NOT splice local knots in this release.
    import braid_backend as b
    raw=b.base_components()
    dest=ROOT/'output'/'borromean'/'Borromean_skeleton_ONLY'
    dest.mkdir(parents=True,exist_ok=True)
    blob=encode(raw)
    assert all(np.array_equal(x,y) for x,y in zip(raw,decode(blob)))
    (dest/'Borromean_skeleton_ONLY.kpt').write_bytes(blob)
    for i,p in enumerate(raw):np.savetxt(dest/f'component_{i}.xyz',p,fmt='%.17g')
    (dest/'Borromean_skeleton_ONLY_LOAD.kpc').write_text('reset all\nload output/borromean/Borromean_skeleton_ONLY/Borromean_skeleton_ONLY.kpt\ninformation\nlength\n',encoding='ascii')
    pairing={f'{i}-{j}':b.ringlinking(raw[i],raw[j]) for i,j in [(0,1),(0,2),(1,2)]}
    dump(dest/'REPORT.json',{'status':'SKELETON_ONLY_NO_TWIST_COMPONENTS',
        'source':'closure of (sigma_1 sigma_2^-1)^3',
        'component_vertex_counts':[len(p) for p in raw],
        'pairwise_linking_quadrature':pairing,
        'triple_linking_independent':'UNRESOLVED',
        'decorated_tikz_roundfold_5_2_5_2_6_1':'NOT_IMPLEMENTED'})

if __name__=='__main__':main()
