from __future__ import annotations
from pathlib import Path
import json,statistics
from .seal import sha256_file


def _verify(c):
    s=json.loads((c/'CERT_BLIND_SEAL.json').read_text()); checks={'manifest_sha256':'BLIND_MANIFEST.json','results_sha256':'CERT_RESULTS_BLIND.json','analysis_sha256':'CERT_ANALYSIS_BLIND.json','report_sha256':'CERT_REPORT_BLIND.md','config_sha256':'CERT_CONFIG.json','backend_qualification_sha256':'BACKEND_QUALIFICATION.json'}
    for k,f in checks.items():
        if sha256_file(c/f)!=s[k]: raise RuntimeError('blind seal mismatch: '+f)
    p=c/'_private/PRIVATE_MAPPING.json'
    if sha256_file(p)!=s['private_mapping_commitment']: raise RuntimeError('private mapping commitment mismatch')
    return p


def reveal_certification(campaign:Path):
    c=Path(campaign); pp=_verify(c); priv=json.loads(pp.read_text()); res=json.loads((c/'CERT_RESULTS_BLIND.json').read_text()); ana=json.loads((c/'CERT_ANALYSIS_BLIND.json').read_text()); cfg=json.loads((c/'CERT_CONFIG.json').read_text()); fine=max(int(x) for x in cfg['n_ladder'])
    fine_by={}
    for r in res['results']:
        if r.get('N')==fine: fine_by[(r['anonymous_id'],r['sector'])]=r
    rows=[]
    for aid,m in priv['mapping'].items():
        labels=m['components']; opposed=[]; blind_secs=ana['summaries'][aid]['sectors']
        for j,q in enumerate(('Q1','Q2','Q3')):
            r=fine_by[(aid,q)]; bs=blind_secs[q]
            opposed.append({'slot':j,'knot':labels[j],'sector':q,'status':bs['status'],'spatial_converged':bs['spatial_converged'],'gates':r.get('gates',{}),
                            'normalized_growth':(r.get('spectrum') or {}).get('normalized_max_real'),'rel_eq':r.get('relative_equilibrium_residual'),
                            'ringdown_max_over_initial':(r.get('ringdown') or {}).get('max_over_initial'),'floquet_max_abs':(r.get('floquet') or {}).get('max_nontrivial_abs'),
                            'rpo_accepted':(r.get('rpo') or {}).get('accepted')})
        six=[x for x in opposed if x['knot']=='6_1']; five=[x for x in opposed if x['knot']=='5_2']
        rows.append({'anonymous_id':aid,'architecture_code':m['architecture_code'],'architecture':m['architecture'],'twist_bits':m['twist_bits'],'components':labels,'n_6_1':m['n_6_1'],'provider_stratum':m['provider_stratum'],
                     'all_same_status':blind_secs['Q0']['status'],'opposed':opposed,
                     'six1_certified_fraction':sum(x['status'].startswith('CERTIFIED_') for x in six)/max(len(six),1),
                     'five2_certified_fraction':sum(x['status'].startswith('CERTIFIED_') for x in five)/max(len(five),1)})
    contrasts=[]
    for arch in ('G','B','U'):
        rr=[r for r in rows if r['architecture_code']==arch]
        if not rr: continue
        paired_growth=[]; paired_ring=[]; cert_pref=[]; floq_pref=[]
        for r in rr:
            six=[x for x in r['opposed'] if x['knot']=='6_1']; five=[x for x in r['opposed'] if x['knot']=='5_2']
            sg=[x['normalized_growth'] for x in six if x['normalized_growth'] is not None]; fg=[x['normalized_growth'] for x in five if x['normalized_growth'] is not None]
            sr=[x['ringdown_max_over_initial'] for x in six if x['ringdown_max_over_initial'] is not None]; fr=[x['ringdown_max_over_initial'] for x in five if x['ringdown_max_over_initial'] is not None]
            if sg and fg: paired_growth.append(statistics.median(sg)-statistics.median(fg))
            if sr and fr: paired_ring.append(statistics.median(sr)-statistics.median(fr))
            if six and five:
                cert_pref.append((sum(x['status'].startswith('CERTIFIED_') for x in six)/len(six))-(sum(x['status'].startswith('CERTIFIED_') for x in five)/len(five)))
                floq_pref.append((sum(x['status']=='CERTIFIED_RPO_PROJECTED_FLOQUET_BRANCH' for x in six)/len(six))-(sum(x['status']=='CERTIFIED_RPO_PROJECTED_FLOQUET_BRANCH' for x in five)/len(five)))
        contrasts.append({'architecture_code':arch,'n_cells':len(rr),
                          'median_delta_normalized_growth_6_1_minus_5_2':None if not paired_growth else statistics.median(paired_growth),
                          'sign_6_1_lower_growth_fraction':None if not paired_growth else sum(x<0 for x in paired_growth)/len(paired_growth),
                          'median_delta_ringdown_6_1_minus_5_2':None if not paired_ring else statistics.median(paired_ring),
                          'median_certification_fraction_advantage_6_1_minus_5_2':None if not cert_pref else statistics.median(cert_pref),
                          'median_floquet_fraction_advantage_6_1_minus_5_2':None if not floq_pref else statistics.median(floq_pref)})
    out={'schema':'A054-CERT-REVEAL-2.0','blind_seal_verified':True,'fine_resolution':fine,'cases':rows,'architecture_knot_contrasts':contrasts,
         'interpretation_guard':'Certification is a finite-core filament-model result. No mass/charge fit or nucleon label is encoded in the blind runner. Projected relative Floquet is evaluated only for accepted RPOs; it is a nonlinear time-T return-map diagnostic in a preregistered physical subspace, not a proof of the full Euler spectrum.'}
    (c/'CERT_REVEALED_RESULTS.json').write_text(json.dumps(out,indent=2)+'\n')
    lines=['# A054 v0.2.0 — REVEALED certification','','Blind certification outputs were sealed before semantic attachment.','','## Architecture × opposed-knot contrasts','']
    for x in contrasts: lines.append(f"- {x['architecture_code']}: n={x['n_cells']}, median Δ normalized growth (6_1−5_2)={x['median_delta_normalized_growth_6_1_minus_5_2']}, fraction 6_1 lower-growth={x['sign_6_1_lower_growth_fraction']}, median certification advantage={x['median_certification_fraction_advantage_6_1_minus_5_2']}")
    (c/'CERT_REPORT_REVEALED.md').write_text('\n'.join(lines)+'\n'); return out
