#!/usr/bin/env python3
"""F005 v0.5.0-p2. Read-only evidence audit for raw acquisition and initial state.

Never imports or executes downloaded acquisition code. Never opens DATASET.zip.
Never reads NPY response matrices (TRAIN, DEV_VALIDATION, TEST or OOD).
Does not write the v0.5.0 geometry file or set its certification flags.
Python 3.10+, standard library only.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = 'F005_v0.5.0-p2'
SPLIT_SHA256 = 'd60bfe0daa8195290958ca0b8f6268e01bf93811267e6c80b02cfadaa84d37a2'
CAMILOTTO_SHA256 = 'e8db99ce4623942ff621a0c01cbb375afa6b22ef8524083e00dd5ea405d33add'
EXPECTED = {'tank_length_internal_m':.080, 'tank_width_internal_m':.031,
            'fill_depth_m':.043, 'sensor_x_from_center_m':.040,
            'liquid_density_kg_m3':998., 'surface_tension_N_m':0.,
            'gravity_m_s2':9.81, 'n_modes':4}
PATTERNS = {
  'acceleration_axis': re.compile(r'\b(accel(?:eration)?|acceleration_axis_sign|ddot|x_ddot|robot.{0,16}axis|axis.{0,16}sign|input_train|end.?effector)\b',re.I),
  'height_axis': re.compile(r'\b(elev(?:ation)?|height|wall|sign|theta|atan|slope|output_train|angle)\b',re.I),
  'premotion': re.compile(r'\b(pre.?motion|pre.?start|baseline|before.{0,12}motion|equilib|stationary|reset|1000|synchron|timestamp|motion.?start)\b',re.I),
}
ALLOWED_SUFFIXES = {'.py','.cpp','.c','.h','.hpp','.m','.txt','.md','.json','.yaml','.yml','.ini','.cfg'}
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_RAW_CSV_BYTES = 64 * 1024 * 1024


def sha256_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def within(child, root):
    root=root.resolve(); child=child.resolve()
    try: child.relative_to(root); return True
    except ValueError: return False


def split_audit(path, expected_hash=SPLIT_SHA256, expected_count=3400, expected_total=4250):
    if not path.is_file():
        return {'status':'BLOCKED_SPLIT_NOT_FOUND', 'path':str(path)},set()
    actual=sha256_file(path)
    if actual!=expected_hash:
        return {'status':'BLOCKED_SPLIT_SHA256_CHANGED','actual_sha256':actual,'expected_sha256':expected_hash},set()
    with path.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    ids=[]; dev=[]; groups={}
    try:
        for r in rows:
            row=int(r['row_id_zero_based']); partition=r['partition']; cid=r['proxy_component_id']
            if row<0 or row>=5000 or partition not in ('DEV_TRAIN','DEV_VALIDATION'):raise ValueError('Invalid row or partition')
            ids.append(row)
            if partition=='DEV_TRAIN':dev.append(row)
            groups.setdefault(cid,set()).add(partition)
    except (KeyError,ValueError) as exc:
        return {'status':'BLOCKED_SPLIT_SCHEMA','error':str(exc)},set()
    if len(rows)!=expected_total or len(set(ids))!=expected_total or len(dev)!=expected_count or any(len(v)>1 for v in groups.values()):
        return {'status':'BLOCKED_SPLIT_INTEGRITY','train_rows':len(dev),'rows':len(rows)},set()
    return {'status':'LOCKED_INPUT_ONLY_SPLIT_VERIFIED','sha256':actual,'train_rows':len(dev),
            'development_validation_rows':len(rows)-len(dev),'family_cross_edges_in_registered_graph':0},set(dev)


def candidate_lines(text, max_each=40):
    out={k:[] for k in PATTERNS}
    for no,line in enumerate(text.splitlines(),1):
        for k,regex in PATTERNS.items():
            if regex.search(line) and len(out[k])<max_each:
                out[k].append({'line':no,'text':line.strip()[:210]})
    return out


def source_files_audit(folder):
    info={'status':'NO_ACQUISITION_FILES_SUBMITTED','path':str(folder),'files':[],'warnings':[]}
    if not folder.is_dir():return info
    for p in sorted(folder.rglob('*')):
        if not p.is_file():continue
        if not within(p,folder):info['warnings'].append('OUTSIDE_ROOT_REJECTED'); continue
        if p.suffix.lower() not in ALLOWED_SUFFIXES:continue
        if p.stat().st_size>MAX_TEXT_BYTES:
            info['warnings'].append(f'TOO_LARGE_TEXT_SKIPPED: {p.name}');continue
        try:raw=p.read_bytes(); txt=raw.decode('utf-8-sig')
        except UnicodeError:
            info['warnings'].append(f'NON_UTF8_SKIPPED: {p.name}');continue
        info['files'].append({'relative_path':p.relative_to(folder).as_posix(),'size_bytes':len(raw),
             'sha256':hashlib.sha256(raw).hexdigest(),'candidate_lines':candidate_lines(txt),
             'classification':'STATIC_TEXT_CUES_NOT_SOURCE_VERIFICATION'})
    if info['files']:info['status']='CANDIDATE_STATIC_TEXT_FOUND_REVIEW_REQUIRED'
    return info


def zip_loader_audit(path):
    """Open ONLY the named 129MB robot ZIP and read only loader text; no archive execution."""
    result={'status':'NO_ROBOT_ZIP','archive_name':path.name}
    if not path.exists():return result
    if path.name != 'sloshing_zenodo_package_v1.0.0.zip':
        return {'status':'UNEXPECTED_ARCHIVE_NAME_REFUSED','archive_name':path.name}
    try:
        with zipfile.ZipFile(path) as z:
            names=[x for x in z.infolist() if x.filename.lower().endswith('load_dataset.py') and not x.is_dir()]
            if len(names)!=1 or names[0].file_size > MAX_TEXT_BYTES or names[0].compress_size>MAX_TEXT_BYTES:
                return {'status':'LOAD_DATASET_PY_UNAVAILABLE_OR_TOO_LARGE'}
            data=z.read(names[0])
        txt=data.decode('utf-8-sig')
        return {'status':'INSPECTION_LOADER_ONLY_NOT_RAW_EXPORT','member':names[0].filename,
          'member_sha256':hashlib.sha256(data).hexdigest(),'candidate_lines':candidate_lines(txt),
          'source_zip_size_bytes':path.stat().st_size,
          'warning':'Loader is not attestation of original recording axes or pre-motion raw arrays'}
    except (OSError,zipfile.BadZipFile,UnicodeError) as exc:
        return {'status':'LOADER_SCAN_ERROR','error':str(exc)}


def evidence_binding(entry, base, folder):
    """Validate a human-submitted source citation. Cannot validate semantic claims automatically."""
    result={'status':'NOT_SUBMITTED'}
    if not isinstance(entry,dict) or entry.get('value') not in (-1,1):return result
    result['proposed_value']=entry['value']
    rel=entry.get('evidence_relative_file')
    if not isinstance(rel,str) or not rel:return {**result,'status':'REVIEW_NO_EVIDENCE_FILE'}
    path=folder/rel
    if not within(path,folder) or not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
        return {**result,'status':'EVIDENCE_PATH_NOT_ALLOWED'}
    if path.stat().st_size>MAX_TEXT_BYTES:return {**result,'status':'EVIDENCE_FILE_TOO_LARGE'}
    expected=entry.get('evidence_sha256')
    actual=sha256_file(path)
    if not expected or expected.lower()!=actual:return {**result,'status':'SOURCE_HASH_NOT_ATTESTED','actual_sha256':actual}
    try:
        lines=path.read_text(encoding='utf-8-sig').splitlines()
        lo=int(entry.get('start_line'));hi=int(entry.get('end_line'))
    except (UnicodeError,ValueError,TypeError):return {**result,'status':'INVALID_LINE_REFERENCE'}
    if lo<1 or hi<lo or hi>len(lines) or hi-lo>30:return {**result,'status':'LINE_REFERENCE_OUT_OF_BOUNDS'}
    result.update({'status':'SOURCE_BYTES_AND_RANGE_VERIFIED_SEMANTICS_REVIEW_REQUIRED',
                   'evidence_sha256':actual,'lines':[lo,hi],
                   'quoted_lines':[{'line':i+1,'text':lines[i][:200]} for i in range(lo-1,hi)],
                   'reason':'Sign meaning and coordinate-frame chain require human/author interpretation'})
    return result


def raw_premotion_trace(path, motion_start_s, height_field='height_mm', time_field='time_s'):
    """Examine only specifically submitted pre-motion raw CSV, not NPY response matrices."""
    if path.stat().st_size>MAX_RAW_CSV_BYTES:raise ValueError('RAW_FILE_TOO_LARGE')
    times=[];h=[];post=0
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or time_field not in reader.fieldnames or height_field not in reader.fieldnames:
            raise ValueError('REQUIRED_RAW_COLUMNS_ABSENT')
        for r in reader:
            t=float(r[time_field]);v=float(r[height_field])
            if not math.isfinite(t) or not math.isfinite(v):raise ValueError('NONFINITE_RAW_VALUE')
            if times and t<=times[-1] and t<motion_start_s:raise ValueError('PREMOTION_TIMES_NOT_STRICTLY_INCREASING')
            if t<motion_start_s: times.append(t);h.append(v)
            else:post+=1
    n=len(times)
    if not n:raise ValueError('NO_PREMOTION_SAMPLES')
    mean=sum(h)/n
    rms=(sum((v-mean)**2 for v in h)/n)**0.5
    tm=sum(times)/n; var=sum((t-tm)**2 for t in times)
    slope=sum((t-tm)*(v-mean) for t,v in zip(times,h))/var if var else float('nan')
    return {'pre_motion_samples':n,'pre_motion_span_s':times[-1]-times[0],
            'pre_motion_mean_mm':mean,'pre_motion_rms_around_mean_mm':rms,
            'pre_motion_linear_slope_mm_s':slope,'post_motion_samples_seen':post,
            'scalar_pre_motion_1000_samples':'PASS' if n>=1000 else 'FAIL',
            'hydrodynamic_rest_certified':False,
            'explanation':'A stationary scalar free surface is not proof of vanishing interior velocity.'}


def premotion_audit(manifest_rel, folder, train_ids, max_cases=3400):
    info={'status':'NO_RAW_PREMOTION_MANIFEST','evaluated':0,'minimum_1000_sample_cases':0,'cases':[],'errors':[]}
    if not manifest_rel:return info
    p=folder/manifest_rel
    if not within(p,folder) or not p.is_file() or p.suffix.lower()!='.csv':
        info['status']='MANIFEST_NOT_FOUND_OR_UNSAFE';return info
    with p.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    if len(rows)>max_cases:info['status']='MANIFEST_TOO_MANY_ROWS';return info
    seen=set()
    for r in rows:
        try:
            row=int(r['row_id_zero_based'])
            if row not in train_ids:raise ValueError('NOT_IN_LOCKED_DEV_TRAIN')
            if row in seen:raise ValueError('DUPLICATED_ROW')
            seen.add(row)
            rel=r['raw_csv']; path=folder/rel
            if not within(path,folder) or not path.is_file() or path.suffix.lower()!='.csv':
                raise ValueError('RAW_PATH_UNSAFE_OR_ABSENT')
            h=sha256_file(path)
            if h.lower()!=r['sha256'].lower():raise ValueError('RAW_SHA256_MISMATCH')
            data=raw_premotion_trace(path,float(r['motion_start_time_s']))
            data.update({'row_id_zero_based':row,'raw_relative_file':rel,'sha256':h})
            info['cases'].append(data)
            if data['scalar_pre_motion_1000_samples']=='PASS':info['minimum_1000_sample_cases']+=1
        except (KeyError,ValueError,TypeError,OSError) as exc:
            info['errors'].append({'row':r.get('row_id_zero_based'),'error':str(exc)})
    info['evaluated']=len(info['cases'])
    info['status']='RAW_SCALAR_PREMOTION_SCREEN_REVIEW' if not info['errors'] else 'PARTIAL_OR_INVALID_RAW_PREMOTION_EVIDENCE'
    return info


def main_run(root, output, evidence_dir=None, manifest=None, p1=None, split=None, geometry=None):
    root=Path(root).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=True)
    folder=(root/'sources'/'acquisition_evidence') if evidence_dir is None else Path(evidence_dir).resolve()
    mpath=Path(manifest) if manifest else root/'config'/'P2_EVIDENCE_MANIFEST.json'
    p1path=Path(p1) if p1 else root/'outputs'/'f005_e0_provenance_audit_v0.5.0_p1'/'e0_audit_report.json'
    splitpath=Path(split) if split else root/'outputs'/'f005_family_disjoint_v0.4.3'/'proxy_family_development_split.csv'
    cfgpath=Path(geometry) if geometry else root/'config'/'EULER_GEOMETRY_REQUIRED.json'
    report={'tool':VERSION,'utc':datetime.now(timezone.utc).isoformat(),
            'status':'E0_P2_REVIEW_NOT_CERTIFIED',
            'protected_data_policy':'NO_NPY_READ_NO_VALIDATION_TEST_OOD_RESPONSES',
            'source_files_modified':False,'geometry_config_modified':False,
            'gates':{'P2_LOCKED_DEVELOPMENT_SPLIT':'NOT_RUN','P2_GEOMETRY_SOURCE':'NOT_RUN',
                     'P2_STATIC_ACQUISITION_CODE':'NOT_RUN','P2_INPUT_AXIS':'BLOCKED_SOURCE_SEMANTICS',
                     'P2_HEIGHT_AXIS':'BLOCKED_SOURCE_SEMANTICS',
                     'P2_PREMOTION_RAW':'BLOCKED_NO_PER_TRAJECTORY_PROOF',
                     'P2_HYDRODYNAMIC_REST':'BLOCKED_NOT_OBSERVABLE_FROM_SCALAR_TRACE',
                     'P2_PROVENANCE_ATTESTATION':'BLOCKED',
                     'E0_MAIN_EULER_GATE':'BLOCKED','E5_EULER_VALIDATION':'NOT_RUN','E7_PKLSA':'NOT_RUN'}}
    s,train=split_audit(splitpath)
    report['locked_split']=s
    report['gates']['P2_LOCKED_DEVELOPMENT_SPLIT']='PASS' if s['status'].startswith('LOCKED') else 'BLOCKED'
    if cfgpath.exists():
        cfg=read_json(cfgpath)
        matches={k:(cfg.get(k)==v) for k,v in EXPECTED.items()}
        report['geometry']={'source':'Camilotto thesis Tables 1.1, 2.1 and longitudinal wall model',
                            'value_checks':matches,'source_tension_is_model_zero_not_measured':True,
                            'current_polarities':{'input':cfg.get('acceleration_axis_sign'),
                                                  'height':cfg.get('measurement_height_sign')},
                            'geometry_sha256':sha256_file(cfgpath)}
        report['gates']['P2_GEOMETRY_SOURCE']='SOURCE_DOCUMENTED' if all(matches.values()) else 'BLOCKED_GEOMETRY_CHANGED'
    else: report['geometry']={'status':'MISSING_GEOMETRY_CONFIG'}
    report['thesis']={'expected_sha256_for_uploaded_thesis':CAMILOTTO_SHA256,
                      'note':'Reference fingerprint only; thesis not bundled or read during a local audit.'}
    if p1path.exists():
        p1r=read_json(p1path)
        report['p1']={'sha256':sha256_file(p1path), 'status':p1r.get('status'),
                       'relative_polarity_train_only':p1r.get('relative_polarity_train_only'),
                       'initial_state_diagnostic':p1r.get('initial_state_diagnostic'),
                       'warning':'Historical TRAIN-only diagnostic is not raw-axis or rest certification'}
    else:report['p1']={'status':'P1_REPORT_MISSING'}
    report['candidate_acquisition_sources']=source_files_audit(folder)
    report['gates']['P2_STATIC_ACQUISITION_CODE']=report['candidate_acquisition_sources']['status']
    report['robot_zenodo_loader']=zip_loader_audit(root/'sources'/'sloshing_zenodo_package_v1.0.0.zip')
    m={'input_axis':{},'height_axis':{},'raw_premotion_manifest_csv':None}
    if mpath.exists():
        m=read_json(mpath)
        report['evidence_manifest_sha256']=sha256_file(mpath)
    else:report['evidence_manifest_status']='TEMPLATE_MISSING'
    report['input_axis_evidence']=evidence_binding(m.get('input_axis'),root,folder)
    report['height_axis_evidence']=evidence_binding(m.get('height_axis'),root,folder)
    report['premotion_evidence']=premotion_audit(m.get('raw_premotion_manifest_csv'),folder,train) if train else {'status':'SPLIT_NOT_VERIFIED','cases':[]}
    report['manual_review_pending']=['Raw source code must trace the actual exported NPY axis/sign and coordinate-frame transform.',
        'Exact source byte ranges do not certify their physical semantic meaning.',
        'Scalar pre-motion traces cannot demonstrate vanishing 3D vortex/velocity field.',
        'A human/author-reviewed evidence contract and independent initial-state evidence are required before any E0 promotion.',
        'TRAIN-only relative polarity +1 is not raw acquisition provenance.']
    # Explicitly never promote E0: matching citations alone cannot prove the underlying physics.
    (out/'p2_audit_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    lines=['# F005 v0.5.0-p2 - raw acquisition and initial-state audit','',
       '**Scientific status:** `E0_P2_REVIEW_NOT_CERTIFIED`','',
       'Existing E0 configuration was NOT changed. No NPY response matrix or DATASET.zip was opened.','',
       '## Gates','']+[f'- `{k}`: `{v}`' for k,v in report['gates'].items()]
    lines+=['','## Evidence state','',
     '- Development split: '+s['status'],
     '- Acquisition source scan: '+report['candidate_acquisition_sources']['status'],
     '- Robot loader: '+report['robot_zenodo_loader']['status'],
     '- Acceleration axis: '+report['input_axis_evidence']['status'],
     '- Height axis: '+report['height_axis_evidence']['status'],
     '- Pre-motion raw: '+report['premotion_evidence']['status'],
     '- P1 relative sign: TRAIN-only hypothesis +1 preferred, NOT independently verified.','',
     '## Required source material','',
     'Submit the genuine acquisition/export scripts that created INPUT_TRAIN.npy and OUTPUT_TRAIN.npy,',
     'the robot coordinate-frame mapping and the pre-motion raw timestamped traces or per-run logs.',
     'Use `sources/acquisition_evidence/` and then fill `config/P2_EVIDENCE_MANIFEST.json`.',
     'No automatic sign selection or E0 gate promotion is implemented.','']
    (out/'P2_AUDIT_SUMMARY.md').write_text('\n'.join(lines),encoding='utf-8')
    return report


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',default='.')
    ap.add_argument('--out',default=None)
    ap.add_argument('--evidence-dir',default=None)
    ap.add_argument('--manifest',default=None)
    ap.add_argument('--p1',default=None)
    ap.add_argument('--split',default=None)
    ap.add_argument('--geometry',default=None)
    a=ap.parse_args(argv);root=Path(a.root).resolve()
    output=Path(a.out).resolve() if a.out else root/'outputs'/'f005_raw_provenance_v0.5.0_p2'
    r=main_run(root,output,a.evidence_dir,a.manifest,a.p1,a.split,a.geometry)
    print(json.dumps({'status':r['status'],'summary':str(output/'P2_AUDIT_SUMMARY.md'),'out':str(output)}))
    return 0 # A correctly reported BLOCKED scientific gate is not a runner error.

if __name__=='__main__':sys.exit(main())
