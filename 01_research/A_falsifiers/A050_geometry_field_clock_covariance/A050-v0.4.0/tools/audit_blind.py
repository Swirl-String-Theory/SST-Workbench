from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1]
patterns=[r'alpha',r'circlearrow',r'circulation',r'rho_core',r'rho_f',r'f_swirl',r'f_gr',r'1\.09384563',r'1\.40897017',r'3\.8934358',r'7\.0e-7',r'trefoil',r'3_1',r'knotplot',r'gilbert',r'pklsa']
fixed=[r'target_mode[^\n]{0,32}[:=][^\n]{0,8}3\b',r'fixed_mode[^\n]{0,32}[:=][^\n]{0,8}3\b',r'mode_target[^\n]{0,32}[:=][^\n]{0,8}3\b']
hits=[]
for base in [ROOT/'sst_gfcc_blind',ROOT/'config']:
    for p in base.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in ('.py','.json','.txt'): continue
        if p.name.startswith('SEAL_'): continue
        s=p.read_text(encoding='utf-8',errors='ignore')
        for pat in patterns+fixed:
            if re.search(pat,s,re.I): hits.append((str(p.relative_to(ROOT)),pat))
print(json.dumps({'hits':hits,'count':len(hits)},indent=2)); raise SystemExit(1 if hits else 0)
