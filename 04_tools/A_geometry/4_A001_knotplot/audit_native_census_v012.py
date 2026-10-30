#!/usr/bin/env python3
"""Read-only KnotPlot census auditor, v0.1.2.

Lengths are reconstructed from native KPF float/double coordinates; the KnotPlot
"data format \"/N,/l\"" zero-length bug cannot affect this audit.
The original native files are never modified. Source identity and physical validity
are NOT certified by geometric/coordinate parity alone.

Usage:
  py -3 audit_native_census_v012.py --zip falsifier_census_v0.1.0_output.zip --out audit_output
  py -3 audit_native_census_v012.py --census-dir Build_Knot_Link_Torus_KnotPlot_Scripts/falsifier_census_v0.1.2
"""
import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import struct
import sys
import zipfile
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_kpf(data):
    sep = data.find(b'\x0c')
    if not data.startswith(b'KnotPlot 1.0') or sep < 0 or sep + 1 >= len(data):
        raise ValueError('Invalid KnotPlot native header')
    pos = sep + 2  # form-feed + one arbitrary post-header byte
    comps = []
    current = None
    saw_end = False
    while pos < len(data):
        if pos + 4 > len(data):
            raise ValueError('Truncated field header')
        try:
            kind = data[pos:pos+4].decode('ascii')
        except UnicodeDecodeError as e:
            raise ValueError('Invalid field name') from e
        pos += 4
        if kind == 'endf':
            saw_end = True
            if data[pos:].strip(b'\x00\t\r\n '):
                raise ValueError('Data after native terminator')
            break
        if kind == 'comp':
            current = {'points': [], 'closed': True}
            comps.append(current)
            continue
        if kind[:2].islower():
            continue
        if kind[:2].isupper():
            if pos + 4 > len(data):
                raise ValueError('Truncated payload length')
            length = struct.unpack_from('>I', data, pos)[0]
            pos += 4
            if pos + length > len(data):
                raise ValueError('Truncated payload')
            payload = data[pos:pos+length]
            pos += length
            if kind in {'LOCF','LOCD'}:
                if current is None:
                    raise ValueError('Coordinates without component')
                fmt = '>fff' if kind == 'LOCF' else '>ddd'
                width = struct.calcsize(fmt)
                if length % width:
                    raise ValueError('Misaligned coordinate payload')
                current['points'].extend(struct.iter_unpack(fmt, payload))
            elif kind in {'LOCC','LOCS'}:
                raise ValueError('Quantized KPF not supported; export `save ... float`')
        elif kind[0].isupper() and kind[1].islower():
            if pos + 4 > len(data):
                raise ValueError('Truncated scalar field')
            scalar = struct.unpack_from('>I', data, pos)[0]
            pos += 4
            if kind == 'Attr':
                if current is None:
                    raise ValueError('Attribute without component')
                current['closed'] = bool(scalar & 1)
        else:
            raise ValueError('Unknown native field class ' + kind)
    if not saw_end:
        raise ValueError('Native terminator missing')
    if not comps:
        raise ValueError('No components')
    for c in comps:
        if not c['closed']:
            raise ValueError('Open components not in census closure policy')
        if len(c['points']) < 3:
            raise ValueError('Too few points')
        if not all(math.isfinite(z) for p in c['points'] for z in p):
            raise ValueError('Nonfinite coordinate')
    return comps


def parse_ascii(data):
    components, current = [], []
    for line in data.decode('utf-8-sig').splitlines():
        line = line.strip()
        if not line:
            if current:
                components.append(current)
                current = []
            continue
        fields = line.split()
        if len(fields) != 3:
            raise ValueError('Expected ASCII XYZ triples')
        point = tuple(map(float, fields))
        if not all(math.isfinite(v) for v in point):
            raise ValueError('Nonfinite ASCII coordinate')
        current.append(point)
    if current:
        components.append(current)
    return components


def component_metrics(points):
    if len(points) < 3 or not all(math.isfinite(v) for p in points for v in p):
        raise ValueError('Invalid polygon coordinates')
    edge = [math.dist(a,b) for a,b in zip(points, points[1:] + points[:1])]
    if min(edge) <= 0:
        raise ValueError('Zero-length segment')
    n = len(points)
    length = math.fsum(edge)
    mean = length/n
    return {
        'N_beads':n, 'L_polygon_units':length,
        'ds_mean_units':mean, 'ds_min_units':min(edge),
        'ds_max_units':max(edge), 'ds_max_over_min':max(edge)/min(edge),
        'ds_cv':statistics.pstdev(edge)/mean,
        'bbox_x_units':max(p[0] for p in points)-min(p[0] for p in points),
        'bbox_y_units':max(p[1] for p in points)-min(p[1] for p in points),
        'bbox_z_units':max(p[2] for p in points)-min(p[2] for p in points),
    }


class Source:
    def __init__(self, dirpath=None, archive=None):
        self.dirpath = Path(dirpath) if dirpath else None
        self.archive = zipfile.ZipFile(archive) if archive else None
        if self.archive:
            bad = self.archive.testzip()
            if bad:
                raise ValueError('Invalid ZIP member '+bad)
            names = self.archive.namelist()
            manifest = [n for n in names if n.endswith('/census_targets.json') or n == 'census_targets.json']
            if len(manifest) != 1:
                raise ValueError('Expected exactly one census_targets.json')
            self.prefix = manifest[0][:-len('census_targets.json')]
        else:
            self.prefix = ''
    def read(self, filename):
        if self.archive:
            return self.archive.read(self.prefix + filename)
        return (self.dirpath / filename).read_bytes()
    def try_read(self, filename):
        try:
            return self.read(filename)
        except (KeyError,FileNotFoundError):
            return None
    def close(self):
        if self.archive:
            self.archive.close()


