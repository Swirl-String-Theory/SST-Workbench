"""A058-v0.3.2: auditable, additive KnotPlot-distribution inspection.

NO mutation of v0.2.9 scientific source, v0.3.0 clone or private blind files.
The user supplies the original distribution ZIP; no KnotPlot code is bundled.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,subprocess,sys,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.kpf_readonly import decode_kpf,metrics,KPFMalformed,KPFUnsupported
from tools.geometry_safety import assess
from tools.shortcut_runtime import resolve_launcher,native_probe_script

SCHEMA='A058-DISTRIBUTION-AUDIT-v0.3.2'
SOURCES={
 'dynamics_help':'demos/Dyna_help.txt',
 'newtonian_velocity_demo':'demos/relax2.kps',
 'alternative_mech_drag_demo':'demos/FreeDrag.kps',
 'benchmark_dstep_1':'benchmarks/relaxA-bm.kps',
 'benchmark_dstep_4':'benchmarks/relaxB-bm.kps',
 'lua_dynamics':'resource/Lua/Dynamics.lua',
 'native_kpf_reader':'resource/src/simple-reader-writer/kpf_io.cpp',
 'native_kpf_reader_header':'resource/src/simple-reader-writer/kpf_io.h',
 'native_kpf_scope':'resource/src/simple-reader-writer/README.txt',
}
SELECTED_KPF=['basic/0_1','basic/3.1','basic/4.1','basic/8.19','basic/6.3.3']
GUI={
 'elec':{'shown':'ON','class':'bead-pair repulsion','policy':'DAMPED_CORE'},
 'charge':{'shown':15.0,'class':'electrical strength','policy':'SWEEP_WITH_ELEC_ON'},
 'power':{'shown':5.0,'class':'electrical distance exponent','policy':'SWEEP_WITH_ELEC_ON'},
 'mech':{'shown':'ON','class':'neighbor attraction','policy':'DAMPED_CORE'},
 'hooke':{'shown':1.0,'class':'mechanical strength','policy':'SWEEP_WITH_MECH_ON'},
 'amech':{'shown':'OFF','class':'alternative spring mechanics','policy':'SEPARATE_EXPLICIT_ON_MODE'},
 'spring':{'shown':1.4,'class':'alternative-mech rest length','policy':'ONLY_WITH_AMECH_ON'},
 'afmpower':{'shown':2.0,'class':'alternative-mech exponent','policy':'ONLY_WITH_AMECH_ON'},
 'max-dr':{'shown':0.1,'class':'max bead displacement','policy':'NUMERICAL_SAFETY_CONTROL'},
 'close':{'shown':0.12,'class':'collision/exclusion distance','policy':'REQUIRE_NO_CROSSING_CHECK'},
 'tinc':{'shown':15.0,'class':'GUI time increment','policy':'CLI_ALIAS_UNVERIFIED'},
 'tanf':{'shown':'ON','class':'tangential force','policy':'EXCLUDED_KNOWN_IMPLEMENTATION_BUG'},
 'tanmag':{'shown':9.0,'class':'tangential magnitude','policy':'EXCLUDED_KNOWN_IMPLEMENTATION_BUG'},
 'velfo':{'shown':None,'class':'velocity-proportional force','policy':'EXCLUDED_FROM_DAMPED_CORE_UNDAMPED_ONLY'},
 'dstep':{'shown':None,'class':'display cadence','policy':'NEGATIVE_CONTROL'},
 'No Collide':{'shown':None,'class':'prevents self-crossings','policy':'COLLISION_FAST_PLUS_INDEPENDENT_3D_CHECK'},
}


def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def savejson(p:Path,v):
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')

def folder_new(out:Path):
 if out.exists():raise FileExistsError(f'Fail-closed: audit directory already exists: {out}')
 out.mkdir(parents=True)

def required_source(z):
 names=z.namelist()
 candidate_roots={n.split('/')[0] for n in names if n.endswith('demos/Dyna_help.txt')}
 if len(candidate_roots)!=1:raise ValueError('Distribution root ambiguous or Dyna_help.txt missing')
 root=next(iter(candidate_roots))
 return root+'/'

def rel_text(z,root,rel):return z.read(root+rel).decode('utf-8',errors='replace')
def matched_lines(s,pattern):
 return [i for i,line in enumerate(s.splitlines(),1) if re.search(pattern,line,re.I)]

def distribution_report(dist:Path):
 with zipfile.ZipFile(dist,'r') as z:
  root=required_source(z)
  evidence={}
  for label,path in SOURCES.items():
   data=z.read(root+path)
   evidence[label]={'archive_path':root+path,'sha256':sha(data),'bytes':len(data)}
  helptext=rel_text(z,root,SOURCES['dynamics_help']).lower()
  demo2=rel_text(z,root,SOURCES['newtonian_velocity_demo'])
  freedrag=rel_text(z,root,SOURCES['alternative_mech_drag_demo'])
  a=rel_text(z,root,SOURCES['benchmark_dstep_1'])
  b=rel_text(z,root,SOURCES['benchmark_dstep_4'])
  lua=rel_text(z,root,SOURCES['lua_dynamics'])
  kpf=rel_text(z,root,SOURCES['native_kpf_reader'])
  tests={
   'help_documents_tanf_bug':('implementation bug' in helptext),
   'help_documents_velocity_force':('proportional to velocity' in helptext),
   'help_documents_damped_inertia':('do not retain any inertia' in helptext),
   'demo_velfo_cli_alias_velforce':bool(re.search(r'(?m)^\s*velforce\s*=\s*true',demo2)),
   'demo_velocity_force_uses_newtonian_mode':bool(re.search(r'(?m)^\s*force\s+1\b',demo2)),
   'demo_velocity_force_disables_collision':bool(re.search(r'(?m)^\s*collision\s+allow\b',demo2)),
   'demo_amech_on':bool(re.search(r'(?m)^\s*amech\s*=\s*on',freedrag)),
   'demo_spring_control':bool(re.search(r'(?m)^\s*spring\s*=',freedrag)),
   'demo_drag_control':bool(re.search(r'(?m)^\s*drag\s*=\s*on',freedrag)),
   'benchmark_dstep_1':bool(re.search(r'(?m)^\s*dstep\s*=\s*1\b',a)),
   'benchmark_dstep_4':bool(re.search(r'(?m)^\s*dstep\s*=\s*4\b',b)),
   'benchmarks_both_collision_allow':all(bool(re.search(r'(?m)^\s*coll\s+a\b',s)) for s in (a,b)),
   'lua_speed_uses_coordinates_and_elapsed_time':('coords cofm' in lua and 'timeKP () - T0' in lua),
   'source_reader_supports_LOCS_LOCF_LOCD_LOCC':all(f'"{x}"' in kpf for x in ('LOCS','LOCF','LOCD','LOCC')),
   'reader_scope_restricted_to_single_component':('single component' in rel_text(z,root,SOURCES['native_kpf_scope']).lower()),
  }
  evidence['script_line_references']={
   'relax2_force_1':matched_lines(demo2,r'force\s+1'),
   'relax2_collision_allow':matched_lines(demo2,r'collision\s+allow'),
   'relax2_velforce':matched_lines(demo2,r'velforce'),
   'FreeDrag_amech':matched_lines(freedrag,r'amech\s*='),
   'benchmark_A_dstep':matched_lines(a,r'dstep\s*='),
   'benchmark_B_dstep':matched_lines(b,r'dstep\s*='),
  }
  return {'schema':SCHEMA,'distribution_file':dist.name,'distribution_sha256':sha_file(dist),
      'files_in_archive':len(z.namelist()),'dist_root':root,
      'source_evidence':evidence,'static_tests':tests,'static_tests_pass':all(tests.values()),
      'source_version':'kpdist-23mar2025 (Linux distribution of build 5093)',
      'native_2026_binary_test':'NOT_RUN','claims_limited_to':'documentation/scripts/file format, NOT actual force solver',
      'old_blind_271_condition_protocol':'UNMODIFIED'}

def kpf_report(dist:Path):
 with zipfile.ZipFile(dist,'r') as z:
  root=required_source(z)
  rows=[]
  for catalog in SELECTED_KPF:
   blob=z.read(root+catalog)
   rec={'catalog':catalog,'archive_path':root+catalog,'sha256':sha(blob),'bytes':len(blob)}
   try:
    parsed=decode_kpf(blob)
    snapshot=assess(parsed.points)
    rec.update({'status':'PARSED_SINGLE_CLOSED_COMPONENT','encoding':parsed.encoding,**metrics(parsed.points),
        'min_nonadjacent_segment_distance_native_units':snapshot['minimum_distance'],
        'snapshot_centerline_safety':snapshot['status'],'continuous_time_topology_guarantee':False})
   except KPFUnsupported as e:
    rec.update({'status':'UNSUPPORTED_LINK_OR_ENCODING','reason':str(e)})
   except KPFMalformed as e:
    rec.update({'status':'INVALID_OR_TRUNCATED','reason':str(e)})
   rows.append(rec)
 return {'schema':'A058-KPF-INDEPENDENT-AUDIT-1','distribution_sha256':sha_file(dist),'catalog_samples':rows,
         'topological_knot_identification':'NOT_PERFORMED','SI_LENGTH_CALIBRATION':'NOT_PERFORMED',
         'link_import_certification':'NOT_PERFORMED','source_blind_state':'UNTOUCHED'}

def write_csv(p:Path,rows):
 cols=sorted({k for r in rows for k in r})
 with p.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)

def do_audit(dist:Path,out:Path,mode:str):
 if not dist.is_file():raise FileNotFoundError(f'Missing distribution ZIP: {dist}')
 folder_new(out)
 if mode in ('DIST_AUDIT','AUDIT_ALL'):
  d=distribution_report(dist)
  savejson(out/'SOURCE_EVIDENCE.json',d)
  savejson(out/'GUI_CONTROL_MATRIX.json',{'schema':'A058-GUI-CONTROL-MATRIX-1','observed_2026_screenshots_not_verified_reset_defaults':True,'controls':GUI,'S0_S7_private_mapping':'REDACTED_NOT_REMAPPED'})
  write_csv(out/'GUI_CONTROL_MATRIX.csv',[{'control':n,'observed_value':str(r['shown']),'class':r['class'],
     'registered_policy':r['policy'],'runtime_getter_2026':'NOT_VERIFIED','experiment_effect':'NOT_MEASURED_IN_THIS_AUDIT'}
     for n,r in GUI.items()])
  write_csv(out/'PARAMETER_EFFECT_MATRIX_TEMPLATE.csv',[{'control':n,'experiment_status':'NOT_RUN',
     'effect_type':'UNMEASURED','requested_value':'','observed_getter':'',
     'knotplot_executable_sha256':'','seed_sha256':'','iterations':'','dynamics_mode':'',
     'collision_mode':'','KPF_or_XYZ_sha256':'','length_native_units':'','rg_native_units':'',
     'edge_cv':'','shape_distance':'','min_nonadjacent_segment_distance':'',
     'KnotPlot_safe_response':'','topology_signature':'','discrepancy_comment':''}
     for n in GUI])
 if mode in ('KPF_AUDIT','AUDIT_ALL'):
  k=kpf_report(dist);savejson(out/'KPF_AUDIT.json',k);write_csv(out/'KPF_AUDIT.csv',k['catalog_samples'])
 savejson(out/'RUN_RECEIPT.json',{'mode':mode,'source_distribution_sha256':sha_file(dist),
       'original_A058_source_or_outputs_changed':False,'native_experiment':'NOT_RUN',
       'scope':'OFFLINE_STATIC_AND_BINARY_FILE_PARSING_ONLY'})
 return out

BASE_SCRIPT=['reset all','collision fast','load A058_seed.kpf','elec = on','mech = on','amech = off',
             'velforce = off','tanf = off','grav = off','therm = off']
def safe_probe_script(dstep:int):
 lines=BASE_SCRIPT+[f'dstep = {dstep}','echo A058_SAFE_START','safe','echo A058_SAFE_START_END',
      'go 32','echo A058_SAFE_FINAL','safe','echo A058_SAFE_FINAL_END','length','rog','alex -1',
      'data open A058_native_metrics.csv','data format "/N,/l,/g,/D,/I"','data header','data','data close',
      'save A058_final.txt ascii']
 return '\n'.join(lines)+'\n'

def generate_probes(dist:Path,out:Path):
 if not dist.is_file():raise FileNotFoundError(dist)
 folder_new(out)
 with zipfile.ZipFile(dist) as z:
  root=required_source(z)
  seed=z.read(root+'basic/3.1')
  parsed=decode_kpf(seed)
  if len(parsed.points)<3:raise RuntimeError('seed lacks valid geometry')
 for value in (1,4):
  sub=out/f'dstep_{value}';sub.mkdir()
  (sub/'A058_seed.kpf').write_bytes(seed)
  script=safe_probe_script(value)
  (sub/'probe.kpc').write_text(script,encoding='utf-8',newline='\n')
 savejson(out/'PROBES.json',{'schema':'A058-SAFE-NATIVE-PROBES-1','distribution_sha256':sha_file(dist),
  'seed_sha256':sha(seed),'seed_beads':len(parsed.points),'collision_policy':'collision fast',
  'force_exclusions':['velforce = off','tanf = off','grav = off','therm = off'],
  'dstep_values':[1,4],'equal_solver_steps':32,'native_execution':'NOT_RUN',
  'warning':'Requires an actual 2026 KnotPlot executable; preserves raw PRIVATE stdout. Do not infer no crossing between steps.',
  'benchmark_origin':'2025 relaxA/B differ by dstep but had unsafe collision allow; sanitized scripts are new control probes'})
 return out

def _read_xyz(path:Path):
 pts=[]
 for ln in path.read_text(errors='replace').splitlines():
  ss=ln.strip().split()
  if len(ss)!=3:continue
  try: xyz=tuple(map(float,ss))
  except ValueError:continue
  if not all(math.isfinite(x) for x in xyz):raise ValueError('Non-finite XYZ')
  pts.append(xyz)
 if len(pts)<3:raise ValueError('No plain 3-column exported xyz found')
 return pts

def run_safe_probes(exe:Path,out:Path,timeout:int,workdir:Path|None=None):
 if timeout<=0:raise ValueError('Timeout must be positive')
 launcher=resolve_launcher(exe,workdir_override=workdir)
 if not (out/'PROBES.json').is_file():raise FileNotFoundError('Generate probes first')
 if (out/'NATIVE_RESULTS.json').exists():raise FileExistsError('Results already present; use a new probe directory')
 if (out/'NATIVE_LAUNCH_PRIVATE.json').exists():raise FileExistsError('Previous launch metadata; use a new probe directory')
 receipt=json.loads((out/'PROBES.json').read_text())
 plan=[]
 # Preflight both probes before executing either: no silent re-use/overwrite.
 for val in receipt['dstep_values']:
  wd=out/f'dstep_{val}'
  script=wd/'probe.kpc'
  runtime=wd/'probe.native.kpc'
  log=wd/'NATIVE_STDOUT_PRIVATE.log'
  if any(p.exists() for p in (runtime,log,wd/'A058_native_metrics.csv',wd/'A058_final.txt')):
   raise FileExistsError(f'Previous native probe evidence present in {wd}; use a new directory')
  if sha((wd/'A058_seed.kpf').read_bytes()) != receipt['seed_sha256']:
   raise RuntimeError('Protected seed was modified')
  plan.append((val,wd,script,runtime,log,native_probe_script(script.read_text(encoding='utf-8'),wd)))
 savejson(out/'NATIVE_LAUNCH_PRIVATE.json',{
  'original_input_launcher':str(exe),
  'resolved_executable':str(launcher.executable),
  'executable_sha256':sha_file(launcher.executable),
  'shortcut_path':str(launcher.shortcut) if launcher.shortcut else None,
  'shortcut_sha256':sha_file(launcher.shortcut) if launcher.shortcut else None,
  'startup_workdir':str(launcher.workdir),'startup_workdir_source':launcher.workdir_source,
  'shortcut_arguments':launcher.shortcut_args,
  'output_policy':'ABSOLUTE_PATHS_IN_A058_PROBE_DIR',
  'runtime_files':['probe.native.kpc','NATIVE_STDOUT_PRIVATE.log','A058_final.txt','A058_native_metrics.csv']})
 results=[]
 for val,wd,script,runtime,log,script_text in plan:
  runtime.write_text(script_text,encoding='utf-8',newline='\n')
  try:
   with runtime.open('rb') as inp,log.open('wb') as lf:
    # Native process starts in the Shortcut's Start-in directory; all A058 IO is absolute.
    p=subprocess.run(launcher.command(),cwd=launcher.workdir,
                     executable=str(launcher.executable),stdin=inp,stdout=lf,
                     stderr=subprocess.STDOUT,timeout=timeout,check=False)
   rc=p.returncode;timed_out=False
  except subprocess.TimeoutExpired:
   rc=None;timed_out=True
  text=log.read_text(errors='replace')
  errors=[e for e in ('unknown command','freeglut error:','nothing to save','not safe') if e in text.lower()]
  export=wd/'A058_final.txt'; met=wd/'A058_native_metrics.csv'
  obs={'dstep':val,'returncode':rc,'timeout':timed_out,'error_tokens':errors,
       'private_log_sha256':sha_file(log),'private_log_relative':str(log.relative_to(out)),
       'runtime_script_sha256':sha_file(runtime),
       'source_probe_sha256':sha_file(script),
       'workdir_policy':launcher.workdir_source,
       'export_exists':export.exists(),'metrics_csv_exists':met.exists()}
  if rc==0 and not errors and export.exists() and met.exists():
   try:
    pts=_read_xyz(export)
    obs.update({'status':'OBSERVED_NATIVE_SCRIPT_SUCCESS_NOT_PHYSICS_CERTIFIED',
         'coordinate_sha256':sha_file(export),'metrics':metrics(pts)})
   except (ValueError,OSError) as e:
    obs.update({'status':'UNQUALIFIED_EXPORT','error_class':type(e).__name__})
  else:
   obs['status']='UNSUPPORTED_OR_FAILED_NATIVE_RUNTIME'
  results.append(obs)
 valid=all(v['status']=='OBSERVED_NATIVE_SCRIPT_SUCCESS_NOT_PHYSICS_CERTIFIED' for v in results)
 neg={'status':'UNRESOLVED','comparison':'dstep 1 versus 4 at matched 32 iterations'}
 if valid:
  p1=_read_xyz(out/'dstep_1/A058_final.txt');p4=_read_xyz(out/'dstep_4/A058_final.txt')
  if len(p1)==len(p4):
   rms=math.sqrt(sum(math.dist(a,b)**2 for a,b in zip(p1,p4))/len(p1))
   scale=max(results[0]['metrics']['length_native_units']/len(p1),1e-12)
   neg={'status':'WITHIN_DISPLAY_CONTROL_TOLERANCE' if rms/scale<=1e-8 else 'DIFFERENCE_DETECTED',
        'rms_native_units':rms,'relative_to_mean_edge':rms/scale,'tolerance':1e-8,
        'caveat':'Geometry equality at one budget is NOT evidence of physical convergence or topology preservation'}
 doc={'schema':'A058-NATIVE-PROBE-RESULT-1','exe_sha256':sha_file(launcher.executable),
      'shortcut_used':launcher.shortcut is not None,
      'launch_evidence_private_sha256':sha_file(out/'NATIVE_LAUNCH_PRIVATE.json'),
      'native_execution':'ATTEMPTED','conditions':results,'dstep_negative_control':neg,
      'old_271_condition_gate_ledger':'UNTOUCHED','no_collider_certification':'NOT_ESTABLISHED',
      'physical_interpretation':'NOT_ESTABLISHED'}
 savejson(out/'NATIVE_RESULTS.json',doc)
 return doc

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('mode',choices=['DIST_AUDIT','KPF_AUDIT','AUDIT_ALL','GENERATE_PROBES','RUN_SAFE_PROBES'])
 ap.add_argument('--dist',type=Path)
 ap.add_argument('--out',type=Path,required=True)
 ap.add_argument('--exe',type=Path)
 ap.add_argument('--workdir',type=Path,help='Absolute override for shortcut Start-in if ambiguous')
 ap.add_argument('--timeout',type=int,default=120)
 a=ap.parse_args()
 if a.mode!='RUN_SAFE_PROBES' and not a.dist:ap.error('--dist is required')
 if a.mode=='RUN_SAFE_PROBES' and not a.exe:ap.error('--exe is required')
 try:
  if a.mode in ('DIST_AUDIT','KPF_AUDIT','AUDIT_ALL'):
   do_audit(a.dist,a.out,a.mode)
  elif a.mode=='GENERATE_PROBES':generate_probes(a.dist,a.out)
  else:run_safe_probes(a.exe,a.out,a.timeout,a.workdir)
  print('A058',a.mode,'COMPLETE: outputs at',a.out,flush=True)
 except Exception as e:
  print('A058',a.mode,'FAIL-CLOSED:',type(e).__name__,str(e),file=sys.stderr)
  return 2
 return 0
if __name__=='__main__':raise SystemExit(main())
