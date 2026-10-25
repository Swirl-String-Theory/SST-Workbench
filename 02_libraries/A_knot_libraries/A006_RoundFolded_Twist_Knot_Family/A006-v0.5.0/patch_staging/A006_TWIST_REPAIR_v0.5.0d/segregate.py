from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parent
path=ROOT/'MANIFEST.json';m=json.loads(path.read_text())
qroot=ROOT/'QUARANTINE';qroot.mkdir(exist_ok=True)
for case in m['cases']:
    if case['release_status']=='QUARANTINE_PREVIEW_ONLY':
        for key in ('file','kpt_filename'):
            fname=case[key];src=ROOT/'REPLACEMENTS'/fname;dest=qroot/fname
            if src.exists():shutil.move(str(src),str(dest))
        case['subdirectory']='QUARANTINE'
    else:
        case['subdirectory']='REPLACEMENTS'
m['static_geometry_candidates']=sum(c['subdirectory']=='REPLACEMENTS' for c in m['cases'])
m['quarantined_preview_cases']=sum(c['subdirectory']=='QUARANTINE' for c in m['cases'])
path.write_text(json.dumps(m,indent=2)+'\n')
print(m['static_geometry_candidates'],'static candidates;',m['quarantined_preview_cases'],'quarantined')