def csv_write(path, rows, headers):
    with path.open('w', newline='', encoding='utf-8') as file:
        w = csv.DictWriter(file, fieldnames=headers, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def audit(src, out):
    targets = json.loads(src.read('census_targets.json'))['targets']
    out.mkdir(parents=True,exist_ok=True)
    per_object, per_component, failures = [],[],[]
    for t in targets:
        label = f"{t['kind']}_{t['id']}"
        try:
            kpf = src.read(f'raw_native/{label}.kpf')
            txt = src.read(f'raw_native/{label}.txt')
            comp = parse_kpf(kpf)
            ascii_comp = parse_ascii(txt)
            if len(comp) != len(ascii_comp):
                raise ValueError('KPF/ASCII component counts differ')
            parity_max = 0.0
            cm = []
            for j,(c,ac) in enumerate(zip(comp,ascii_comp)):
                pp = c['points']
                if len(pp) != len(ac):
                    raise ValueError(f'KPF/ASCII bead count mismatch at component {j}')
                parity_max = max(parity_max, max(abs(a-b) for p,q in zip(pp,ac) for a,b in zip(p,q)))
                m=component_metrics(pp)
                m.update({'kind':t['kind'],'id':t['id'],'component_index':j,
                          'source_sha256_kpf':sha(kpf),'evidence_class':'NATIVE_GEOMETRY'})
                cm.append(m)
            if parity_max > 5e-5:
                raise ValueError('KPF/ASCII maximum coordinate mismatch > 5e-5 units')
            if t['kind'] == 'torus':
                p,q=(int(x) for x in t['id'].split('.'))
                if len(cm) != math.gcd(p,q):
                    raise ValueError('torus component count differs from gcd(p,q)')
            N=sum(m['N_beads'] for m in cm)
            L=math.fsum(m['L_polygon_units'] for m in cm)
            original=src.try_read(f'metrics/{label}.csv')
            old_len=''
            old_status='NOT_PRESENT'
            if original:
                old_rows=list(csv.reader(io.StringIO(original.decode('utf-8-sig'))))
                try:
                    vals=old_rows[1]
                    old_n=int(float(vals[0]));old_len=float(vals[1]);
                    old_status=('LEGACY_LENGTH_INVALID' if abs(old_len-L)>max(1e-4,2e-6*L) else 'LEGACY_LENGTH_AGREES')
                    if old_n!=N:
                        old_status='LEGACY_COUNT_MISMATCH'
                except (IndexError,ValueError):
                    old_status='LEGACY_METRIC_NOT_PARSEABLE'
            entry={'kind':t['kind'],'id':t['id'],'seed_type':t['baseline_type'],
                   'N_total':N,'component_count':len(cm),'L_total_polygon_units':L,
                   'ds_overall_units':L/N,'kpf_ascii_max_coordinate_delta_units':parity_max,
                   'KPF_SHA256':sha(kpf),'ASCII_SHA256':sha(txt),
                   'legacy_KnotPlot_L':old_len,'legacy_csv_status':old_status,
                   'geometric_status':'GEOMETRY_PARITY_PASS_SOURCE_ID_UNVERIFIED'}
            per_object.append(entry)
            per_component.extend(cm)
        except (ValueError,UnicodeError,KeyError,OSError,struct.error,ZeroDivisionError) as e:
            failures.append({'geometry':label,'failure':str(e)})
    if per_object:
        csv_write(out/'baseline_geometry_v012.csv',per_object,list(per_object[0]))
    if per_component:
        csv_write(out/'baseline_components_v012.csv',per_component,list(per_component[0]))
    csv_write(out/'failed_cases_v012.csv',failures,['geometry','failure'])
    summary = {
       'version':'0.1.2','source_records_expected':len(targets),
       'objects_parsed':len(per_object),'components_parsed':len(per_component),
       'failure_count':len(failures),'legacy_zero_or_bad_csv_count':sum(x['legacy_csv_status'] not in ('LEGACY_LENGTH_AGREES','NOT_PRESENT') for x in per_object),
       'legacy_csv_absent_count':sum(x['legacy_csv_status']=='NOT_PRESENT' for x in per_object),
       'geometric_status':'PARITY_PASS' if len(per_object)==len(targets) and not failures else 'UNRESOLVED',
       'KnotPlot_catalogue_identity':'UNVERIFIED',
       'scientific_finite_core_convergence':'NOT_TESTED',
       'unit':'original KnotPlot coordinate units (not SI)',
       'policy':'Lengths recomputed from KPF; never use /l=0 as geometry measurement',
       'partial_data_are_not_qualification':True,
    }
    (out/'AUDIT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    checks = []
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != 'SHA256SUMS.txt':
            checks.append(f'{sha(p.read_bytes())}  {p.name}')
    (out/'SHA256SUMS.txt').write_text('\n'.join(checks)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    return 0 if summary['geometric_status']=='PARITY_PASS' else 2


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--zip',type=Path)
    group.add_argument('--census-dir',type=Path)
    parser.add_argument('--out',type=Path,default=Path('SST_KnotPlot_Census_v0.1.2_audit'))
    args=parser.parse_args(argv)
    src=Source(dirpath=args.census_dir,archive=args.zip)
    try:return audit(src,args.out)
    finally:src.close()

if __name__=='__main__':sys.exit(main())
