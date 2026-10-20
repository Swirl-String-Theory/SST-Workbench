from pathlib import Path
import json,csv,hashlib,sys,subprocess,platform,os,zipfile
import numpy as np
R=Path(__file__).resolve().parent; P=R/'PKLSA_KnotPlot_SeedProduction_v0.1.0'; O=P/'production_out'
extra=json.loads((R/'extra_validation.json').read_text()); env=json.loads((R/'environment.json').read_text()); keep=json.loads((R/'preservation.json').read_text())
doctor=json.loads((R/'logs/pklsa_doctor.log').read_text(encoding='utf-8-sig'))
rows=list(csv.DictReader((O/'manifest.csv').open()))
sample=[]
for row in rows:
    a=np.loadtxt(O/row['geometry_txt']); b=np.loadtxt(P/'example_release'/row['geometry_txt'])
    sample.append({'id':row['id'],'max_abs_difference':float(np.max(np.abs(a-b)))})
(R/'sample_comparison.json').write_text(json.dumps(sample,indent=2))
dump=(R/'logs/runtime_probe.log').read_text(); params=dump[dump.index('PanicAllow ='):dump.rindex('KnotPlot>')]
(R/'runtime_parameters.txt').write_text(params)
cal={'knotplot_version':'1.022 build 5125W x86_64','host':platform.node(),'close':0.12,'max_dr':0.1,'parameters_dump_sha256':hashlib.sha256((R/'runtime_parameters.txt').read_bytes()).hexdigest(),'executable_sha256':env['knotplot_sha256'],'qualification':'PARAMETER_DUMP_ONLY_NO_PREP_OR_DYNAMICS'}
(R/'runtime_calibration.json').write_text(json.dumps(cal,indent=2))
cp=subprocess.run([sys.executable,str(P/'src/make_knotplot_campaign.py'),str(O),'--runtime',str(R/'runtime_calibration.json')],capture_output=True,text=True)
(R/'logs/calibrated_script_generation.log').write_text(cp.stdout+cp.stderr+f'\nEXIT_CODE={cp.returncode}\n')
gates=[]
def gate(id,status,detail): gates.append(dict(id=id,status=status,detail=detail))
gate('PACKAGE_INTEGRITY','PASS','59/59 bundled SHA256 entries match; original ZIP retained.')
gate('REGRESSION','PASS','5 unittest tests passed, exit 0.')
gate('S0_GENERATED_PROVENANCE','PASS','Two frozen formulas, 16 manifest rows with source/mirror/provider lineage and SHA256. One shared notebook provider group, not 16 providers.')
gate('S0_ORIGINAL_NOTEBOOK_AUTHENTICITY','UNRESOLVED','Original notebook page images/bytes are not included; historical formula transcription authenticity not independently verified.')
gate('S1_STATIC_GEOMETRY','PASS','16/16 STATIC_QA_PASS: finite closed single components, edge QA; dimensionless.')
gate('S2_MIRROR_PROJECTION','PASS','16/16 three-crossing signed projection regressions, including after actual ASCII reload; not an isotopy proof.')
gate('S3_RESOLUTION_LADDER','PASS','N=128,256,512,1024 generated for A/B and exact z mirrors. This is geometric consistency, not solver convergence.')
gate('S4_INSTALLED_KNOTPLOT','PASS','16/16 LOCD loads and ASCII reloads; coordinate comparator exit 0 at rtol=atol=1e-12; one component and matching bead counts. No command-error diagnostics in checked import logs.')
gate('RAW_COORDS_COMPARATOR','FAIL','Packaged comparator rejects KnotPlot coords output header Component 0:. coords is six-decimal output; save ... ascii supplies high precision. Supplied KPC overwrites its coords file with ASCII save; separate local wrappers preserve both formats. Original failure log retained.')
gate('LEGACY_AUDITOR_AS_SHIPPED','FAIL','All 49 files initially UNPARSEABLE because raw.decode uses unknown encoding utf8-sig. Exit 0 does not imply valid inventory. Original results retained.')
fixed=list(csv.DictReader((R/'legacy_quarantine_inventory_codec_fixed.csv').open()))
gate('LEGACY_AUDIT_CODEC_FIXED','PASS' if all(x['status']=='QUARANTINE_HISTORICAL_ONLY' for x in fixed) else 'FAIL',f"Separate companion copy changes encoding spelling only to utf-8-sig; {len(fixed)} raw files inventoried; {sum(x['status']=='UNPARSEABLE' for x in fixed)} unparseable. No historical file changed or promoted.")
gate('PKLSA_EXISTING_INSTALLATION','FAIL','E010 v0.3.1 source facade executes doctor via explicit PYTHONPATH; main venv has no installed sst_pklsa. Doctor exit 0 but coverage.pass=false: 10/11 required sources resolved; pipeline.ptsa_e009 missing. No repair/import attempted.')
gate('S5_RUNTIME_AND_RELAXATION','UNRESOLVED','Actual reset parameter dump collected: close=0.12, max-dr=0.10; executable SHA recorded. Preparation scripts generated only; no prep, fitto, go-1 or dynamics executed. Full safety/calibration and independent seeds remain unqualified.')
gate('S6_INDEPENDENT_TOPOLOGY','UNRESOLVED','No independent Alexander/link-isotopy certificate executed; projection regression alone is insufficient.')
gate('S7_FINITE_CORE','UNRESOLVED','No finite-core tube, nonlocal clearance/reach or core-to-mesh qualification.')
gate('S8_PHYSICAL_DYNAMICS','UNRESOLVED','No Euler/pressure-Poisson, space/time/core/backend convergence or phase qualification; static seeds only.')
gate('E010_PRESERVATION','PASS',f"{keep['E010_files_hashed']} existing E010 v0.3.1 files hashed before/after with no differences (excludes venv/build/cache).")
gate('GLOBAL_RESEARCH_SNAPSHOT','UNRESOLVED',f"Metadata snapshot covered {keep['metadata_files_checked']} files in 01_research and 03_data. {len(keep['research_data_metadata_changes'])} changes all under concurrent A068 execution_20261018_home; no writes by this run targeted that tree. No repo-wide byte hash claim.")
report={'role':'STATIC_GEOMETRY_ONLY','physical_certification':'NONE','environment':env,'gates':gates,'sample_comparison_max_abs':max(x['max_abs_difference'] for x in sample),'legacy_files':len(fixed)}
(R/'GATE_LEDGER.json').write_text(json.dumps(report,indent=2))
lines=['# PKLSA KnotPlot Seed Production v0.1.0 — lokaal uitvoeringsverslag','', 'Uitgevoerd op 18 oktober 2026 op de thuis-pc, binnen SST-Workbench. Alle geometrieën zijn uitsluitend dimensieloze statische seeds; geen fysisch gevalideerde vortexoplossingen.','',f"Python {sys.version.split()[0]}, NumPy {np.__version__}; KnotPlot 1.022 build 5125W. ZIP SHA256: `{env['package_sha256']}`.",'', '## Gates','']
for g in gates:lines.extend([f"- **{g['status']} — {g['id']}**: {g['detail']}",''])
lines.extend(['## Uitvoer en reproduceerbaarheid','', '- `PKLSA_KnotPlot_SeedProduction_v0.1.0/production_out/`: 16 XYZ, 16 LOCD, manifest, candidate metadata, import/checkpoint exports and generated preparation scripts.','- `commands.json`, `logs/`, `extra_validation.json`: commands, exit codes, runtime logs and import evidence.','- `runtime_calibration.json`, `runtime_parameters.txt`, `environment.json`: actual executable/parameter provenance.','- `legacy_quarantine_inventory.csv`: original failed audit; `legacy_quarantine_inventory_codec_fixed.csv`: separate corrected audit.','- `preservation.json`, `E010_hashes_before.json`, `protected_metadata_before.json`: preservation evidence.','',f"Generated sample versus bundled example: largest absolute coordinate difference {report['sample_comparison_max_abs']:.17g}. Byte identity across platform/NumPy builds is not asserted; original sample and new files retained.",'', '## Begrenzing','', 'Geen E010-import, registrywijziging, frozen-falsifier run, relaxatiecampagne, commit of push uitgevoerd. Het originele pakket blijft ongewijzigd; companion scripts en alle nieuwe outputs staan uitsluitend in deze deliverables-map. S5–S8 en authenticatie van de oorspronkelijke notebookpagina’s vereisen afzonderlijk werk. De bestaande PTSA-bronresolutie moet worden hersteld voordat PKLSA-brede volledigheid kan worden geclaimd.'])
(R/'EXECUTION_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
files=sorted(p for p in R.rglob('*') if p.is_file() and p.name!='OUTPUT_SHA256SUMS.txt')
(R/'OUTPUT_SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(R)).replace('\\','/')+'\n' for p in files))
archive=R.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in R.rglob('*'):
        if p.is_file():z.write(p,str(p.relative_to(R)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'gates':{s:sum(g['status']==s for g in gates) for s in ['PASS','FAIL','UNRESOLVED']},'archive':str(archive),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'sample_difference':report['sample_comparison_max_abs']},indent=2))
