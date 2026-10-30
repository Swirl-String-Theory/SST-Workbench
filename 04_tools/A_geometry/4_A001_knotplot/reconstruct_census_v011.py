#!/usr/bin/env python3
"""Read-only reconstruction of KnotPlot census v0.1.0 KPF/ASCII files.

Never rewrites original metrics or native exports; records their defects as evidence.
This script certifies coordinate parse/parity only, NOT KnotPlot catalogue identity.
Usage: python reconstruct_census_v011.py INPUT.zip OUTPUT_DIRECTORY
"""
import csv, hashlib, io, json, math, re, statistics, struct, sys, zipfile
from collections import Counter
from pathlib import Path

def sha(bs): return hashlib.sha256(bs).hexdigest()

def parse_kpf(bs):
    marker=bs.find(b'\x0c')
    if marker<0 or not bs.startswith(b'KnotPlot 1.0') or marker+1>=len(bs):
        raise ValueError('missing KnotPlot 1.0 header')
    pos=marker+2
    cs=[]; current=None
    while pos<len(bs):
        if pos+4>len(bs): raise ValueError('truncated field name')
        key=bs[pos:pos+4].decode('ascii');pos+=4
        if key=='endf':
            if bs[pos:].strip(b'\r\n\x00\t '): raise ValueError('unexpected trailing bytes after endf')
            break
        if key=='comp':
            current={'points':[],'closed':True};cs.append(current)
        elif key[:2].islower():
            continue
        elif key[:2].isupper():
            if pos+4>len(bs): raise ValueError('truncated field length')
            size=struct.unpack_from('>I',bs,pos)[0];pos+=4
            if pos+size>len(bs): raise ValueError('truncated field payload')
            payload=bs[pos:pos+size];pos+=size
            if key in ('LOCF','LOCD'):
                if current is None:raise ValueError('coordinates without component')
                fmt='>fff' if key=='LOCF' else '>ddd'; n=struct.calcsize(fmt)
                if size % n: raise ValueError('malformed coordinate length')
                current['points'] += list(struct.iter_unpack(fmt,payload))
            if key in ('LOCS','LOCC'):raise ValueError('unsupported quantized coords')
        elif key[0].isupper() and key[1].islower():
            if pos+4>len(bs): raise ValueError('truncated scalar')
            value=struct.unpack_from('>I',bs,pos)[0];pos+=4
            if key=='Attr':
                if current is None: raise ValueError('Attr before comp')
                current['closed']=bool(value & 1)
        else:raise ValueError('unexpected field '+key)
    else:raise ValueError('missing endf')
    if not cs or any(len(c['points'])<3 for c in cs):raise ValueError('insufficient vertices')
    if any(not c['closed'] for c in cs):raise ValueError('open component: requires separate segment policy')
    if any(not all(math.isfinite(x) for p in c['points'] for x in p) for c in cs):raise ValueError('nonfinite coordinates')
    return cs

def parse_ascii(bs):
    cs=[]; current=[]
    for line in bs.decode('utf-8-sig').splitlines():
        line=line.strip()
        if not line:
            if current:cs.append(current);current=[]
            continue
        parts=line.split()
        if len(parts)!=3:raise ValueError('not an XYZ triplet')
        p=tuple(map(float,parts))
        if not all(map(math.isfinite,p)):raise ValueError('nonfinite ASCII coordinate')
        current.append(p)
    if current:cs.append(current)
    return cs

def component_metrics(pts):
    ds=[math.dist(a,b) for a,b in zip(pts,pts[1:]+pts[:1])]
    if any(x<=0 for x in ds):raise ValueError('zero length segment')
    total=math.fsum(ds);mean=total/len(ds)
    return {'N_beads':len(pts),'L_polygon_units':total,'ds_mean_units':mean,
           'ds_min_units':min(ds),'ds_max_units':max(ds),'ds_max_over_min':max(ds)/min(ds),
           'ds_cv':statistics.pstdev(ds)/mean,'bbox_x_units':max(p[0] for p in pts)-min(p[0] for p in pts),
           'bbox_y_units':max(p[1] for p in pts)-min(p[1] for p in pts),
           'bbox_z_units':max(p[2] for p in pts)-min(p[2] for p in pts),
           'N_for_ds_1p2_reference_only':math.ceil(total/1.2)}

