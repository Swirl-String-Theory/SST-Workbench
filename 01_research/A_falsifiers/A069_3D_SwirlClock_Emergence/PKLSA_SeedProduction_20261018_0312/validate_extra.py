from pathlib import Path
import sys, json, hashlib, subprocess, csv, re, os
import numpy as np
RUN=Path(__file__).resolve().parent
PKG=RUN/'PKLSA_KnotPlot_SeedProduction_v0.1.0'
OUT=PKG/'production_out'; LOG=RUN/'logs'
EXE=r'C:\Users\oscar\AppData\Local\Programs\KnotPlot\KnotPlot.exe'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path.insert(0,str(PKG/'src'))
from audit_legacy import components
from seedproduction import projected_crossings,tilt
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
integrity=[]
for line in (PKG/'SHA256SUMS.txt').read_text().splitlines():
    h,p=line.split(None,1);f=PKG/p.strip()
    integrity.append({'file':p,'pass':f.is_file() and sha(f)==h})
rows=list(csv.DictReader((OUT/'manifest.csv').open()))
results=[]
for r in rows:
    key=r['id'];script=OUT/(key+'__ascii_reload.kpc')
    script.write_text(f'reset all\nload checkpoints/{key}_roundtrip.txt\ninformation\ncoords checkpoints/{key}_coords_raw.txt\nsave checkpoints/{key}_ascii_reloaded.txt ascii\nquit\n')
    with script.open('rb') as inp,(LOG/(key+'__ascii_reload.log')).open('wb') as log:
        cp=subprocess.run([EXE,'-stdin','-nographics'],cwd=OUT,stdin=inp,stdout=log,stderr=subprocess.STDOUT,timeout=30)
    observed=OUT/'checkpoints'/(key+'_ascii_reloaded.txt')
    with (LOG/(key+'__ascii_compare.log')).open('wb') as log:
        cmp=subprocess.run([sys.executable,str(PKG/'src/check_knotplot_roundtrip.py'),str(OUT/r['geometry_txt']),str(observed)],stdout=log,stderr=subprocess.STDOUT)
    points=components(observed.read_text())[0]
    crossings=projected_crossings(tilt(points))
    texts=[(LOG/(key+'.log')).read_text(errors='replace'),(LOG/(key+'__ascii_reload.log')).read_text(errors='replace')]
    errors=[s for text in texts for s in text.splitlines() if re.search(r'unknown command|error|cannot|failed|warning|\*\*\*',s,re.I)]
    results.append({'id':key,'ascii_reload_exit':cp.returncode,'compare_exit':cmp.returncode,'projection_writhe':sum(c[2] for c in crossings),'crossings':len(crossings),'log_diagnostics':errors,'source_txt_sha_match':sha(OUT/r['geometry_txt'])==r['geometry_txt_sha256'],'source_kpt_sha_match':sha(OUT/r['knotplot_locd'])==r['knotplot_locd_sha256'],'example_txt_identical':sha(OUT/r['geometry_txt'])==sha(PKG/'example_release'/r['geometry_txt'])})
(RUN/'extra_validation.json').write_text(json.dumps({'package_integrity':integrity,'ascii_reload':results},indent=2))
print('integrity',sum(r['pass'] for r in integrity),'/',len(integrity),'ascii',sum(r['compare_exit']==0 for r in results),'/',len(results))
