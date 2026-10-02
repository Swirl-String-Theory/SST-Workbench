from pathlib import Path
import csv,json,sys,numpy as np

def load(path):
    p=Path(path)/'analysis'/'blind_zero_crossings.csv'; out={}
    if not p.exists(): return out
    with p.open(newline='',encoding='utf-8') as f:
      for r in csv.DictReader(f):
        key=(r['family_blind'],r.get('replicate','0'),r['axis'],r['bracket_low'],r['bracket_high'],r['q_slice'] if r['axis']!='q' else '',r['h_slice'] if r['axis']!='h' else '',r['p_slice'] if r['axis']!='p' else ''); out[key]=float(r['root_coordinate'])
    return out

def compare(root,names,out):
    root=Path(root); maps=[load(root/n) for n in names]; common=set.intersection(*(set(m) for m in maps)) if all(maps) else set(); diffs=[]
    for k in common:
        v=[m[k] for m in maps]; scale=max(1.,max(abs(x) for x in v)); diffs.append(abs(v[-1]-v[-2])/scale)
    z={'format':'SST-QHP-RESOLUTION-1','levels':names,'n_common_crossings':len(common),'median_relative_Nhigh_minus_Nmid':float(np.median(diffs)) if diffs else None,'max_relative_Nhigh_minus_Nmid':float(np.max(diffs)) if diffs else None,'verdict':'PASS' if diffs and float(np.median(diffs))<0.02 else 'INDETERMINATE_OR_FAIL'}; Path(out).write_text(json.dumps(z,indent=2),encoding='utf-8'); print(json.dumps(z,indent=2)); return z
if __name__=='__main__': compare(sys.argv[1],sys.argv[2:5],sys.argv[5])
