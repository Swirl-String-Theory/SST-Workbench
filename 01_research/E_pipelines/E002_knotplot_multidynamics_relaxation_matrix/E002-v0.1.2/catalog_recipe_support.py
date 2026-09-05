from __future__ import annotations
import json, hashlib, re
from pathlib import Path
DYNAMIC_LINE=re.compile(r"^\s*(?:collision\s+\S+|close\s*=.*|max-dr\s*=.*|mechforce\s*=.*|elecforce\s*=.*|bendforce\s*=.*|charge\s+.*|hooke\s+.*|power\s+.*|timeincr\s+.*|bencon\s*=.*|stusplit\s*=.*|dstep\s*=.*|bradius\s*=.*|cradius\s*=.*|energy\s+model\s+.*)\s*$",re.I)
def load_recipe(path:Path,allow_provisional=False):
    d=json.loads(path.read_text(encoding='utf-8'))
    if not d.get('approved_for_catalog') and not allow_provisional:
        raise ValueError(f"recipe {path.name} is not approved_for_catalog")
    p=d['parameters']; required={'collision','close','max_dr','mechforce','elecforce','bendforce','charge','hooke','power','timeincr','bencon','stusplit','dstep','bradius','cradius','energy_model'}
    miss=sorted(required-set(p));
    if miss: raise ValueError(f'missing recipe parameters: {miss}')
    return d
def recipe_hash(d):
    return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def block(d):
    p=d['parameters']; h=recipe_hash(d)
    on=lambda x:'on' if x else 'off'
    return [f"% RECIPE_ID {d['recipe_id']}",f"% RECIPE_SHA256 {h}","collision "+str(p['collision']),f"close = {p['close']}",f"max-dr = {p['max_dr']}",f"mechforce = {on(p['mechforce'])}",f"elecforce = {on(p['elecforce'])}",f"bendforce = {on(p['bendforce'])}",f"charge {p['charge']}",f"hooke {p['hooke']}",f"power {p['power']}",f"timeincr {p['timeincr']}",f"bencon = {p['bencon']}",f"stusplit = {p['stusplit']}",f"dstep = {p['dstep']}",f"bradius = {p['bradius']}",f"cradius = {p['cradius']}",f"energy model {p['energy_model']}"]
def inject(text,d):
    lines=text.splitlines(); clean=[ln for ln in lines if not DYNAMIC_LINE.match(ln) and not ln.startswith('% RECIPE_')]
    idx=next((i+1 for i,ln in enumerate(clean) if re.match(r'^\s*fitto\s+mindist\b',ln,re.I)),None)
    if idx is None: idx=next((i+1 for i,ln in enumerate(clean) if re.match(r'^\s*centre\s*$',ln,re.I)),None)
    if idx is None: raise ValueError('cannot find recipe insertion point')
    b=['']+block(d)+['']; return '\n'.join(clean[:idx]+b+clean[idx:])+'\n'
