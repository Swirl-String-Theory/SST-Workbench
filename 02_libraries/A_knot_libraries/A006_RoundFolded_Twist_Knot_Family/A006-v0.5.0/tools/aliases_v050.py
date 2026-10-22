"""Generate collision-free geometry aliases from *existing* A006 v0.5.0 XYZ files.

Always preserves unrelated user RC aliases and never writes stale v043 filenames.
The go32 suffix uses atomic `ago 32` deliberately for reliable snapshots.
"""
from __future__ import annotations
from pathlib import Path
import re,json,sys
from orientation_v043b import orientation_key
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Input'/'original_frozen'/'knotplotrc_v044b_user.kps'
RC=ROOT/'knotplotrc.kps'
OUT=ROOT/'Output'/'v050'/'geometry'
PROFILES={'BALANCED':'B','SOFT':'S','TIGHT':'Q','FLAT':'F'}
KNOTS={'3_1':'31','4_1':'41','5_1':'51','5_2':'52','6_1':'61','7_1':'71','7_2':'72',
       '8_1':'81','9_1':'91','9_2':'92','10_1':'101','11a247':'112','11a367':'111'}

def render(strict=True):
    old=SOURCE.read_text(encoding='utf-8-sig')
    keep=[]
    for line in old.splitlines():
        m=re.match(r'^alias\s+(\S+)\s+',line,re.I)
        # Replace *all* obsolete v043 Borromean alias blocks, but preserve
        # original user aliases for unrelated operations and the original seeds.
        if m and re.match(r'^(?:556|665)[BSQF](?:256|512|1024|2048)',m.group(1)):continue
        keep.append(line)
    out=['% A006 v0.5.0 rebuilt geometry aliases -- automatically generated',
         '% GO32 suffix performs atomic ago 32; no asynchronous snapshot races.']
    names={re.match(r'^alias\s+(\S+)\s+',l,re.I).group(1).casefold() for l in keep if re.match(r'^alias\s+(\S+)\s+',l,re.I)}
    added=[];missing=[]
    def add(name,src):
        for alias in (name,name+'go32'):
            if alias.casefold() in names:raise ValueError('RC alias collision: '+alias)
            names.add(alias.casefold())
        if not src.is_file():
            missing.append(str(src.relative_to(ROOT)));return
        rel=src.relative_to(ROOT).as_posix()
        stat_file=src.with_suffix('.json')
        if not stat_file.exists():raise FileNotFoundError('Missing count metadata: '+str(stat_file))
        stat=json.loads(stat_file.read_text())
        total=sum(stat['n_actual'])
        if total<=3000:beadcmd=''
        else:
            limit=4000
            while limit<=total:limit*=2
            beadcmd=f'; go beadlimit {limit}'
        out.append(f'alias {name} "reset all; show backdrop; mode cb; load {rel}{beadcmd}"')
        out.append(f'alias {name}go32 "{name}; ago 32"')
        added.append((name,rel,total))
    for knot,short in KNOTS.items():
        for n in (256,512,1024,2048):
            for state,tail in (('ORIG',''),('MIRROR','m')):
                add(f'{short}N{n}v5{tail}',OUT/f'KNOT_{knot}_N{n:04d}_{state}.xyz')
    for lid in ('5_5_6','6_6_5'):
        short=lid.replace('_','')
        for profile,letter in PROFILES.items():
            for n in (256,512,1024,2048):
                for state,tail in (('ORIG','cc'),('MIRROR','mcc')):
                    add(f'{short}{letter}{n}{tail}',OUT/f'LINK_{lid}_{profile}_N{n:04d}_{state}_{orientation_key("FIXED61",(0,0,180))}.xyz')
    if missing and strict:raise RuntimeError(f'{len(missing)} geometry files not ready; run --prepare first; example: {missing[:3]}')
    block='% -------- BEGIN A006 V0.5.0 --------\n'+'\n'.join(out)+'\n% -------- END A006 V0.5.0 --------\n'
    original='\n'.join(keep).rstrip()+'\n'
    # User placement requirement: AFTER existing seed aliases, BEFORE trefoil.
    anchor=original.find('% Trefoil intake preset')
    if anchor==-1:raise RuntimeError('Expected trefoil section anchor missing from supplied RC')
    separator=original.rfind('% ------------------------------------------------------------',0,anchor)
    at=separator if separator>=0 else anchor
    full=original[:at]+'\n'+block+'\n'+original[at:]

    RC.write_text(full,encoding='utf8',newline='\n')
    (ROOT/'Output'/'v050'/'ALIAS_AUDIT.json').write_text(json.dumps({
      'alias_pairs':len(added),'new_aliases':2*len(added),'missing_geometry':missing,
      'all_existing_aliases_preserved_except_obsolete_556_665_blocks':True,
      'source_rc':str(SOURCE.relative_to(ROOT)),
      'validated_unique':len(names)==len(set(names)),'aliases':[x[0] for x in added]
    },indent=2)+'\n')
    print(f'RC: {len(added)} working geometry aliases, {2*len(added)} total incl. go32, missing {len(missing)}')
    return 0 if not missing else 4

if __name__=='__main__':
    try:raise SystemExit(render('--partial' not in sys.argv))
    except Exception as e:print('ALIASES FAILED:',e,file=sys.stderr);raise SystemExit(2)
