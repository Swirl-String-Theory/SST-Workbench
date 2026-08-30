from __future__ import annotations


def evaluate_record(record: dict, policy: str='audit') -> dict:
    """Evaluate whether a prepared knot record may enter a downstream physics falsifier.

    strict: topology must be CERTIFIED, geometry qualification (if present) must pass,
            and provider_id must be present (unknown provenance is Quarantine, not strict).
    audit: MISMATCH/ERROR blocks; UNVERIFIED is allowed but explicitly marked.
    geometry-only: ignores topology for legacy compatibility (still warns if no provider_id).
    """
    p=policy.lower(); cert=record.get('topology_certification') or {}; qs=record.get('qualification')
    geo=record.get('geometry') or {}
    prov=record.get('provenance') or {}
    provider_id=geo.get('provider_id') or prov.get('provider_id')
    geo_ok=True if qs is None else bool(qs.get('pass',False)) if isinstance(qs,dict) else all(x.get('pass',False) for x in qs)
    status=cert.get('status','UNVERIFIED')
    if p=='strict': topo_ok=status=='CERTIFIED'
    elif p=='audit': topo_ok=status not in {'MISMATCH','ERROR'}
    elif p in {'geometry-only','legacy'}: topo_ok=True
    else: raise ValueError('policy must be strict, audit, or geometry-only')
    notes=[]
    if status=='UNVERIFIED': notes.append('topology is not independently certified')
    if not geo_ok: notes.append('geometry qualification failed')
    if status in {'MISMATCH','ERROR'}: notes.append(f'topology status blocks candidate: {status}')
    provider_ok=True
    if not provider_id:
        notes.append('missing provider_id (unknown provenance → Quarantine; not strict falsifier input)')
        if p=='strict':
            provider_ok=False
    return {
        'policy':p,'geometry_ok':geo_ok,'topology_ok':topo_ok,'provider_ok':provider_ok,
        'provider_id':provider_id,'topology_status':status,
        'pass':bool(geo_ok and topo_ok and provider_ok),'notes':notes,
    }
