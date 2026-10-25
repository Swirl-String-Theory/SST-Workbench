"""A058-v0.3.7 additive native measurement *qualification*, not a physical falsifier.

Inputs are historical user-owned native probe outputs or the separately generated,
non-blind, 32-iteration measurement controls. Never rewrites A058 source, gates,
old observations, or scientific preregistration. Private stdout stays private.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from distribution_audit import BASE_SCRIPT, required_source, sha_file
from shortcut_runtime import knotplot_path, resolve_launcher

SCHEMA = 'A058-NATIVE-MEASUREMENT-QUALIFICATION-1'
CASES = tuple((d, o) for d in (1, 4) for o in ('before', 'after'))
XCOL = ('nbeads', 'length', 'rg', 'iteration')
FATAL = ('unknown command', 'freeglut error:', 'freeglut  error:', 'nothing loaded', 'nothing to save', 'not safe.', 'could not open', 'cannot open')
MAX_EVIDENCE_BYTES = 8_000_000


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_json(b: bytes) -> dict:
    result = json.loads(b.decode('utf-8-sig'))
    if not isinstance(result, dict):
        raise ValueError('Expected JSON object')
    return result


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


class Evidence:
    """Read-only archive/folder view. ZIP member matching is unique and bounded."""
    def __init__(self, source: Path):
        self.source = Path(source).expanduser().resolve(strict=True)
        self.archive = zipfile.ZipFile(self.source) if self.source.is_file() else None
        if self.archive is not None:
            names = self.archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError('Duplicate ZIP member paths are ambiguous')
            if any(n.startswith('/') or '..' in Path(n).parts or '\\' in n for n in names):
                raise ValueError('ZIP has unsafe member paths')
            markers = [n for n in names if n.endswith('NATIVE_RESULTS.json') and n.count('/') <= 2]
            self.prefix = markers[0][:-len('NATIVE_RESULTS.json')] if len(markers) == 1 else ''
            if not self.prefix:
                seeds = [n for n in names if n.endswith('dstep_1/NATIVE_STDOUT_PRIVATE.log') and n.count('/') <= 3]
                if len(seeds) != 1:
                    raise ValueError('Cannot uniquely locate native evidence root in ZIP')
                self.prefix = seeds[0][:-len('dstep_1/NATIVE_STDOUT_PRIVATE.log')]
        else:
            if not self.source.is_dir():
                raise ValueError('Evidence source must be a ZIP or folder')
            self.prefix = ''

    def read(self, rel: str, *, required: bool = False) -> bytes | None:
        if '..' in Path(rel).parts or rel.startswith('/'):
            raise ValueError('Unsafe evidence path')
        if self.archive is None:
            target = (self.source / rel)
            if not target.is_file():
                if required: raise FileNotFoundError(target)
                return None
            if target.stat().st_size > MAX_EVIDENCE_BYTES:
                raise ValueError('Excessive evidence file size: ' + rel)
            return target.read_bytes()
        name = self.prefix + rel
        try:
            info = self.archive.getinfo(name)
        except KeyError:
            if required: raise FileNotFoundError(name) from None
            return None
        if info.file_size > MAX_EVIDENCE_BYTES:
            raise ValueError('Excessive ZIP evidence member size: ' + rel)
        return self.archive.read(info)

    def close(self):
        if self.archive is not None: self.archive.close()


def xyz_points(data: bytes) -> list[tuple[float, float, float]]:
    points = []
    for ln in data.decode('utf-8', errors='replace').splitlines():
        split = ln.split()
        if len(split) != 3: continue
        try: triple = tuple(float(x) for x in split)
        except ValueError: continue
        if all(math.isfinite(x) for x in triple): points.append(triple)
        else: raise ValueError('nonfinite xyz')
    if len(points) < 3: raise ValueError('No complete xyz geometry')
    return points


def geom_metrics(pts):
    n = len(pts)
    seg = [math.dist(pts[i], pts[(i + 1) % n]) for i in range(n)]
    centroid = [sum(p[j] for p in pts) / n for j in range(3)]
    return {'nbeads': n, 'length': sum(seg),
            'rg': math.sqrt(sum(sum((p[j] - centroid[j]) ** 2 for j in range(3)) for p in pts) / n),
            'min_edge': min(seg)}


def _marked(log: str, head: str, tail: str) -> str | None:
    a = log.find(head); b = log.find(tail, a + len(head)) if a >= 0 else -1
    if a < 0 or b < 0 or b <= a: return None
    return log[a + len(head):b]


def _safe_pass(log, kind):
    # Explicitly consume the bounded echo segment; mere absence of an error is not enough.
    marker = f'A058_SAFE_{kind}'
    part = _marked(log, marker, marker + '_END')
    return part is not None and bool(re.search(r'current\s+position\s+is\s+safe\.', part, re.I)) and not re.search(r'not\s+safe', part, re.I)


def _get_readback(log: str, field: str) -> float | None:
    part = _marked(log, 'A058_READBACK_BEGIN', 'A058_READBACK_END')
    if part is None: return None
    m = re.search(r'(?im)^\s*(?:KnotPlot>\s*)?' + re.escape(field) + r'\s*=\s*([-+\d.eE]+)', part)
    return float(m.group(1)) if m and math.isfinite(float(m.group(1))) else None


def _scalar_from_console(log: str) -> dict:
    # The release-2026 console shows `#0: Nb 47 tot 56.757945 ...` and a
    # standalone `KnotPlot> 4.355587` for rog. These are diagnostic, not a
    # replacement for valid CSV or independent XYZ.
    lm = re.search(r'(?im)^#0:\s*Nb\s+(\d+)\s+tot\s+([-+\d.eE]+)', log)
    lm = lm or re.search(r'(?im)\bNb\s+(\d+)\s+tot\s+([-+\d.eE]+)', log)
    rm = re.search(r'(?im)^\s*KnotPlot>\s*([-+]?\d+\.\d+(?:[eE][-+]?\d+)?)\s*$', log)
    return {'length': float(lm.group(2)) if lm else None,
            'length_nbeads': int(lm.group(1)) if lm else None,
            'rg': float(rm.group(1)) if rm else None}


def csv_observation(data: bytes | None) -> dict:
    if data is None: return {'status': 'MISSING_CSV'}
    try:
        rows = list(csv.reader(io.StringIO(data.decode('utf-8-sig'))))
        if len(rows) != 2: return {'status':'UNEXPECTED_ROW_COUNT', 'rows':len(rows)}
        cols = [c.strip().casefold() for c in rows[0]]
        vals = [c.strip() for c in rows[1]]
        if len(cols) != len(vals): return {'status':'INVALID_CSV_SHAPE'}
        wanted = {'nbeads':'nbeads','length':'length','rg':'rog','iteration':'iteration'}
        result = {}
        for key, name in wanted.items():
            if name not in cols: return {'status':'MISSING_COLUMN','column':name}
            number = float(vals[cols.index(name)])
            if not math.isfinite(number): return {'status':'NONFINITE_CSV','column':name}
            result[key] = number
        return {'status':'READABLE', 'values':result,
                'alex_column': 'alex ev.' in cols,
                'alex_value': vals[cols.index('alex ev.')] if 'alex ev.' in cols else None}
    except (UnicodeError, ValueError, csv.Error) as exc:
        return {'status':'MALFORMED_CSV','error_type':type(exc).__name__}


def tolerance(display: float, actual: float) -> bool:
    return abs(display-actual) <= max(2e-5, 1e-6 * abs(actual))


def qualify_case(log_data, xyz_data, csv_data, *, expected_dstep: int, runtime_script: bytes | None = None):
    if log_data is None:
        return {'status':'MISSING_NATIVE_LOG','scientific_status':'UNQUALIFIED'}
    log = log_data.decode('utf-8', errors='replace')
    fatal = [tok for tok in FATAL if tok in log.casefold()]
    external_alex = bool(re.search(r"can['’]?t\s+open\s+file\s+[`'\"]?KP-alex\.exe", log, re.I))
    result = {'native_stdout_sha256': digest(log_data), 'fatal_tokens':fatal,
              'safe_start':_safe_pass(log, 'START'), 'safe_final':_safe_pass(log, 'FINAL'),
              'alex_dependency':'MISSING_OR_UNRESOLVED' if external_alex else 'NOT_DIAGNOSED',
              'readback_dstep':_get_readback(log, 'dstep'),
              'readback_status':'NOT_RECORDED' if 'A058_READBACK_BEGIN' not in log else 'PRESENT',
              'console':_scalar_from_console(log), 'csv':csv_observation(csv_data)}
    if result['readback_dstep'] is not None:
        result['readback_status'] = ('PASS_DISPLAY_PRECISION' if abs(result['readback_dstep']-expected_dstep)<5e-7 else 'MISMATCH')
    if runtime_script is not None:
        script = runtime_script.decode('utf-8', errors='replace')
        result['runtime_script_sha256'] = digest(runtime_script)
        result['script_declares_dstep'] = bool(re.search(r'(?m)^dstep\s*=\s*'+str(expected_dstep)+r'\s*$',script))
        result['script_guards'] = {c:bool(re.search(r'(?m)^'+re.escape(c)+r'\s*$',script)) for c in
                                  ('collision fast','velforce = off','tanf = off','grav = off','therm = off')}
    if xyz_data is None:
        result.update(status='MISSING_COORDINATES',scientific_status='UNQUALIFIED')
        return result
    try:
        pts = xyz_points(xyz_data)
    except ValueError as exc:
        result.update(status='INVALID_COORDINATES',scientific_status='UNQUALIFIED',detail=str(exc))
        return result
    geo = geom_metrics(pts)
    result.update(geometry=geo, coordinate_sha256=digest(xyz_data))
    console = result['console']
    result['console_comparison'] = {
        'length_matches_xyz':console['length'] is not None and tolerance(console['length'],geo['length']),
        'rg_matches_xyz':console['rg'] is not None and tolerance(console['rg'],geo['rg'])}
    csvv = result['csv'].get('values')
    result['csv_comparison'] = {
        'length_matches_xyz':bool(csvv and tolerance(csvv['length'],geo['length'])),
        'rg_matches_xyz':bool(csvv and tolerance(csvv['rg'],geo['rg'])),
        'nbeads_matches_xyz':bool(csvv and csvv['nbeads']==geo['nbeads']),
        'iteration_32':bool(csvv and csvv['iteration']==32),
    }
    scalar = result['csv_comparison']['length_matches_xyz'] and result['csv_comparison']['rg_matches_xyz']
    count = result['csv_comparison']['nbeads_matches_xyz'] and result['csv_comparison']['iteration_32']
    result['scalar_gate'] = 'PASS' if scalar else 'FAIL' if csvv else 'UNRESOLVED'
    result['iteration_gate'] = 'PASS_CSV_RECORDED' if count else 'FAIL_OR_UNRESOLVED'
    result['safety_gate'] = 'PASS_SNAPSHOT_MARKERS_ONLY' if result['safe_start'] and result['safe_final'] else 'FAIL'
    result['parameter_gate'] = ('PASS' if result['readback_status']=='PASS_DISPLAY_PRECISION' else
                                'FAIL' if result['readback_status']=='MISMATCH' else 'UNRESOLVED')
    result['alex_gate'] = 'UNAVAILABLE' if external_alex else 'UNRESOLVED_NOT_IN_SCALAR_GATE'
    result['script_gate'] = ('PASS' if runtime_script is not None and result.get('script_declares_dstep') and
                             all(result.get('script_guards', {}).values()) else 'UNRESOLVED_OR_FAIL')
    other_ok = all(result['console_comparison'].values()) and not fatal and result['safe_start'] and result['safe_final']
    if not other_ok or not scalar or not count or result['parameter_gate']=='FAIL' or result['script_gate']!='PASS':
        result['status']='FAIL_MEASUREMENT_QUALIFICATION'
    elif result['parameter_gate']=='PASS':
        result['status']='QUALIFIED_NUMERICAL_MEASUREMENT_ONLY'
    else:
        result['status']='INCOMPLETE_PARAMETER_READBACK'
    result['scientific_status']='NO_PHYSICAL_CONCLUSION'
    return result


def analyze_existing(source: Path, out: Path) -> dict:
    out = Path(out).resolve()
    if out.exists(): raise FileExistsError('Qualification destination must be NEW; never overwrite')
    ev = Evidence(source)
    try:
        conditions = {}
        for d in (1, 4):
            folder = f'dstep_{d}/'
            # The original v0.3.6 script is intentionally not mutated.
            conditions[f'dstep_{d}'] = qualify_case(ev.read(folder+'NATIVE_STDOUT_PRIVATE.log'),
                ev.read(folder+'A058_final.txt'), ev.read(folder+'A058_native_metrics.csv'),
                expected_dstep=d, runtime_script=ev.read(folder+'probe.native.kpc'))
        record = read_json(ev.read('NATIVE_RESULTS.json',required=True))
        design_data=ev.read('PROBES.json')
        design=read_json(design_data) if design_data is not None else {}
        expected_seed=design.get('seed_sha256')
        seed_digests=[]
        for d in (1,4):
            seed=ev.read(f'dstep_{d}/A058_seed.kpf')
            seed_digests.append(digest(seed) if seed is not None else None)
        seed_integrity=(expected_seed is not None and len(expected_seed)==64 and
                        seed_digests[0]==seed_digests[1]==expected_seed)
        by_dstep={int(x['dstep']):x for x in record.get('conditions',[]) if x.get('dstep') in (1,4)}
        for d in (1,4):
            r=conditions[f'dstep_{d}']; hist=by_dstep.get(d)
            original_script=ev.read(f'dstep_{d}/probe.kpc')
            matches = (hist is not None and hist.get('returncode') == 0 and not hist.get('timeout') and
                       hist.get('private_log_sha256') == r.get('native_stdout_sha256') and
                       hist.get('coordinate_sha256') == r.get('coordinate_sha256') and
                       hist.get('runtime_script_sha256') == r.get('runtime_script_sha256') and
                       original_script is not None and
                       hist.get('source_probe_sha256') == digest(original_script) and seed_integrity)
            r['shared_seed_integrity'] = 'PASS' if seed_integrity else 'FAIL'
            r['original_run_record_gate'] = 'PASS' if matches else 'FAIL'
            if not matches: r['status'] = 'INVALID_HISTORICAL_RECEIPT'
        a,b=(conditions[f'dstep_{v}'] for v in (1,4))
        same = (a.get('coordinate_sha256') is not None and a.get('coordinate_sha256')==b.get('coordinate_sha256'))
        doc = {'schema':SCHEMA,'mode':'READ_ONLY_HISTORICAL_REQUALIFICATION',
               'source_name':Path(source).name,'source_sha256':sha_file(source) if Path(source).is_file() else None,
               'source_mutated':False,'conditions':conditions,
               'negative_control':{'byte_identical':same,'status':'IDENTICAL_EXPORTED_SNAPSHOTS' if same else 'UNRESOLVED_OR_DIFFERENT',
                                   'scope':'matched 32 iterations only; not continuous-time dynamics'},
               'all_measurements_qualified':all(v['status']=='QUALIFIED_NUMERICAL_MEASUREMENT_ONLY' for v in conditions.values()),
               'blind_271_condition_protocol':'UNTOUCHED','physical_model_claim':'UNRESOLVED',
               'no_collision_between_steps':'NOT_CERTIFIED'}
    finally:
        ev.close()
    out.mkdir(parents=True,exist_ok=False)
    write_json(out/'QUALIFICATION.json',doc)
    write_markdown(out/'QUALIFICATION.md',doc)
    write_matrix(out/'MEASUREMENT_MATRIX.csv',doc)
    return doc


def write_matrix(path: Path, doc: dict):
    with path.open('x',newline='',encoding='utf-8') as fp:
        writer=csv.writer(fp)
        writer.writerow(['condition','status','start_safe','final_safe','console_length_vs_xyz',
                         'console_rg_vs_xyz','csv_length_vs_xyz','csv_rg_vs_xyz','csv_iteration_32',
                         'dstep_getter','alex_dependency','coordinate_sha256'])
        for name,res in doc['conditions'].items():
            cv=res.get('csv_comparison',{}); nv=res.get('console_comparison',{})
            writer.writerow([name,res['status'],res.get('safe_start'),res.get('safe_final'),
                            nv.get('length_matches_xyz'),nv.get('rg_matches_xyz'),
                            cv.get('length_matches_xyz'),cv.get('rg_matches_xyz'),cv.get('iteration_32'),
                            res.get('readback_status'),res.get('alex_dependency'),res.get('coordinate_sha256')])


def write_markdown(path: Path, doc: dict):
    lines=['# A058 Native Measurement Qualification', '',
           f"Mode: `{doc['mode']}`; evidence: `{doc.get('source_name','fresh native diagnostic')}`.", '',
           '| Condition | Qualification | CSV length/Rg | Parameter readback | Alex |',
           '|---|---|---|---|---|']
    for name,r in doc['conditions'].items():
        lines.append('| '+ ' | '.join([name,r['status'],r.get('scalar_gate','UNRESOLVED'),r.get('parameter_gate','UNRESOLVED'),r.get('alex_gate','UNRESOLVED')])+' |')
    lines.extend(['','**Qualification does not establish physical stability, Euler dynamics, continuous collision safety, or convergence.**',
                  '', 'Historical source bytes, gate ledgers, and preregistered 271 conditions remain untouched.', ''])
    path.write_text('\n'.join(lines),encoding='utf-8',newline='\n')


def native_script(dstep: int, order: str) -> str:
    if (dstep,order) not in CASES: raise ValueError('Invalid preregistered diagnostic branch')
    setup=BASE_SCRIPT + [f'dstep = {dstep}', 'echo A058_READBACK_BEGIN','parameters','echo A058_READBACK_END',
                          'echo A058_SAFE_START','safe','echo A058_SAFE_START_END',
                          'go 32','echo A058_SAFE_FINAL','safe','echo A058_SAFE_FINAL_END']
    data=['data open A058_native_metrics.csv','data format "/N,/l,/g,/I"','data header']
    measurements=['length','rog']
    lines=setup+(data+measurements if order=='before' else measurements+data)
    lines+=['data','data close','save A058_final.txt ascii']
    return '\n'.join(lines)+'\n'


def generate_measurements(dist: Path, out: Path) -> dict:
    dist=Path(dist).resolve(strict=True);out=Path(out).resolve()
    if out.exists():raise FileExistsError('Measurement output path already exists; new destination required')
    with zipfile.ZipFile(dist) as z:
        root=required_source(z)
        seed=z.read(root+'basic/3.1')
    if len(seed)<100:raise ValueError('Distribution trefoil seed unexpectedly small')
    out.mkdir(parents=True,exist_ok=False)
    conditions=[]
    for d,o in CASES:
        name=f'dstep_{d}_{o}'; wd=out/name;wd.mkdir()
        (wd/'A058_seed.kpf').write_bytes(seed)
        script=native_script(d,o)
        (wd/'probe.kpc').write_text(script,encoding='utf-8',newline='\n')
        conditions.append({'id':name,'dstep':d,'data_open_order':o,'seed_sha256':digest(seed),
                           'script_sha256':digest(script.encode())})
    doc={'schema':'A058-NATIVE-MEASUREMENT-DESIGN-1','distribution_sha256':sha_file(dist),
         'conditions':conditions,'matched_go_iterations':32,'collision_guard':'collision fast',
         'dependency_alex':'EXCLUDED_FROM_SCALAR_VALIDATION; historical KP-alex error audited separately',
         'purpose':'Diagnose cached native CSV and verify independent parameter getter; not A058 blind physics',
         'scientific_protocol':'UNTOUCHED'}
    write_json(out/'MEASUREMENT_DESIGN.json',doc)
    return doc


def _runtime_script(src: str, folder: Path) -> str:
    replacements={
        'load A058_seed.kpf':'load '+knotplot_path(folder/'A058_seed.kpf'),
        'data open A058_native_metrics.csv':'data open '+knotplot_path(folder/'A058_native_metrics.csv'),
        'save A058_final.txt ascii':'save '+knotplot_path(folder/'A058_final.txt')+' ascii',
    }
    lines=src.splitlines()
    for original,new in replacements.items():
        matches=[i for i,line in enumerate(lines) if line.strip()==original]
        if len(matches)!=1:raise ValueError('Expected one command '+original)
        lines[matches[0]]=new
    return '\n'.join(lines)+'\n'


def probe_plan(out: Path) -> list[dict]:
    design=read_json((out/'MEASUREMENT_DESIGN.json').read_bytes())
    if design.get('schema')!='A058-NATIVE-MEASUREMENT-DESIGN-1' or len(design.get('conditions',[]))!=4:
        raise ValueError('Invalid measurement design')
    if [(e['dstep'],e['data_open_order']) for e in design['conditions']] != list(CASES):
        raise ValueError('Measurement condition list changed')
    plan=[]
    for e in design['conditions']:
        wd=out/e['id'];sp=wd/'probe.kpc';seed=wd/'A058_seed.kpf'
        if not sp.is_file() or not seed.is_file(): raise FileNotFoundError(f'Generated input missing for {e["id"]}')
        if sha_file(sp)!=e['script_sha256'] or sha_file(seed)!=e['seed_sha256']:
            raise ValueError(f'Generated input hash mismatch for {e["id"]}')
        if sp.read_text(encoding='utf-8')!=native_script(e['dstep'],e['data_open_order']):
            raise ValueError('Generated script deviates from v0.3.7 definition')
        for name in ('probe.native.kpc','NATIVE_STDOUT_PRIVATE.log','A058_native_metrics.csv','A058_final.txt'):
            if (wd/name).exists():raise FileExistsError(f'Existing native evidence: {wd/name}')
        plan.append({**e,'folder':wd,'script':_runtime_script(sp.read_text(encoding='utf-8'),wd)})
    if (out/'NATIVE_RESULTS.json').exists() or (out/'NATIVE_LAUNCH_PRIVATE.json').exists():
        raise FileExistsError('Previous native result present; refuse overwrite')
    return plan


def run_measurements(exe, out: Path, timeout: int, *, workdir=None, dist=None) -> dict:
    if timeout <= 0:raise ValueError('positive timeout required')
    out=Path(out).resolve()
    if not out.exists() and dist is not None:
        generate_measurements(dist,out)
    plan=probe_plan(out)  # all plans validated before first process starts
    launcher=resolve_launcher(exe,workdir_override=workdir)
    # Read-only sidecar diagnostic; does not copy or call KP-alex.exe.
    search_locations=[launcher.workdir/'KP-alex.exe', launcher.executable.parent/'KP-alex.exe']
    path_candidate=shutil.which('KP-alex.exe')
    if path_candidate:search_locations.append(Path(path_candidate))
    alex_diag={'status':'FOUND_CANDIDATE_NOT_FUNCTIONALLY_VERIFIED' if any(x.is_file() for x in search_locations)
                else 'NOT_FOUND_IN_STANDARD_SEARCH_LOCATIONS',
               'searched':list(dict.fromkeys(str(p) for p in search_locations)),
               'note':'KnotPlot helper lookup may use additional internal rules; only native alex -1 confirms operation'}
    write_json(out/'NATIVE_LAUNCH_PRIVATE.json',{
        'executable':str(launcher.executable),'executable_sha256':sha_file(launcher.executable),
        'workdir':str(launcher.workdir),'workdir_source':launcher.workdir_source,
        'shortcut':str(launcher.shortcut) if launcher.shortcut else None,
        'shortcut_arguments':launcher.shortcut_args,'io_policy':'EXPLICIT_ABSOLUTE_A058_OUTPUTS',
        'native_console_is_private':True})
    results={}
    for e in plan:
        wd=e['folder'];(wd/'probe.native.kpc').write_text(e['script'],encoding='utf-8',newline='\n')
        rawlog=wd/'NATIVE_STDOUT_PRIVATE.log'
        rc=None;timedout=False
        try:
            with (wd/'probe.native.kpc').open('rb') as inputfile, rawlog.open('xb') as logfile:
                cp=subprocess.run(launcher.command(),cwd=launcher.workdir,executable=str(launcher.executable),
                     stdin=inputfile,stdout=logfile,stderr=subprocess.STDOUT,timeout=timeout,check=False)
                rc=cp.returncode
        except subprocess.TimeoutExpired:
            timedout=True
        qualification=qualify_case(rawlog.read_bytes() if rawlog.exists() else None,
            (wd/'A058_final.txt').read_bytes() if (wd/'A058_final.txt').exists() else None,
            (wd/'A058_native_metrics.csv').read_bytes() if (wd/'A058_native_metrics.csv').exists() else None,
            expected_dstep=e['dstep'],runtime_script=(wd/'probe.native.kpc').read_bytes())
        if rc != 0 or timedout:
            qualification['status']='FAILED_NATIVE_PROCESS_OR_TIMEOUT'
        qualification.update({'process_returncode':rc,'timeout':timedout, 'data_open_order':e['data_open_order']})
        results[e['id']]=qualification
    doc={'schema':SCHEMA,'mode':'NEW_NATIVE_DIAGNOSTIC','conditions':results,
         'all_measurements_qualified':all(r['status']=='QUALIFIED_NUMERICAL_MEASUREMENT_ONLY' for r in results.values()),
         'blind_271_condition_protocol':'UNTOUCHED','physical_model_claim':'UNRESOLVED',
         'alex_helper_preflight':alex_diag,
         'no_collision_between_steps':'NOT_CERTIFIED','native_attempted':True}
    write_json(out/'NATIVE_RESULTS.json',doc)
    # Public qualification separate from raw logs, which remain private in condition dirs.
    sub=out/'qualification';sub.mkdir(exist_ok=False)
    write_json(sub/'QUALIFICATION.json',doc)
    write_markdown(sub/'QUALIFICATION.md',doc)
    write_matrix(sub/'MEASUREMENT_MATRIX.csv',doc)
    return doc


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['QUALIFY_EXISTING','GENERATE_MEASUREMENTS','RUN_MEASUREMENTS'])
    p.add_argument('--source',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--dist',type=Path)
    p.add_argument('--exe',type=Path)
    p.add_argument('--workdir',type=Path)
    p.add_argument('--timeout',type=int,default=120)
    args=p.parse_args(argv)
    if args.mode=='QUALIFY_EXISTING' and args.source is None:p.error('--source required')
    if args.mode in ('GENERATE_MEASUREMENTS','RUN_MEASUREMENTS') and args.dist is None and args.mode=='GENERATE_MEASUREMENTS':p.error('--dist required')
    if args.mode=='RUN_MEASUREMENTS' and args.exe is None:p.error('--exe required')
    try:
        if args.mode=='QUALIFY_EXISTING':
            doc=analyze_existing(args.source,args.out)
        elif args.mode=='GENERATE_MEASUREMENTS':
            doc=generate_measurements(args.dist,args.out)
        else:
            doc=run_measurements(args.exe,args.out,args.timeout,workdir=args.workdir,dist=args.dist)
        print(json.dumps({'mode':args.mode,'out':str(args.out),'qualified':doc.get('all_measurements_qualified'),
                          'cases':len(doc['conditions'])},sort_keys=True),flush=True)
        # Analysis can write a valid negative result; exit code 2 differentiates scientific qualification failure.
        return 0 if args.mode=='GENERATE_MEASUREMENTS' or doc.get('all_measurements_qualified') else 2
    except (ValueError,FileNotFoundError,FileExistsError,RuntimeError,OSError,zipfile.BadZipFile) as exc:
        print(f'A058 {args.mode} FAIL-CLOSED: {type(exc).__name__}: {exc}',file=sys.stderr,flush=True)
        return 3

if __name__=='__main__':raise SystemExit(main())
