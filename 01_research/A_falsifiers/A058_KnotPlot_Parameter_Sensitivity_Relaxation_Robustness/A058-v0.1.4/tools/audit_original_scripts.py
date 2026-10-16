from pathlib import Path
import argparse,collections,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]

def audit(root=ROOT):
    src=root/'inputs'/'original_scripts'
    files=sorted(src.glob('*.kpc'))
    values=collections.defaultdict(collections.Counter)
    records=[]
    explicit_ascii=0
    for p in files:
        t=p.read_text(encoding='utf-8',errors='replace')
        kind='knot' if p.name.startswith('build_knot_') else 'link' if p.name.startswith('build_link_') else 'torus'
        rec={'file':p.name,'kind':kind,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        lm=re.search(r'^\s*load\s+(\S+)',t,re.M)
        tm=re.search(r'^\s*torus\s+(\d+)\s+(\d+)\s+(\d+)',t,re.M)
        nm=re.search(r'^\s*refine nbeads\s+(\d+)',t,re.M)
        rec['source']=lm.group(1) if lm else (f'torus({tm.group(1)},{tm.group(2)})' if tm else None)
        rec['nbeads']=int(nm.group(1)) if nm else (int(tm.group(3)) if tm else None)
        rec['ago1000_count']=len(re.findall(r'^\s*ago\s+1000\s*$',t,re.M))
        saves=re.findall(r'^\s*save\s+(.+)$',t,re.M)
        rec['save_count']=len(saves)
        rec['explicit_ascii_save']=bool(saves) and all(re.search(r'\s+(ascii|raw)\s*$',s,re.I) for s in saves)
        explicit_ascii += int(rec['explicit_ascii_save'])
        for key in ['close','max-dr','mechforce','elecforce','bendforce','bencon','stusplit','dstep','bradius','cradius']:
            m=re.search(rf'^\s*{re.escape(key)}\s*=\s*([^\s%]+)',t,re.M)
            if m: values[key][m.group(1)]+=1
        em=re.search(r'^\s*energy model\s+(\S+)',t,re.M)
        if em: values['energy_model'][em.group(1)]+=1
        records.append(rec)
    dyn_cmds=['charge','hooke','power','timeincr']
    dyn_counts={cmd:sum(bool(re.search(rf'^\s*{cmd}\s+[^\s%]+',p.read_text(encoding='utf-8',errors='replace'),re.M)) for p in files) for cmd in dyn_cmds}
    out={
      'schema':'A058-ORIGINAL-SCRIPT-AUDIT-1','file_count':len(files),
      'kind_counts':dict(collections.Counter(r['kind'] for r in records)),
      'parameter_values':{k:dict(v) for k,v in values.items()},
      'checkpoint_count_distribution':dict(collections.Counter(str(r['ago1000_count']) for r in records)),
      'explicit_ascii_save_files':explicit_ascii,
      'explicit_ascii_save_all': bool(files) and explicit_ascii==len(files),
      'implicit_sformat_dependency': bool(files) and explicit_ascii!=len(files),
      'explicit_dynamic_command_counts':dyn_counts,
      'runtime_default_dependency':any(v<len(files) for v in dyn_counts.values()),
      'records':records
    }
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='build/original_script_audit.json'); a=ap.parse_args()
    out=audit(); p=ROOT/a.out; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ['file_count','kind_counts','parameter_values','explicit_ascii_save_all','implicit_sformat_dependency']},indent=2))
if __name__=='__main__': main()
