#!/usr/bin/env python3
"""Read KnotPlot native LO[F/D]C v1.0 files (big-endian) without inventing component boundaries.
Run from the extracted package's parent directory or pass a census directory.
Only KnotPlot's native output files count toward a native census, not the legacy relaxed XYZ files.
"""
import argparse,csv,hashlib,json,math,struct,sys
from pathlib import Path

def parse_native(path):
    bs=path.read_bytes(); sep=bs.find(b'\x0c')
    if sep<0 or not bs.startswith(b'KnotPlot 1.0'):
        raise ValueError('Missing KnotPlot 1.0 header/formfeed: not a recognized native file')
    pos=sep+2   # FORM FEED followed by one arbitrary byte (normally newline)
    if pos>len(bs): raise ValueError('Truncated after formfeed')
    components=[]; current=None; fields=[]
    while pos<len(bs):
        if pos+4>len(bs):raise ValueError('Truncated field name')
        raw=bs[pos:pos+4];pos+=4
        try: name=raw.decode('ascii')
        except: raise ValueError('Non-ASCII field name')
        fields.append(name)
        if name=='endf': break
        if name=='comp':
            current={'points':[],'closed':True,'attr_raw':None}
            components.append(current)
            continue
        if name[:2].islower():
            # No-data fields: their interpretation is not needed for geometry.
            continue
        if name[:2].isupper():
            if pos+4>len(bs):raise ValueError('Truncated length prefix')
            nbytes=struct.unpack_from('>I',bs,pos)[0];pos+=4
            if pos+nbytes>len(bs):raise ValueError('Field length exceeds file')
            payload=bs[pos:pos+nbytes];pos+=nbytes
            if name in ('LOCF','LOCD'):
                if current is None:
                    raise ValueError('Coordinates before comp delimiter: ambiguous component membership')
                w=12 if name=='LOCF' else 24
                fmt='>fff' if name=='LOCF' else '>ddd'
                if nbytes%w:raise ValueError('Coordinate field has non-multiple-of-vector byte length')
                for xyz in struct.iter_unpack(fmt,payload):
                    if not all(math.isfinite(t) for t in xyz):raise ValueError('Nonfinite vertex')
                    current['points'].append(xyz)
            elif name=='LOCS' or name=='LOCC':
                raise ValueError('Quantized LOCS/LOCC not supported: export with "save ... float"')
        elif name[0].isupper() and name[1].islower():
            if pos+4>len(bs):raise ValueError('Truncated scalar field')
            payload=bs[pos:pos+4];pos+=4
            if name=='Attr' and current is not None:
                # KnotPlot docs call this bit 1: assume LSB is the closure bit.
                flags=struct.unpack('>I',payload)[0]
                current['closed']=bool(flags&1)
                current['attr_raw']=flags
        else:raise ValueError('Unrecognized field class: '+name)
    else:
        raise ValueError('Native file missing endf')
    if not components or any(len(c['points'])<3 for c in components):
        raise ValueError('Empty/malformed component')
    return components, fields

