from __future__ import annotations
from collections import defaultdict
from statistics import median
from math import isfinite


def _num(x):
    try:
        v=float(x)
        return v if isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _mad(values, med):
    return median([abs(v-med) for v in values]) if values else None


def metric_value(seed: dict, metric: str):
    base='Wr' if metric=='Wr_abs' else metric
    status=str((seed.get('observable_status') or {}).get(base,'')).upper()
    value=_num((seed.get('finest_metrics') or {}).get(base))
    if status!='RESOLVED' or value is None:
        return None
    return abs(value) if metric=='Wr_abs' else value


def band_for(metric: str, policy: dict) -> dict:
    bands=policy['provider_agreement']['bands']
    return bands.get(metric, bands['default'])


def _summary(vals: list[float]):
    med=median(vals); lo=min(vals); hi=max(vals); denom=max(abs(med),1e-15)
    return {'n':len(vals),'median':med,'mad':_mad(vals,med),'min':lo,'max':hi,'absolute_span':hi-lo,'relative_span':(hi-lo)/denom,'relative_half_span':0.5*(hi-lo)/denom}


def provider_agreement_rows(topology_id: str, primary_seeds: list[dict], policy: dict) -> list[dict]:
    """Agreement is between provider medians, while within-provider spread is retained.

    This prevents a provider with dozens of historical/final variants from receiving dozens
    of votes against a provider that contributes one reference geometry.
    """
    grouped=defaultdict(list)
    for seed in primary_seeds:
        provider=str(seed.get('provider_group') or '')
        if provider: grouped[provider].append(seed)
    out=[]
    for metric in policy['provider_agreement']['metrics']:
        provider_stats={}; provider_medians=[]; all_values=[]
        for provider,seeds in sorted(grouped.items()):
            vals=[v for v in (metric_value(s,metric) for s in seeds) if v is not None]
            if not vals: continue
            st=_summary(vals); provider_stats[provider]=st; provider_medians.append(st['median']); all_values.extend(vals)
        if not all_values:
            out.append({'topology_id':topology_id,'metric':metric,'provider_count':0,'seed_count':0,'status':'NOT_TESTABLE_NO_RESOLVED_VALUES','provider_summaries':{}})
            continue
        empirical=_summary(all_values)
        row={
          'topology_id':topology_id,'metric':metric,'provider_count':len(provider_stats),'seed_count':len(all_values),
          'provider_groups':list(provider_stats),'provider_summaries':provider_stats,
          'empirical_min':empirical['min'],'empirical_max':empirical['max'],'empirical_median':empirical['median'],
          'empirical_mad':empirical['mad'],'empirical_relative_span':empirical['relative_span'],
        }
        if len(provider_medians)<2:
            row.update({'between_provider_median':provider_medians[0] if provider_medians else None,'between_provider_relative_span':None,'status':'SINGLE_PROVIDER_ONLY'})
        else:
            cross=_summary(provider_medians); rel=cross['relative_span']; b=band_for(metric,policy)
            if rel<=b['strong_max_relative_span']: status='AGREEMENT_STRONG'
            elif rel<=b['acceptable_max_relative_span']: status='AGREEMENT_ACCEPTABLE'
            elif rel<=b['weak_max_relative_span']: status='AGREEMENT_WEAK'
            else: status='PROVIDER_SENSITIVE'
            row.update({
              'between_provider_median':cross['median'],'between_provider_mad':cross['mad'],
              'between_provider_min':cross['min'],'between_provider_max':cross['max'],
              'between_provider_absolute_span':cross['absolute_span'],'between_provider_relative_span':rel,
              'between_provider_relative_half_span':cross['relative_half_span'],'status':status,**b,
            })
        out.append(row)
    return out


def topology_agreement_status(primary_seeds: list[dict], rows: list[dict], policy: dict) -> tuple[str,list[str]]:
    providers={str(s.get('provider_group')) for s in primary_seeds if s.get('provider_group')}
    if not providers: return 'STATIC_NOT_READY_NO_UPSTREAM_REFERENCE',[]
    if len(providers)==1: return 'SINGLE_PROVIDER_QUALIFIED',[]
    by={r['metric']:r for r in rows}; reasons=[]; incomplete=False; sensitive=False
    for metric in policy['provider_agreement']['required_for_cross_provider_robust']:
        r=by.get(metric)
        if not r or int(r.get('provider_count') or 0)<2 or r.get('between_provider_relative_span') is None:
            incomplete=True; reasons.append(f'{metric}:<2_resolved_providers'); continue
        max_ok=band_for(metric,policy)['acceptable_max_relative_span']; rel=float(r['between_provider_relative_span'])
        if rel>max_ok:
            sensitive=True; reasons.append(f'{metric}:between_provider_relative_span={rel:.6g}>{max_ok:.6g}')
    if incomplete: return 'CROSS_PROVIDER_INCOMPLETE',reasons
    if sensitive: return 'CROSS_PROVIDER_SENSITIVE',reasons
    return 'CROSS_PROVIDER_ROBUST',[]
