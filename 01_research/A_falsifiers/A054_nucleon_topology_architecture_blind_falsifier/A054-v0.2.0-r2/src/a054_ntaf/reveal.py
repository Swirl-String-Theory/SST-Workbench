from __future__ import annotations
from pathlib import Path
import json,statistics
from .seal import sha256_file

METRICS=['median_rel_eq','median_cross_stabilization','median_farfield_anisotropy_r6','median_shape_drift','median_separation_curvature']
NORMS=['per_component_quantum','fixed_total_equal_split']


def _sid(m):
    p=m.get('provider_stratum')
    return None if not p else p.get('stratum_id')


def _delta(sa,sb):
    out={}
    for k in METRICS:
        a=sa.get(k); b=sb.get(k)
        out[k]=None if a is None or b is None else a-b
    for norm in NORMS:
        pa=sa.get('polarity',{}).get(norm,{}); pb=sb.get('polarity',{}).get(norm,{})
        for key in ('delta_cross_median','rel_eq_improvement_median'):
            a=pa.get(key); b=pb.get(key)
            out[f'{norm}:{key}']=None if a is None or b is None else a-b
    return out


def _envelope(rows,key='delta_A_minus_B'):
    env={}
    keys=set()
    for r in rows: keys.update((r.get(key) or {}).keys())
    for k in sorted(keys):
        vals=[r[key].get(k) for r in rows if r.get(key,{}).get(k) is not None]
        if vals:
            env[k]={'min':min(vals),'max':max(vals),'median':statistics.median(vals),
                    'sign_consistent':(min(vals)>=0 or max(vals)<=0),'n':len(vals)}
    return env


def _require_seals(campaign):
    seal=json.loads((campaign/'BLIND_SEAL.json').read_text(encoding='utf-8'))
    checks={
        'manifest_sha256':campaign/'BLIND_MANIFEST.json',
        'results_sha256':campaign/'BLIND_RESULTS.json',
        'analysis_sha256':campaign/'ANALYSIS_BLIND.json',
        'report_sha256':campaign/'REPORT_BLIND.md',
        'backend_qualification_sha256':campaign/'BACKEND_QUALIFICATION.json',
        'config_sha256':campaign/'BLIND_CONFIG.json',
    }
    for key,p in checks.items():
        if sha256_file(p)!=seal[key]: raise RuntimeError(f'blind seal mismatch: {p.name}')
    pp=campaign/'_private/PRIVATE_MAPPING.json'
    if sha256_file(pp)!=seal['private_mapping_commitment']: raise RuntimeError('private mapping commitment mismatch')
    return seal,pp


def _factor_key(m):
    return (m.get('architecture_code'),m.get('twist_bits'),_sid(m))


def _control_key(m):
    return m.get('architecture_code') if m.get('semantic_kind')=='unknot_control' else None


def _good(sa,sb):
    return sa.get('status')!='INCONCLUSIVE_NUMERICAL' and sb.get('status')!='INCONCLUSIVE_NUMERICAL'


def _skeleton_contrasts(index):
    rows=[]
    bits_vals=sorted(set(k[1] for k in index if k[1] is not None)); strata=sorted(set(k[2] for k in index if k[2] is not None))
    for bits in bits_vals:
        for st in strata:
            for A,B,name in [('G','U','G_minus_U'),('B','U','B_minus_U'),('B','G','B_minus_G')]:
                ra=index.get((A,bits,st)); rb=index.get((B,bits,st))
                if not ra or not rb: continue
                sa,sb=ra['blind_summary'],rb['blind_summary']
                rows.append({'contrast':name,'twist_bits':bits,'provider_stratum':st,
                             'status':'EVALUATED' if _good(sa,sb) else 'INCONCLUSIVE_NUMERICAL',
                             'delta_A_minus_B':_delta(sa,sb) if _good(sa,sb) else {}})
    return rows


def _twist_edge_contrasts(index):
    rows=[]
    keys=list(index)
    arches=sorted(set(k[0] for k in keys if k[1] is not None)); strata=sorted(set(k[2] for k in keys if k[2] is not None))
    for arch in arches:
        for st in strata:
            for bits_int in range(8):
                bits=f'{bits_int:03b}'
                for slot in range(3):
                    if bits[slot]!='0': continue
                    other=bits[:slot]+'1'+bits[slot+1:]
                    a=index.get((arch,other,st)); b=index.get((arch,bits,st))
                    if not a or not b: continue
                    sa,sb=a['blind_summary'],b['blind_summary']
                    rows.append({'architecture_code':arch,'provider_stratum':st,'slot':slot,
                                 'from_bits':bits,'to_bits':other,'substitution':'5_2_to_6_1',
                                 'status':'EVALUATED' if _good(sa,sb) else 'INCONCLUSIVE_NUMERICAL',
                                 'delta_6_1_minus_5_2':_delta(sa,sb) if _good(sa,sb) else {}})
    return rows


