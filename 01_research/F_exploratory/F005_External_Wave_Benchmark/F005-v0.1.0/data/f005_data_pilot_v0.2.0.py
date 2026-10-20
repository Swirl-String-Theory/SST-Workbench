#!/usr/bin/env python3
"""F005 v0.2.0 external sloshing DATA PILOT (not a PKLSA falsifier).

Reads extracted robot NPY arrays using memmap and one small CSV directly
from a 49.9 GB sloshing archive. Never unpacks or alters source ZIPs.

Requires: Python >=3.9, numpy, matplotlib (for plots/PDF).
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, os, random, statistics, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = '0.2.0'
ROBOT = ('INPUT_TRAIN.npy', 'OUTPUT_TRAIN.npy', 'time_vector.csv', 'trajectory_metadata.csv')
DEFAULT_MEMBER = 'DATASET/NoBody/2deg/2deg_105_0.4375Hz/Digital_pressure.csv'
REFERENCE = {
    'robot_doi': '10.5281/zenodo.20039757',
    'roll_doi': '10.5281/zenodo.15223412',
    'expected_robot_archive_md5': '0c2e91f4556c7b9fd57c12721d165f95',
    'expected_roll_archive_md5': '0cf4dc4f3a93d7898c3da72b921dce7c',
}

def sha256_file(path: Path, chunksize: int=4*1024*1024)->str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(chunksize),b''): digest.update(block)
    return digest.hexdigest()

def md5_file(path: Path, chunksize: int=8*1024*1024)->str:
    digest = hashlib.md5()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(chunksize),b''): digest.update(block)
    return digest.hexdigest()

def search_robot_data(root: Path)->Path:
    preferred = root/'outputs'/'data_preflight_v0.1.0'/'data'/'robot_sloshing'/'raw_extracted'
    if all((preferred/n).is_file() for n in ROBOT): return preferred
    second = root/'data'/'robot_sloshing'/'raw_extracted'
    if all((second/n).is_file() for n in ROBOT): return second
    raise FileNotFoundError('Robot files not found. Expected all 4 files in '+str(preferred)+'\nRe-run original --extract-robot preflight if necessary.')

def read_time(path: Path, expected: int):
    import numpy as np
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f); rows=list(reader)
    if not rows: return None, {'status':'UNRESOLVED','reason':'Empty time CSV'}
    hdr=[str(x).strip().lower() for x in rows[0]]
    has_header=any(any(c.isalpha() for c in x) for x in hdr)
    content=rows[1:] if has_header else rows
    cols=[]
    for i in range(max(map(len, content)) if content else 0):
        v=[]; ok=True
        for row in content:
            if i>=len(row): ok=False;break
            try: v.append(float(row[i].strip()))
            except (ValueError,IndexError):ok=False;break
        if ok and len(v)==expected and all(math.isfinite(x) for x in v):cols.append((i,v))
    if not cols: return None, {'status':'UNRESOLVED','reason':'No numeric column with expected length','headings':hdr,'rows':len(content)}
    labels=hdr if has_header else ['']*(max(i for i,_ in cols)+1)
    candidates=[item for item in cols if ('time' in labels[item[0]] or 'second' in labels[item[0]] or labels[item[0]].strip() in ('t','t_s','t (s)'))]
    if not candidates: return None, {'status':'UNRESOLVED','reason':'Numeric columns found but no explicit time label; refusing to guess units','headings':hdr}
    index,t=candidates[0]
    differences=np.diff(np.asarray(t,dtype='float64'))
    if not len(differences) or not np.all(differences>0):return None, {'status':'FAIL','reason':'Non-increasing time'}
    dt=float(np.median(differences))
    jitter=float(np.max(np.abs(differences-dt)))
    status='PASS' if jitter<max(1e-7,0.01*dt) else 'REVIEW'
    return np.asarray(t,dtype='float64'), {'status':status,'column':labels[index],'dt_seconds':dt,'duration_seconds':float(t[-1]-t[0]),'max_dt_deviation_seconds':jitter,'samples':expected}

def csv_metadata_header(path: Path):
    with path.open('r',newline='',encoding='utf-8-sig') as f:
        reader=csv.reader(f);hdr=next(reader,[])
        n=sum(1 for _ in reader)
    return {'headers':hdr,'rows':n}

def diagnostic_frequency(y,dt):
    import numpy as np
    n=len(y)
    if n<16 or dt is None:return None
    d=y-np.mean(y)
    power=np.abs(np.fft.rfft(d*np.hanning(n)))**2
    hz=np.fft.rfftfreq(n,dt)
    if len(hz)<3:return None
    i=1+int(np.argmax(power[1:]))
    return {'peak_hz':float(hz[i]),'resolution_hz':float(1/(n*dt)), 'warning':'FFT maximum is descriptive; not a certified eigenfrequency'}

def robot_pilot(root:Path, out:Path, cap:int, seed:int):
    import numpy as np
    d=search_robot_data(root)
    a=np.load(d/'INPUT_TRAIN.npy',mmap_mode='r',allow_pickle=False)
    y=np.load(d/'OUTPUT_TRAIN.npy',mmap_mode='r',allow_pickle=False)
    shape_ok=(a.shape==y.shape and a.ndim==2)
    size_ok=bool(shape_ok and a.shape==(9822,1500))
    shape={'input_shape':list(a.shape),'output_shape':list(y.shape),'input_dtype':str(a.dtype),'output_dtype':str(y.dtype),'paired_dimensions_valid':shape_ok,'published_dimensions_match':size_ok,'units':{'INPUT_TRAIN.npy':'m/s^2 (publisher)','OUTPUT_TRAIN.npy':'mm (publisher)'}}
    if not shape_ok: raise ValueError('Input and output must be equal 2-D arrays; got '+str(shape))
    n, length = a.shape
    time_arr,time_info=read_time(d/'time_vector.csv',length)
    meta=csv_metadata_header(d/'trajectory_metadata.csv')
    warnings=[]
    if not size_ok: warnings.append('Shape not equal to publisher (9822,1500): do NOT certify source identity.')
    if meta['rows']!=n:warnings.append('metadata row count does not match arrays')
    if time_info['status']!='PASS':warnings.append('Time axis is not PASS: frequency metrics disabled.')
    idx=[0,n//4,n//2,max(0,n-1)]
    rng=random.Random(seed)
    subsets=[list(range(min(5000,n))),list(range(min(5000,n),n))]
    each=max(1,cap//2)
    for group in subsets:
        idx.extend(rng.sample(group,min(len(group),each)) if group else [])
    idx=sorted(set(i for i in idx if 0<=i<n))
    metrics=[]; dt=time_info.get('dt_seconds') if time_info['status']=='PASS' else None
    for i in idx:
        take=min(750,length)
        xi=np.asarray(a[i,:take],dtype='float64')
        yi=np.asarray(y[i,:take],dtype='float64')
        finite=bool(np.all(np.isfinite(xi)) and np.all(np.isfinite(yi)))
        rec={'row_id_zero_based':i,'source_cohort':'STANDARD_PUBLISHER_INDEX' if i<5000 else 'OPTIMIZED_PUBLISHER_INDEX','first_750_samples':int(take),'all_finite':finite}
        if finite:
            rec.update({'acceleration_peak_m_s2':float(np.max(np.abs(xi))),'acceleration_rms_m_s2':float(np.sqrt(np.mean(xi**2))),'wall_elevation_peak_mm':float(np.max(np.abs(yi))),'wall_elevation_rms_mm':float(np.sqrt(np.mean(yi**2)))})
            rec.update({'dominant_frequency_diagnostic':diagnostic_frequency(yi,dt)})
        metrics.append(rec)
    out.mkdir(parents=True,exist_ok=True)
    with (out/'robot_metrics_sample.csv').open('w',newline='',encoding='utf-8') as f:
        names=['row_id_zero_based','source_cohort','first_750_samples','all_finite','acceleration_peak_m_s2','acceleration_rms_m_s2','wall_elevation_peak_mm','wall_elevation_rms_mm','diagnostic_frequency_hz','frequency_resolution_hz']
        writer=csv.DictWriter(f,fieldnames=names);writer.writeheader()
        for row in metrics:
            dfr=row.get('dominant_frequency_diagnostic') or {}
            writer.writerow({**{x:row.get(x) for x in names},'diagnostic_frequency_hz':dfr.get('peak_hz'),'frequency_resolution_hz':dfr.get('resolution_hz')})
    split_summary={'status':'BLOCKED_SHAPE_OR_METADATA'}
    if size_ok and meta['rows']==n:
        aidx=list(range(5000));rng=random.Random(seed);rng.shuffle(aidx)
        labels={i:('STANDARD_TRAIN' if j<3500 else 'STANDARD_VALIDATION' if j<4250 else 'STANDARD_TEST') for j,i in enumerate(aidx)}
        labels.update({i:'OPTIMIZED_OOD' for i in range(5000,n)})
        with (out/'candidate_split_NOT_BLIND.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(['row_id_zero_based','candidate_partition','note'])
            for i in range(n):w.writerow([i,labels[i],'CANDIDATE_ONLY_DO_NOT_USE_AS_CERTIFIED_BLIND_SPLIT'])
        split_summary={'status':'CANDIDATE_SPLIT_CREATED_NOT_BLIND','standard_train':3500,'standard_val':750,'standard_test':750,'optimized_ood':n-5000,'seed':seed,'group_leakage_audit':'NOT_EXECUTED'}
    # Plot paired measured data in physical units; never call it an eigenmode.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    tr=[0,min(2500,n-1),min(5000,n-1)]
    fig,axes=plt.subplots(len(tr),1,figsize=(10,8),sharex=True)
    for ax,i in zip(axes,tr):
        take=min(750,length)
        tt=time_arr[:take] if time_arr is not None else np.arange(take)
        ax.plot(tt,np.asarray(y[i,:take]),label='Measured wall elevation [mm]')
        ax.set_ylabel('Elevation [mm]')
        ax.set_title(f'Experimental paired signal, row {i} (diagnostic only)',fontsize=10)
        ax2=ax.twinx();ax2.plot(tt,np.asarray(a[i,:take]),linestyle='--',alpha=.7,label='Imposed acceleration [m/s2]');ax2.set_ylabel('Acceleration [m/s²]')
    axes[-1].set_xlabel('Time [s]' if time_arr is not None else 'Sample index [time unresolved]')
    fig.tight_layout();fig.savefig(out/'robot_paired_signals.png',dpi=150)
    with PdfPages(out/'F005_robot_pilot_report_DEVELOPMENT.pdf') as pdf:
        pdf.savefig(fig)
        cover=plt.figure(figsize=(8.27,11.69));cover.text(.07,.92,'F005 Data Pilot v0.2.0 - DEVELOPMENT',fontsize=16,weight='bold');cover.text(.07,.87,'No SST / PKLSA physical validation; data measurements were not available to the assistant.',fontsize=9);lines=[f'Robot shape: {list(a.shape)} (publisher 9822 x 1500)',f'Time gate: {time_info["status"]}',f'Metadata rows: {meta["rows"]}',f'Previewed rows: {len(idx)}',f'Candidate split: {split_summary["status"]}','Original source ZIP archives left untouched.']
        for j,line in enumerate(lines):cover.text(.07,.80-j*.045,line,fontsize=11)
        cover.text(.07,.43,'Next: metadata family leakage audit, fixed train/validation/test lock,',fontsize=10)
        cover.text(.07,.40,'then a physics baseline with out-of-sample predictions.',fontsize=10)
        cover.text(.07,.09,'Observational-only | Not framework-v1.0.7 certified.',fontsize=9)
        pdf.savefig(cover);plt.close(cover)
    plt.close(fig)
    return {'status':'ROBOT_INGESTED_DESCRIPTIVE_ONLY','robot_directory':str(d),'arrays':shape,'time':time_info,'metadata':meta,'previewed_rows':len(metrics),'split':split_summary,'warnings':warnings}

def large_single_member(root:Path,out:Path,preflight:dict|None,chosen:str)->dict:
    p=root/'sources'/'DATASET.zip'
    if not p.is_file():return {'status':'MISSING_ARCHIVE','archive':str(p)}
    if not chosen.startswith('DATASET/NoBody/') or '..' in Path(chosen).parts:
        raise ValueError('Only a single vetted NoBody member is allowed')
    with zipfile.ZipFile(p) as archive:
        if chosen not in archive.namelist():return {'status':'NO_MATCH','member':chosen}
        info=archive.getinfo(chosen)
        if info.file_size>2_000_000:raise ValueError('Selected CSV exceeds 2 MB safety cap')
        raw=archive.read(chosen) # verifies CRC; one <=2MB file only
    out.mkdir(parents=True,exist_ok=True)
    txt=raw.decode('utf-8-sig',errors='replace')
    headers=txt.splitlines()[:15]
    with (out/'NoBody_single_pressure_preview.txt').open('w',encoding='utf-8') as f:
        f.write('Original ZIP MEMBER: '+chosen+'\n')
        f.write('WARNING: Units and column semantics are NOT yet verified against acquisition metadata.\n\n')
        f.write('\n'.join(headers)+'\n')
    return {'status':'ONE_CSV_CRC_VERIFIED','member':chosen,'uncompressed_bytes':info.file_size,'compressed_bytes':info.compress_size,'crc32':hex(info.CRC),'sha256_member':hashlib.sha256(raw).hexdigest(),'preview_lines':len(headers),'units':'UNVERIFIED','source_zip_md5':'UNVERIFIED_UNLESS_OPTIONAL_HASH_REQUESTED'}

def run(root:Path,report_path:Path|None=None,out:Path|None=None,inspect_large=False,robot_only=False,verify_small=False,verify_large=False,member=DEFAULT_MEMBER, cap=128, seed=20261019):
    root=root.resolve();out=out or root/'outputs'/'f005_data_pilot_v0.2.0'
    out.mkdir(parents=True,exist_ok=True)
    pf=report_path or root/'outputs'/'data_preflight_v0.1.0'/'preflight_report.json'
    preflight=json.loads(pf.read_text(encoding='utf-8')) if pf.is_file() else None
    result={'tool':'F005_Data_Pilot_v0.2.0','date_utc':datetime.now(timezone.utc).isoformat(),'local_root':str(root),'basis':'USER_LOCAL_SOURCES','preflight_used':str(pf) if preflight else None,'scientific_status':'OBSERVATIONAL_DATA_INGEST_ONLY','source_archive_hashes':{},'checks':{}}
    for filename, expected, flag in [('sloshing_zenodo_package_v1.0.0.zip',REFERENCE['expected_robot_archive_md5'],verify_small),('DATASET.zip',REFERENCE['expected_roll_archive_md5'],verify_large)]:
        p=root/'sources'/filename
        d={'size_bytes':p.stat().st_size,'md5_status':'NOT_COMPUTED'} if p.is_file() else {'status':'SOURCE_MISSING'}
        if p.is_file() and flag:
            digest=md5_file(p); d.update({'md5_status':'PASS' if digest.lower()==expected else 'FAIL','measured_md5':digest,'expected_md5':expected})
        result['source_archive_hashes'][filename]=d
    try: result['robot']=robot_pilot(root,out,cap,seed)
    except Exception as exc:result['robot']={'status':'BLOCKED','reason':f'{type(exc).__name__}: {exc}'}
    if inspect_large and not robot_only:
        try:result['single_nobody']=large_single_member(root,out,preflight,member)
        except Exception as exc:result['single_nobody']={'status':'BLOCKED','reason':f'{type(exc).__name__}: {exc}'}
    else:result['single_nobody']={'status':'SKIPPED','reason':'Pass --inspect-large to read one small NoBody CSV directly from DATASET.zip'}
    robot=result.get('robot',{}); result['checks']={
      'P0_ARCHIVE_DIRECTORY':'PASS_FROM_USER_PREFLIGHT' if preflight and all(a.get('status')=='ZIP_CENTRAL_DIRECTORY_OK' for a in preflight.get('archives',[])) else 'UNRESOLVED',
      'P1_ARCHIVE_IDENTITY':'PASS' if all(d.get('md5_status')=='PASS' for d in result['source_archive_hashes'].values()) else 'UNRESOLVED',
      'P2_ROBOT_PAIRING':'PASS' if robot.get('arrays',{}).get('published_dimensions_match') and robot.get('metadata',{}).get('rows')==9822 else 'UNRESOLVED',
      'P3_TIME_UNITS':'PASS' if robot.get('time',{}).get('status')=='PASS' else 'UNRESOLVED',
      'P4_NOBODY_PRESSURE':'CSV_DIAGNOSTIC_ONLY' if result['single_nobody'].get('status')=='ONE_CSV_CRC_VERIFIED' else 'UNRESOLVED',
      'P5_SPLIT_LEAKAGE':'NOT_RUN',
      'P6_EULER_BASELINE':'NOT_RUN',
      'P7_PKLSA_INDEPENDENT':'NOT_RUN',
      'P8_PHYSICAL_FALSIFIER':'UNRESOLVED'
    }
    (out/'pilot_report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    md=['# F005 external wave data pilot v0.2.0','','**Status: DEVELOPMENT / OBSERVATIONAL ONLY.**','','## Data checks']
    md += [f'- `{k}`: `{v}`' for k,v in result['checks'].items()]
    md += ['', '## Robot acquisition','```json',json.dumps(robot,indent=2,ensure_ascii=False),'```','', '## NoBody archive preview','```json',json.dumps(result['single_nobody'],indent=2,ensure_ascii=False),'```','','## Scientific limits','- No Euler or PKLSA predictions have been evaluated.','- FFT maximum over a 3 s window is NOT a vortex mode or certified sloshing eigenfrequency.','- First 5000 / final 4822 groups are described by dataset publisher; metadata cross-check is required.','- Proposed split is NOT blind or scientifically certified.','- No data from user local source files were transferred to the assistant environment.','- Never mix sloshing free-surface tests with Kelvin/inertial bulk wave claims.']
    (out/'PILOT_REPORT.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path.cwd(),help='F005-v0.1.0 root, containing sources/ and outputs/')
    p.add_argument('--preflight',type=Path,default=None)
    p.add_argument('--inspect-large',action='store_true',help='Reads only one ~0.4MB CSV directly from 49.9GB ZIP (no extraction)')
    p.add_argument('--large-member',default=DEFAULT_MEMBER)
    p.add_argument('--verify-small-md5',action='store_true')
    p.add_argument('--verify-large-md5',action='store_true',help='Full sequential 49.9GB read; may take many minutes')
    p.add_argument('--sample-cap',type=int,default=128)
    a=p.parse_args()
    result=run(a.root,a.preflight,inspect_large=a.inspect_large,verify_small=a.verify_small_md5,verify_large=a.verify_large_md5,member=a.large_member,cap=max(4,min(2000,a.sample_cap)))
    print(json.dumps({'checks':result['checks'],'robot_status':result['robot'].get('status'),'single_nobody':result['single_nobody'].get('status'),'output':str(a.root/'outputs'/'f005_data_pilot_v0.2.0')},indent=2))
    return 0 if result['robot'].get('status')=='ROBOT_INGESTED_DESCRIPTIVE_ONLY' else 2

if __name__=='__main__':sys.exit(main())
