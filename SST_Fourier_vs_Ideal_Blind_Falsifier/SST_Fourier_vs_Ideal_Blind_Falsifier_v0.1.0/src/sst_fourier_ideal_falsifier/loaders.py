from __future__ import annotations
from pathlib import Path
import json,re
import numpy as np

FLOAT=r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][-+]?\d+)?"

def _f(s): return float(s.replace('D','E').replace('d','e'))

def normalize_topology(s):
    x=str(s).strip().lower().replace(' ', '').replace('-', '_')
    x=re.sub(r'^(knot[._]|knot_)','',x)
    x=re.sub(r'_final$','',x)
    # VortexLab/Gilbert ideal catalog IDs encode crossing:component:index,
    # e.g. 3:1:1 -> standard knot-table 3_1 and 10:1:124 -> 10_124.
    # Only one-component records are remapped; link IDs remain distinct.
    m=re.fullmatch(r'(\d+):1:(\d+)',x)
    if m:x=f'{m.group(1)}_{m.group(2)}'
    x=x.replace('.', '_')
    x=re.sub(r'__+','_',x)
    return x

def eval_fourier(coeffs,n=512):
    th=2*np.pi*np.arange(n)/n
    x=np.zeros((n,3),float)
    for q in coeffs:
        I=int(q['I']);A=np.asarray(q['A'],float);B=np.asarray(q['B'],float)
        x += np.cos(I*th)[:,None]*A + np.sin(I*th)[:,None]*B
    return x

def parse_ideal_txt(path,n=512):
    text=Path(path).read_text(encoding='utf-8',errors='ignore');out=[]
    for m in re.finditer(r'<AB\s+([^>]*)>(.*?)</AB>',text,re.I|re.S):
        attrs=dict(re.findall(r'(\w+)="([^"]*)"',m.group(1)))
        kid=attrs.get('Id') or attrs.get('ID') or attrs.get('id') or 'unknown'; coeff=[]
        for cm in re.finditer(r'<Coeff\s+[^>]*I="\s*([0-9]+)"\s+A="([^"]+)"\s+B="([^"]+)"[^>]*/?>',m.group(2),re.I):
            A=[_f(z.strip()) for z in cm.group(2).split(',')];B=[_f(z.strip()) for z in cm.group(3).split(',')]
            if len(A)==3 and len(B)==3: coeff.append({'I':int(cm.group(1)),'A':A,'B':B})
        if coeff:
            out.append({'topology':normalize_topology(kid),'variant':'canonical','components':[eval_fourier(coeff,n)],'meta':{'loader':'ideal.txt','L':attrs.get('L'),'D':attrs.get('D')}})
    if not out:
        raise ValueError(f"No <AB>/<Coeff> records found in {path}")
    return out

def _extract_js_object(text,var):
    pats=[rf'(?:const|let|var)\s+{re.escape(var)}\s*=\s*',rf'(?:window\.)?{re.escape(var)}\s*=\s*']
    m=None
    for pat in pats:
        m=re.search(pat,text)
        if m:break
    if not m:raise ValueError(f"{var} not found")
    start=text.find('{',m.end());depth=0;ins=None;esc=False
    for i in range(start,len(text)):
        ch=text[i]
        if ins:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==ins:ins=None
        else:
            if ch in ('"',"'"):ins=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return text[start:i+1]
    raise ValueError('unclosed JS object')

def _js_object_to_json(obj):
    # Generated SST catalogs are JSON-like. Normalize the limited JS syntax they use.
    obj=re.sub(r'([,{]\s*)([A-Za-z_$][\w$]*)(\s*:)',r'\1"\2"\3',obj)
    obj=re.sub(r",\s*([}\]])",r"\1",obj)
    obj=obj.replace('undefined','null').replace('NaN','null')
    # Convert single-quoted strings conservatively when present.
    if "'" in obj and '"' not in obj[:20]:
        obj=obj.replace("'",'"')
    return obj

def parse_js_catalog(path,var,n=512):
    text=Path(path).read_text(encoding='utf-8',errors='ignore');obj=_extract_js_object(text,var)
    db=json.loads(_js_object_to_json(obj));out=[]
    for key,e in db.items():
        kid=normalize_topology(e.get('knotId',key));comps=[]
        for c in e.get('components',[]):
            coeff=c.get('coeffs',c if isinstance(c,list) else [])
            if coeff:comps.append(eval_fourier(coeff,n))
        if not comps and e.get('coeffs'):
            comps=[eval_fourier(e['coeffs'],n)]
        if comps:
            out.append({'topology':kid,'variant':str(e.get('variant','canonical')),'components':comps,'meta':{'loader':var,'sourceFile':e.get('sourceFile'),'ideal':e.get('ideal'),'harmonicStart':e.get('harmonicStart')}})
    return out

def parse_fseries(path,n=512,harmonic_start=1):
    rows=[];comments=[]
    for ln in Path(path).read_text(encoding='utf-8',errors='ignore').splitlines():
        s=ln.strip()
        if not s:continue
        vals=re.findall(FLOAT,s)
        if len(vals)==6 and re.fullmatch(rf'\s*{FLOAT}\s+{FLOAT}\s+{FLOAT}\s+{FLOAT}\s+{FLOAT}\s+{FLOAT}\s*',s):
            rows.append([_f(v) for v in vals])
        elif s.startswith('%') or s.startswith('#'):
            comments.append(s)
    if not rows:raise ValueError(f"no six-column Fourier rows: {path}")
    coeff=[]
    for j,r in enumerate(rows):
        ax,bx,ay,by,az,bz=r
        coeff.append({'I':j+harmonic_start,'A':[ax,ay,az],'B':[bx,by,bz]})
    parent=normalize_topology(Path(path).parent.name)
    stem=Path(path).stem.lower().replace('knot.','')
    variant='canonical' if normalize_topology(stem)==parent else normalize_topology(stem)
    return {'topology':parent,'variant':variant,'components':[eval_fourier(coeff,n)],'meta':{'loader':'raw-fseries','harmonicStart':harmonic_start,'comments':comments[:8]}}

def parse_xyz(path):
    groups=[];cur=[]
    for ln in Path(path).read_text(encoding='utf-8',errors='ignore').splitlines():
        s=ln.strip()
        if not s:
            if len(cur)>=4:groups.append(np.asarray(cur,float));cur=[]
            continue
        vals=re.findall(FLOAT,s)
        if len(vals)>=3:
            try:cur.append([_f(vals[0]),_f(vals[1]),_f(vals[2])])
            except ValueError:pass
    if len(cur)>=4:groups.append(np.asarray(cur,float))
    if not groups:raise ValueError(f"no XYZ triples: {path}")
    return groups

TORUS_COORD_TOPOLOGY={
    'torus_2_3':'3_1','torus_2_5':'5_1','torus_2_7':'7_1','torus_2_9':'9_1',
    'torus_3_4':'8_19','torus_3_5':'10_124'
}

def topology_from_relaxed_filename(path):
    s=normalize_topology(Path(path).stem)
    return TORUS_COORD_TOPOLOGY.get(s,s)
