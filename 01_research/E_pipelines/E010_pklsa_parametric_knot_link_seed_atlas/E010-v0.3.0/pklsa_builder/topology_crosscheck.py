from __future__ import annotations
import re, math

def resolve_alias(label, alias_maps):
    hits=set()
    for m in alias_maps:
        for key in (label,str(label).replace('.','_')):
            vals=m.get(key,[])
            hits.update(vals if isinstance(vals,list) else [vals])
    return sorted(x for x in hits if x)

def crosscheck_carrier(carrier, qualification, alias_maps=()):
    expected=carrier.topology_id
    aliases=resolve_alias(expected,alias_maps)
    # Geometry-derived checks here are deliberately limited to facts the centerline supports
    # without pretending to be a complete knot classifier.
    levels=qualification.get('levels',[])
    finest=levels[-1] if levels else {}
    lk=finest.get('linking_matrix_entries',[])
    return {
      'carrier_id':carrier.carrier_id,
      'expected_topology':expected,
      'database_aliases':aliases,
      'component_count':len(finest.get('component_metrics',[])) if finest else None,
      'linking_matrix_entries':lk,
      'reference_database_status':'MATCHED_ALIAS' if aliases else 'NO_ALIAS_MATCH',
      'geometry_topology_certificate':'UNVERIFIED_UNLESS_EXTERNAL_PROVIDER',
      'guard':'Database/PD/invariant agreement is a reference cross-check, not a complete ambient-isotopy proof from the sampled curve.'
    }