def _polarity_knot_interaction(index):
    raw=[]
    for (arch,bits,st),rec in index.items():
        if bits is None: continue
        s=rec['blind_summary']
        if s.get('status')=='INCONCLUSIVE_NUMERICAL': continue
        labels=['6_1' if b=='1' else '5_2' for b in bits]
        for norm in NORMS:
            p=s.get('polarity',{}).get(norm,{})
            deltas=p.get('delta_cross_by_slot') or []
            improves=p.get('rel_eq_improvement_by_slot') or []
            for slot in range(min(3,len(deltas))):
                raw.append({'architecture_code':arch,'provider_stratum':st,'twist_bits':bits,'normalization':norm,
                            'slot':slot,'opposed_component_knot':labels[slot],
                            'delta_cross':deltas[slot],
                            'rel_eq_improvement':improves[slot] if slot<len(improves) else None})
    grouped=[]
    for arch in sorted(set(r['architecture_code'] for r in raw)):
        for norm in NORMS:
            for knot in ('5_2','6_1'):
                vals=[r['delta_cross'] for r in raw if r['architecture_code']==arch and r['normalization']==norm and r['opposed_component_knot']==knot]
                imp=[r['rel_eq_improvement'] for r in raw if r['architecture_code']==arch and r['normalization']==norm and r['opposed_component_knot']==knot and r['rel_eq_improvement'] is not None]
                if vals:
                    grouped.append({'architecture_code':arch,'normalization':norm,'opposed_component_knot':knot,
                                    'n':len(vals),'delta_cross':{'min':min(vals),'max':max(vals),'median':statistics.median(vals)},
                                    'rel_eq_improvement':None if not imp else {'min':min(imp),'max':max(imp),'median':statistics.median(imp)}})
    return {'raw':raw,'grouped':grouped}


def _composition_aggregates(index):
    out=[]
    for arch in ('U','G','B'):
        for n61 in range(4):
            recs=[v for (a,b,st),v in index.items() if a==arch and b is not None and b.count('1')==n61 and v['blind_summary'].get('status')!='INCONCLUSIVE_NUMERICAL']
            if not recs: continue
            out.append({'architecture_code':arch,'n_5_2':3-n61,'n_6_1':n61,'n':len(recs),
                        'median_rel_eq':statistics.median(v['blind_summary']['median_rel_eq'] for v in recs),
                        'median_cross_stabilization':statistics.median(v['blind_summary']['median_cross_stabilization'] for v in recs),
                        'polarity_gate_fraction':sum(bool(v['blind_summary']['polarity']['both_normalizations_gate']) for v in recs)/len(recs)})
    return out


def reveal(campaign:Path):
    seal,pp=_require_seals(campaign)
    priv=json.loads(pp.read_text(encoding='utf-8')); ana=json.loads((campaign/'ANALYSIS_BLIND.json').read_text(encoding='utf-8'))
    revealed=[]; index={}; controls={}
    for aid,s in ana['summaries'].items():
        m=priv['mapping'][aid]
        rec={'anonymous_id':aid,**m,'blind_summary':s}; revealed.append(rec)
        if m.get('semantic_kind')=='factor_cell': index[_factor_key(m)]=rec
        else: controls[_control_key(m)]=rec

    control_contrasts=[]
    for A,B,name in [('G','U','G0_minus_U0'),('B','U','B0_minus_U0'),('B','G','B0_minus_G0')]:
        if controls.get(A) and controls.get(B):
            sa=controls[A]['blind_summary']; sb=controls[B]['blind_summary']
            control_contrasts.append({'contrast':name,'status':'EVALUATED' if _good(sa,sb) else 'INCONCLUSIVE_NUMERICAL',
                                      'delta_A_minus_B':_delta(sa,sb) if _good(sa,sb) else {}})

    skeleton_rows=_skeleton_contrasts(index)
    twist_rows=_twist_edge_contrasts(index)
    pol=_polarity_knot_interaction(index)
    out={
        'schema':'A054-REVEAL-1.1','scientific_ready':ana['scientific_ready'],'cases':revealed,
        'control_skeleton_contrasts':control_contrasts,
        'skeleton_factor_contrasts':skeleton_rows,
        'skeleton_factor_envelopes':{
            name:_envelope([r for r in skeleton_rows if r['contrast']==name and r['status']=='EVALUATED'])
            for name in ('G_minus_U','B_minus_U','B_minus_G')},
        'twist_single_site_substitution_contrasts':twist_rows,
        'twist_substitution_envelope':_envelope([
            {'delta_A_minus_B':r['delta_6_1_minus_5_2']} for r in twist_rows if r['status']=='EVALUATED']),
        'polarity_by_opposed_knot':pol,
        'composition_aggregates':_composition_aggregates(index),
        'provider_policy':'Every E011 provider anchor participates through the Cartesian anchor envelope; 6_1-sensitive conclusions remain provider-conditional unless they survive that envelope.',
        'interpretation_guard':'The full-factorial contrasts test skeleton, local twist-knot identity and circulation polarity under one filament operator. They do not fit mass, charge, or assign proton/neutron identity.',
        'blind_seal_verified':True,
    }
    (campaign/'REVEALED_RESULTS.json').write_text(json.dumps(out,indent=2),encoding='utf-8')

    lines=['# A054 v0.1.1 — REVEALED report','',
           'Blind observables and backend qualification were sealed before semantic identity attachment.','',
           '## Factorial scope','',
           '- Skeleton: unlinked / T(3,3) Triple-Gear proxy / Borromean skeleton.',
           '- Local component identity: complete binary cube of 5_2 and 6_1 assignments over three slots.',
           '- Polarity: +++ and each one-opposed sector, under two circulation normalizations.',
           '- No weighted winner score and no proton/neutron assignment.','',
           '## Skeleton envelopes','']
    for name,env in out['skeleton_factor_envelopes'].items(): lines.append(f'- **{name}**: `{env}`')
    lines += ['','## Twist substitution envelope','',f"`{out['twist_substitution_envelope']}`",'',
              '## Polarity × opposed-knot summaries','']
    for r in pol['grouped']:
        lines.append(f"- {r['architecture_code']} / {r['normalization']} / opposed {r['opposed_component_knot']}: delta-cross median={r['delta_cross']['median']:.6g} (n={r['n']})")
    lines += ['','Interpretation remains conditional on numerical qualification, provider envelopes, and the finite-core filament model.']
    (campaign/'REPORT_REVEALED.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return out