def dump_csv(path, rows, columns):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main():
    if len(sys.argv)!=3:raise SystemExit('Usage: python reconstruct_census_v011.py INPUT.zip OUTPUT_DIR')
    archive=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        bad=z.testzip()
        if bad:raise ValueError('CRC failure: '+bad)
        files={Path(x).name:x for x in z.namelist() if x.endswith('.json')}
        targets=json.loads(z.read(files['census_targets.json']))['targets']
        all_names=z.namelist()
        prefixes={n.split('raw_native/')[0] for n in all_names if '/raw_native/' in n}
        if len(prefixes)!=1:raise ValueError('ambiguous raw_native directories')
        base=next(iter(prefixes))
        totals=[];components=[];issues=[];states=Counter()
        for row in targets:
            key=f"{row['kind']}_{row['id']}";
            raw=z.read(f'{base}raw_native/{key}.kpf')
            ascii_blob=z.read(f'{base}raw_native/{key}.txt')
            original_csv=list(csv.reader(io.StringIO(z.read(f'{base}metrics/{key}.csv').decode('utf-8-sig'))))
            native=parse_kpf(raw);ascii_cs=parse_ascii(ascii_blob)
            if len(native)!=len(ascii_cs):raise ValueError(f'{key}: number of ASCII components does not match KPF')
            amax=0.0
            metrics=[]
            for i,(n,ac) in enumerate(zip(native,ascii_cs)):
                pts=n['points']
                if len(pts)!=len(ac):raise ValueError(f'{key}: vertex counts disagree component {i}')
                amax=max(amax,max(abs(a-b) for p,q in zip(pts,ac) for a,b in zip(p,q)))
                m=component_metrics(pts)
                m.update({'kind':row['kind'],'id':row['id'],'component':i,'N_closed_segments':len(pts),
                          'source_sha256_kpf':sha(raw)})
                metrics.append(m);components.append(m)
            if amax>5e-5:raise ValueError(f'{key}: ASCII disagrees with KPF (>5e-5 coordinate units): {amax}')
            n_tot=sum(m['N_beads'] for m in metrics)
            l_tot=math.fsum(m['L_polygon_units'] for m in metrics)
            csv_N=int(float(original_csv[1][0]));csv_L=float(original_csv[1][1]);
            if csv_N!=n_tot:raise ValueError(f'{key}: source csv N={csv_N} != native {n_tot}')
            if not math.isclose(csv_L,l_tot,rel_tol=2e-6,abs_tol=1e-4):
                issues.append({'geometry':key,'issue':'L_total CSV is invalid','original':csv_L,'reconstructed':l_tot})
            expect=None
            if row['kind']=='torus':
                p,q=map(int,row['id'].split('.'));expect=math.gcd(p,q)
                if expect!=len(metrics):raise ValueError(f'{key}: component count != gcd(p,q)')
            entry={'kind':row['kind'],'id':row['id'],'seed_type':row['baseline_type'],
                   'components':len(metrics),'expected_torus_components':expect,
                   'N_beads':n_tot,'L_polygon_units':l_tot,'ds_overall_units':l_tot/n_tot,
                   'ds_min_component_units':min(m['ds_mean_units'] for m in metrics),
                   'ds_max_component_units':max(m['ds_mean_units'] for m in metrics),
                   'source_kpf_SHA256':sha(raw),'source_ascii_SHA256':sha(ascii_blob),
                   'ascii_max_abs_coordinate_delta':amax,'source_csv_L':csv_L,
                   'source_csv_N':csv_N,'native_vs_ascii':'PARITY_PASS',
                   'geometry_status':'RECONSTRUCTED_PARSABLE_NOT_CATALOGUE_CERTIFIED',
                   'native_script_action':row['action']}
            totals.append(entry);states[row['kind']]+=1
    dump_csv(out/'baseline_geometry_RECONSTRUCTED.csv',totals,list(totals[0]))
    dump_csv(out/'baseline_components_RECONSTRUCTED.csv',components,list(components[0]))
    dump_csv(out/'upstream_csv_failures.csv',issues,['geometry','issue','original','reconstructed'])
    s={ 'audit_version':'0.1.1', 'upstream_zip_sha256':sha(archive.read_bytes()),
       'status':'GEOMETRY_RECONSTRUCTED_UPSTREAM_LENGTH_CSV_INVALID',
       'catalogue_identity':'UNVERIFIED_NO_KNOTPLOT_CONSOLE_LOG',
       'objects':len(totals),'components':len(components),'families':dict(states),
       'source_csv_length_failures':len(issues),
       'native_ascii_parity_pass':len(totals),
       'reference_ds_units':1.2,'reference_ds_status':'DIAGNOSTIC_NOT_PHYSICAL_OR_CERTIFIED',
       'all_closed':True,
       'torus_component_gcd_conformance':True,
       'ranges_by_family':{}
     }
    for fam in ('knot','link','torus'):
        cc=[c for c in components if c['kind']==fam]
        rr=[r for r in totals if r['kind']==fam]
        ds=[c['ds_mean_units'] for c in cc]
        s['ranges_by_family'][fam]={'objects':len(rr),'components':len(cc),'min_mean_ds':min(ds),
          'median_mean_ds':statistics.median(ds),'max_mean_ds':max(ds),
          'min_total_L':min(x['L_polygon_units'] for x in rr),
          'max_total_L':max(x['L_polygon_units'] for x in rr)}
    (out/'audit_summary.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
    readme='''# Read-only correction of the v0.1.0 KnotPlot census

The provided `metrics/*.csv` files report zero in their length columns for **all 50** objects. This is false: valid non-zero closed geometry is preserved in native `.kpf` and the corresponding ASCII exports. The KnotPlot CLI `data format "/N,/l"` is documented, but why the running scripts returned zero has not been established without console logs or rerunning KnotPlot. Do not silently overwrite those CSVs.

This audit reconstructs all lengths from **closed polygonal XYZ edges including the last-to-first edge, separately for every component**. It checks binary KPF (`LOCF`, network-endian float) against ASCII, count parity, finiteness, and expected gcd(p,q) component count for constructed torus links.

Native coordinates are in original KnotPlot units, **not SI**, and the torus cases are `torus p q` procedural constructs using KnotPlot's current settings, not immutable catalogue loads. No relaxation or sampling has been performed. The column `N_for_ds_1p2_reference_only` is a scenario diagnostic, not a prescription; the original geometry must remain intact.

## Certification limits

* Geometry: parsable and cross-format equivalent within `5e-5` coordinate units.
* Source identity: pending KnotPlot stdout/source catalogue hashes.
* Torus dynamics and topology: NOT validated by the gcd component-count check alone.
* Biot–Savart/finite-core dynamical resolution: NOT qualified by constant bead spacing.

## How to run

`py -3 reconstruct_census_v011.py falsifier_census_v0.1.0_output.zip OUTDIR`

Do not modify the original ZIP. Re-test the *KnotPlot* CSV writer in a new run by moving `length` to just before the `data` command and checking whether the zero value persists. Until it is understood, **use native-coordinate calculations as the primary audit**, not the `data /l` field.
'''
    (out/'README_AUDIT.md').write_text(readme,encoding='utf-8')
    sums=[]
    for p in sorted(out.iterdir()):
        if p.is_file():sums.append(f'{sha(p.read_bytes())}  {p.name}')
    (out/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
    print('OBJECTS',len(totals),'COMPONENTS',len(components),'ORIGINAL_CSV_LENGTH_FAILURES',len(issues),'KPF_ASCII_PARITY',len(totals))
    for fam,rec in s['ranges_by_family'].items():
        print(f"{fam}: objects={rec['objects']} components={rec['components']} median_ds={rec['median_mean_ds']:.6f} min_ds={rec['min_mean_ds']:.6f} max_ds={rec['max_mean_ds']:.6f}")
    print('EXAMPLES',[(r['kind']+'_'+r['id'],r['N_beads'],round(r['L_polygon_units'],6)) for r in totals if (r['kind'],r['id']) in [('knot','3.1'),('knot','4.1'),('link','6.3.3'),('torus','3.3'),('torus','6.21')]])
    print('RESULT',s['status'])

if __name__=='__main__':main()
