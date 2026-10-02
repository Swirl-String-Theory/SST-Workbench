from __future__ import annotations
from collections import defaultdict


def build_independence_ledger(rows):
    """Build carrier, lineage, method and provider independence views.

    ``independence_group`` is retained for backwards compatibility. v0.2.0 additionally
    distinguishes upstream provider, construction method and lineage so a relaxation
    stage or resample variant cannot masquerade as a new independent source.
    """
    raw_seen={}; geom_seen={}; entries=[]
    groups=defaultdict(list); providers=defaultdict(list); lineages=defaultdict(list); methods=defaultdict(list)
    upstream_provider_first=set(); method_first=set(); lineage_first=set(); group_first=set()
    upstream_providers=set(); cross_methods=set()

    for row in rows:
        c=row['carrier']; raw=c.get('raw_sha256'); gh=row.get('geometry_sha256')
        dup_raw=raw_seen.get(raw) if raw else None; dup_geom=geom_seen.get(gh) if gh else None
        if raw and raw not in raw_seen: raw_seen[raw]=c['carrier_id']
        if gh and gh not in geom_seen: geom_seen[gh]=c['carrier_id']

        g=c.get('independence_group') or f"{c['source_family']}:{c['carrier_id']}"
        provider=c.get('provider_group') or c.get('source_family')
        lineage=c.get('lineage_group') or g
        method=c.get('method_group') or c.get('source_family')
        groups[g].append(c['carrier_id']); providers[provider].append(c['carrier_id']); lineages[lineage].append(c['carrier_id']); methods[method].append(c['carrier_id'])

        parent=c.get('parent_source_family'); role=c.get('source_role','')
        if dup_raw:
            evidence_class='BYTE_IDENTICAL_MIRROR_NOT_INDEPENDENT'
        elif 'mirror' in c['source_family'] or role.startswith('mirror'):
            evidence_class='MIRROR_NOT_INDEPENDENT'
        elif role.startswith('generated') or c['source_family'] in ('ptsa','ptsa_control','siaf'):
            evidence_class='GENERATED_FAMILY'
        elif parent and c['source_family'] in ('ridgerunner','katlas_braid_derived','katlas_source_derived','knot_library_derived'):
            evidence_class='DERIVED_CROSS_METHOD'
        else:
            evidence_class='UPSTREAM_REFERENCE'

        contributes_group=g not in group_first and evidence_class not in ('MIRROR_NOT_INDEPENDENT','BYTE_IDENTICAL_MIRROR_NOT_INDEPENDENT')
        contributes_provider=provider not in upstream_provider_first and evidence_class=='UPSTREAM_REFERENCE'
        contributes_lineage=lineage not in lineage_first and evidence_class not in ('MIRROR_NOT_INDEPENDENT','BYTE_IDENTICAL_MIRROR_NOT_INDEPENDENT')
        contributes_method=method not in method_first and evidence_class in ('UPSTREAM_REFERENCE','DERIVED_CROSS_METHOD')
        group_first.add(g); lineage_first.add(lineage)
        if evidence_class=='UPSTREAM_REFERENCE':
            upstream_provider_first.add(provider); upstream_providers.add(provider)
        if evidence_class in ('UPSTREAM_REFERENCE','DERIVED_CROSS_METHOD'):
            method_first.add(method); cross_methods.add(method)

        entries.append({
            'carrier_id':c['carrier_id'],'source_family':c['source_family'],'catalog_id':c.get('catalog_id'),'topology_id':c['topology_id'],
            'independence_group':g,'provider_group':provider,'lineage_group':lineage,'method_group':method,
            'parent_source_family':parent,'evidence_independence_class':evidence_class,
            'raw_duplicate_of':dup_raw,'geometry_duplicate_of':dup_geom,
            'contributes_new_independence_group':contributes_group,
            'contributes_new_upstream_provider':contributes_provider,
            'contributes_new_lineage':contributes_lineage,
            'contributes_new_method':contributes_method,
        })

    return {
        'schema':'PKLSA-SOURCE-INDEPENDENCE-2',
        'entries':entries,
        'groups':{k:v for k,v in sorted(groups.items())},
        'providers':{k:v for k,v in sorted(providers.items())},
        'lineages':{k:v for k,v in sorted(lineages.items())},
        'methods':{k:v for k,v in sorted(methods.items())},
        'independent_group_count':len(groups),
        'strict_upstream_independent_provider_count':len(upstream_providers),
        'strict_upstream_independent_group_count':len(upstream_providers),
        'upstream_plus_cross_method_count':len(cross_methods),
        'lineage_group_count':len(lineages),
        'method_group_count':len(methods),
        'carrier_count':len(entries),
        'guard':'Byte-identical mirrors never add evidence. Geometry-hash equality is reported but does not automatically collapse independently sourced curves. Generated parameter variants are not upstream measurements. Provider, method and lineage counts are reported separately.',
    }
