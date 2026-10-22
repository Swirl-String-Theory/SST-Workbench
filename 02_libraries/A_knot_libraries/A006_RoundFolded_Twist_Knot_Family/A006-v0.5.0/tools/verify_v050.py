"""Read-only audited release checks for v0.5.0. No KnotPlot/runtime is claimed."""
from pathlib import Path
import sys,hashlib,json,re,collections,numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from selection_v050 import components_from_xyz,required_beadlimit,checkpoints
from geometry_v050 import KNOTS,metrics
G=ROOT/'Output/v050/geometry'
def run():
    rows=[];fail=[]
    for p in sorted(G.glob('*.xyz')):
        d=json.loads(p.with_suffix('.json').read_text())
        try:
            if p.name.startswith('LINK_'):
                parts=components_from_xyz(p)
                if d['orientation'].get('policy')!='FIXED61':raise AssertionError('New link must use default FIXED61')
                expected=[180. if x=='6_1' else 0. for x in d['component_knots']]
                if d['orientation']['angles_deg']!=expected:raise AssertionError('Wrong 6_1 default rotation')
                if '_CPFIXED61.' not in p.name:raise AssertionError('Old closure policy filename')
                if p.read_text().count('\n\n')!=2:raise AssertionError('Requires precisely two component separators')
                if len(parts)!=3:raise AssertionError('3 components required')
            else:
                parts=[np.loadtxt(p)];assert len(parts[0])==d['n_actual'][0]
            stats=[metrics(x) for x in parts]
            if [len(x) for x in parts]!=d['n_actual']:raise AssertionError('Bead count mismatch')
            if any(x['closing_edge_over_median']<.18 or x['closing_edge_over_median']>1.6 for x in stats):
                raise AssertionError('Grossly nonuniform seam length')
            h=hashlib.sha256(p.read_bytes()).hexdigest()
            if h!=d['sha256']:raise AssertionError('SHA mismatch')
            rows.append({'name':p.stem,'status':d['status'],'N_actual':d['n_actual'],'sha256':h})
        except Exception as e:fail.append(f'{p.name}: {e}')
    rc=(ROOT/'knotplotrc.kps').read_text()
    aliases=re.findall(r'^alias\s+(\S+)\s+',rc,re.M)
    if len(aliases)!=len(set(x.lower() for x in aliases)):fail.append('Duplicate RC alias name')
    targets=re.findall(r'load\s+(Output/v050/geometry/\S+?\.xyz)',rc)
    if len(targets)!=168 or not all((ROOT/x).exists() for x in targets):fail.append('Stale/missing new RC geometry targets')
    camps=list((ROOT/'Output/v050/runs').glob('*/*/campaign.kpc'))
    if len(camps)!=336:fail.append(f'Expected 336 new campaigns got {len(camps)}')
    for script in camps:
        lines=script.read_text().splitlines()
        mm=[x for x in lines if x.startswith('load ')]
        if len(mm)!=1:fail.append(f'{script}: ambiguous geometry load');continue
        source=ROOT/mm[0][5:]
        d=json.loads(source.with_suffix('.json').read_text())
        total=sum(d['n_actual']);req=required_beadlimit(d['n_actual'])
        if req is not None:
            if f'go beadlimit {req}' not in lines or lines.index(f'go beadlimit {req}')<lines.index(mm[0]):
                fail.append(f'{script}: missing/misplaced beadlimit')
        if 'ago' not in script.read_text():fail.append(f'{script}: missing atomic iterations')
        if not any('A006_CHECKPOINT_0008000' in x for x in lines):fail.append(f'{script}: not an 8000 campaign')
    status=collections.Counter(x['status'] for x in rows)
    audit={'version':'0.5.0a','geometry_files':len(rows),'geometry_statuses':dict(status),'aliases':len(aliases),
      'new_alias_geometry_targets':len(targets),'campaign_scripts':len(camps),
      'failed_checks':fail,'runtime':'NOT_EXECUTED',
      'geometry_morphology':'SHARP_TURN_WARNING candidates must not be represented as relaxed/certified',
      'topological_isotopy':'UNRESOLVED','Milnor_triple':'UNRESOLVED','Euler':'NOT_RUN'}
    (ROOT/'Output/v050/RELEASE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))
    return 0 if not fail and len(rows)==168 else 4
if __name__=='__main__':raise SystemExit(run())