def component_stats(c):
    pts=c['points']; n=len(pts)
    pairs=list(zip(pts,pts[1:]))
    if c['closed']:pairs.append((pts[-1],pts[0]))
    edges=[math.dist(p,q) for p,q in pairs]
    if not edges or min(edges)<=0:raise ValueError('Zero-length edge')
    return {'N_beads':n,'L_polygon_units':sum(edges),'ds_mean_units':sum(edges)/len(edges),
      'ds_min_units':min(edges),'ds_max_units':max(edges),'ds_max_over_min':max(edges)/min(edges),
      'ds_CV':(sum((e-sum(edges)/len(edges))**2 for e in edges)/len(edges))**0.5/(sum(edges)/len(edges)),
      'closed':c['closed'],'attr_raw':c['attr_raw']}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--census-dir',type=Path,default=Path('Build_Knot_Link_Torus_KnotPlot_Scripts/falsifier_census_v0.1.0'))
    p.add_argument('--out',type=Path,default=None);args=p.parse_args(argv)
    basedir=args.census_dir;targets=json.loads((basedir/'census_targets.json').read_text())['targets']
    out=args.out or (basedir/'audit_reports');out.mkdir(parents=True,exist_ok=True)
    recs=[]; components=[]; incomplete=0
    for row in targets:
        label=f'{row["kind"]}_{row["id"]}';path=basedir/'raw_native'/f'{label}.kpf';csvfile=basedir/'metrics'/f'{label}.csv'
        entry={'id':row['id'],'kind':row['kind'],'seed_type':row['baseline_type'],'file':str(path),'exists':path.exists(),
               'source_SHA256':hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,'status':'MISSING'}
        if path.exists():
            try:
                cc, fields=parse_native(path)
                cs=[component_stats(c) for c in cc]
                entry.update({'component_count':len(cs),'N_total':sum(t['N_beads'] for t in cs),
                    'L_total_polygon_units':sum(t['L_polygon_units'] for t in cs),
                    'status':'PARSED_NATIVE_UNVERIFIED_CATALOGUE_ID'})
                for k,c in enumerate(cs):components.append({'id':row['id'],'kind':row['kind'],'component':k,**c})
                if csvfile.exists():
                    with csvfile.open(newline='',encoding='utf-8-sig') as h:
                        metric=list(csv.reader(h))
                    numbers=[v for rr in metric for v in rr if v.strip()]
                    numeric=[]
                    for v in numbers:
                        try:numeric.append(float(v.strip()))
                        except ValueError:pass
                    if len(numeric)>=2:
                        cn,cl=numeric[0:2]
                        entry['knotplot_data_N']=cn;entry['knotplot_data_L']=cl
                        # Float saved coordinates need not match double in-memory values bit-for-bit.
                        if int(round(cn))==entry['N_total'] and abs(cl-entry['L_total_polygon_units'])<=max(1e-4,2e-6*max(1,abs(cl))):
                            entry['status']='NUMERICALLY_VALIDATED_PENDING_LOAD_PROVENANCE'
                        else:
                            entry['status']='FAILED_NATIVE_METRICS_DISAGREE'
                    else:entry['status']='FAILED_BAD_METRICS_CSV'
                else:entry['status']='FAILED_MISSING_METRICS_CSV'
            except (OSError,ValueError,struct.error) as exc:
                entry['status']='FAILED_PARSE';entry['error']=str(exc)
        if entry['status'] not in ('NUMERICALLY_VALIDATED_PENDING_LOAD_PROVENANCE',):incomplete+=1
        recs.append(entry)
    with (out/'baseline_summary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['id','kind','seed_type','status','component_count','N_total','L_total_polygon_units','source_SHA256'],extrasaction='ignore');w.writeheader();w.writerows(recs)
    fields=['id','kind','component','N_beads','L_polygon_units','ds_mean_units','ds_min_units','ds_max_units','ds_max_over_min','ds_CV','closed','attr_raw']
    with (out/'baseline_components.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(components)
    (out/'audit.json').write_text(json.dumps({'gate':'NATIVE_CENSUS','status':'UNRESOLVED' if incomplete else 'NUMERICALLY_VALIDATED_PENDING_LOAD_PROVENANCE',
        'missing_or_failed_count':incomplete,'target_count':len(targets),'entries':recs},indent=2),encoding='utf-8')
    print(f'Targets={len(targets)} rows={len(recs)} component_records={len(components)} missing_or_failed={incomplete}')
    print('Output:',out)
    if incomplete:
        print('UNRESOLVED: cannot certify a census with missing or invalid files')
        return 2
    print('Numerical checks agree; KnotPlot load identity still requires source catalogue/log verification.')
    return 0

if __name__=='__main__':sys.exit(main())
