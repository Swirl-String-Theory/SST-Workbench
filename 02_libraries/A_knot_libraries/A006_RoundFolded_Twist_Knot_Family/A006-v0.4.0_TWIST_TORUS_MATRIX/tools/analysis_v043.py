#!/usr/bin/env python3
"""A006 v0.4.3 runtime metric and mirror symmetry analysis.
Uses *only* DONE+native.csv, never fabricates unrun values.
"""
import argparse,csv,json,math,sys
from collections import defaultdict
from pathlib import Path

FIELDS=('iteration','nbeads','length','rog','safe')

def csv_out(p,fields,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def run(root):
 root=Path(root);base=root/'output'/'selection_v043';out=base/'analysis';out.mkdir(parents=True,exist_ok=True)
 matrix=[];errors=[]
 for d in sorted((base/'runs').glob('*/*')):
  if not d.is_dir():continue
  p=d/'DONE.json';native=d/'native.csv'
  if not p.exists():continue
  try:
   m=json.loads(p.read_text())
   if m.get('status')!='RUNTIME_CHECKPOINTS_COMPLETE':raise ValueError('NOT_RUNTIME_COMPLETE')
   with native.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f)
    if [s.strip() for s in reader.fieldnames]!=list(FIELDS):raise ValueError('Unexpected native header')
    values=[{k:float(v) for k,v in row.items()} for row in reader]
   if len(values)!=len(m['checkpoints']) or [int(x['iteration']) for x in values]!=m['checkpoints']:
    raise ValueError('Incomplete native checkpoint sequence')
   if any(not all(math.isfinite(v) for v in x.values()) for x in values):raise ValueError('Nonfinite metric')
   for entry in values:
    matrix.append({'kind':m['kind'],'name':m['label'],'profile':m['profile'],
                   'N':m['resolution'],'orientation':m['orientation'],'tanf':m['tanf'],
                   'iteration':int(entry['iteration']),'nbeads':entry['nbeads'],
                   'length':entry['length'],'rog':entry['rog'],'safe':entry['safe'],
                   'run':str(d.relative_to(root))})
  except Exception as ex:errors.append({'run':str(d.relative_to(root)),'error':str(ex)})
 matrix.sort(key=lambda x:(x['kind'],x['name'],x['profile'],x['N'],x['tanf'],x['orientation'],x['iteration']))
 cols=('kind','name','profile','N','orientation','tanf','iteration','nbeads','length','rog','safe','run')
 csv_out(out/'metrics_long.csv',cols,matrix)
 groups=defaultdict(dict)
 for row in matrix:
  key=(row['kind'],row['name'],row['profile'],row['N'],row['tanf'],row['iteration'])
  groups[key][row['orientation']]=row
 sym=[]
 for key,group in sorted(groups.items()):
  if not {'ORIG','MIRROR'}<=group.keys():continue
  a,b=group['ORIG'],group['MIRROR']
  stat={'kind':key[0],'name':key[1],'profile':key[2],'N':key[3],'tanf':key[4],
        'iteration':key[5], 'topological_achirality_proven':'UNRESOLVED',
        'physical_Euler_parity':'NOT_TESTED'}
  for metric in ('length','rog','safe'):
   stat[f'{metric}_original']=a[metric];stat[f'{metric}_mirror']=b[metric]
   stat[f'{metric}_rel_diff']=abs(b[metric]-a[metric])/max(abs(a[metric]),abs(b[metric]),1.e-12)
  sym.append(stat)
 columns=list(sym[0]) if sym else ('kind','name','profile','N','tanf','iteration','length_original','length_mirror','length_rel_diff','rog_original','rog_mirror','rog_rel_diff','safe_original','safe_mirror','safe_rel_diff','topological_achirality_proven','physical_Euler_parity')
 csv_out(out/'mirror_comparison.csv',columns,sym)
 # Compare N to 2*N for otherwise identical experimental arms and checkpoint clocks.
 binned=defaultdict(dict)
 for x in matrix:binned[(x['kind'],x['name'],x['profile'],x['orientation'],x['tanf'],x['iteration'])][x['N']]=x
 conv=[]
 for key,by_n in sorted(binned.items()):
  for n in sorted(by_n):
   if 2*n not in by_n:continue
   a,b=by_n[n],by_n[2*n]
   conv.append({'kind':key[0],'name':key[1],'profile':key[2], 'orientation':key[3],
                'tanf':key[4],'iteration':key[5],'N_lower':n,'N_upper':2*n,
                'length_rel_diff':abs(a['length']-b['length'])/max(abs(a['length']),abs(b['length']),1.e-12),
                'rog_rel_diff':abs(a['rog']-b['rog'])/max(abs(a['rog']),abs(b['rog']),1.e-12)})
 csv_out(out/'resolution_comparison.csv', ('kind','name','profile','orientation','tanf','iteration','N_lower','N_upper','length_rel_diff','rog_rel_diff'), conv)
 charts=[]
 if sym:
  try:
   import matplotlib
   matplotlib.use('Agg')
   import matplotlib.pyplot as plt
   # One plot per metric, selected valid mirror pairs only, max 16 representative traces.
   for metric in ('length','rog','safe'):
    fig,ax=plt.subplots(figsize=(10,5))
    grouped=defaultdict(list)
    for s in sym:
     label=f"{s['name']} {s['profile']} N{s['N']} TANF={s['tanf']}"
     grouped[label].append(s)
    for label,items in list(sorted(grouped.items()))[:16]:
     items.sort(key=lambda x:x['iteration'])
     ax.plot([i['iteration'] for i in items],[i[f'{metric}_rel_diff'] for i in items],label=label)
    ax.set(xlabel='KnotPlot atomic ago iteration',ylabel=f'{metric} mirror relative difference',
           title='Mirror parity sensitivity — KnotPlot relaxation only')
    ax.grid(alpha=.2)
    if len(grouped)<=16:ax.legend(fontsize=7)
    fig.tight_layout();dest=out/f'{metric}_mirror_difference.png';fig.savefig(dest,dpi=130);plt.close(fig)
    charts.append(dest.name)
  except ImportError:errors.append({'type':'plotting','error':'matplotlib not installed; CSV preserved'})
 audit={'status':'RUNTIME_DATA_PRESENT' if matrix else 'NO_KNOTPLOT_RUNTIME_DATA',
        'metric_rows':len(matrix),'mirror_pair_rows':len(sym),'resolution_pair_rows':len(conv),
        'plots':charts,'errors':errors,
        'claim':'KnotPlot MD only; neither parity data nor visual mirror similarity certify isotopy/amphichirality or Euler dynamics'}
 (out/'AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf8')
 print(json.dumps(audit,indent=2))
 return 1 if errors and any(x.get('type')!='plotting' for x in errors) else 0

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);args=p.parse_args()
 sys.exit(run(args.root))
