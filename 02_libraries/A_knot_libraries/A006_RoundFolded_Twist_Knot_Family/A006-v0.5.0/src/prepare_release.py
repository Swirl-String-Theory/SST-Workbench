from pathlib import Path
import json,shutil
root=Path(__file__).resolve().parents[1]
(root/'CONTROL_NOT_FOR_INSTALL').mkdir(exist_ok=True)
for folder in ['SEEDS','QUARANTINE']:
 for f in list((root/folder).glob('KNOT_6_1_*')):
  target=root/'CONTROL_NOT_FOR_INSTALL'/f.name
  if target.exists():target.unlink()
  shutil.move(str(f),str(target))
fn=root/'MANIFEST.json';m=json.loads(fn.read_text())
controls=[r for r in m['results']+m['quarantine'] if r['name']=='6_1']
m['results']=[r for r in m['results'] if r['name']!='6_1']
m['quarantine']=[r for r in m['quarantine'] if r['name']!='6_1']
m['controls']={'6_1':controls,'5_2':'Original user TikZ reference retained but not exported: non-generic crossing projection with repeated P3/P10.'}
m['status']='GEOMETRY_STATIC_CANDIDATES_NO_LAB_RUNTIME'
fn.write_text(json.dumps(m,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
print('replacement candidates',len(m['results']),'quarantine',len(m['quarantine']),'6_1 control',len(controls))
