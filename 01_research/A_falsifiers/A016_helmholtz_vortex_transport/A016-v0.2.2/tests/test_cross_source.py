from experiment.cross_source import evaluate_cross_source_consistency


def _cfg():
    return {
        'thresholds':{
            'cross_source_min_provider_groups':2,
            'cross_source_min_topologies':1,
            'cross_source_min_agreement_fraction':0.80,
        },
        'cross_source':{'gate_set':['H2','H3','P3','P4','P5','P6']},
    }


def _sample(provider,states,generated=False):
    return {
        'topology_group_id':'T0','provider_group_id':provider,'source_family_group_id':provider+'F',
        'source_generated':generated,'sample_gate_pass':states,
        'relative_equilibrium':{'normal_nrmse':0.1},
        'energy_partition_high':{'exterior_energy_fraction':0.5},
        'far_field':{'velocity_decay_exponent':3.0},
    }


def test_cross_source_pass_two_upstream_providers_agree():
    st={g:True for g in ['H2','H3','P3','P4','P5','P6']}
    samples=[_sample('A',st),_sample('B',st),_sample('GEN',{g:False for g in st},generated=True)]
    status,metrics,_=evaluate_cross_source_consistency(samples,[],_cfg())
    assert status=='PASS'
    assert metrics['n_generated_samples_excluded_from_closure']==1


def test_cross_source_fail_on_provider_disagreement():
    a={g:True for g in ['H2','H3','P3','P4','P5','P6']}
    b=dict(a); b['H3']=False
    status,metrics,_=evaluate_cross_source_consistency([_sample('A',a),_sample('B',b)],[],_cfg())
    assert status=='FAIL'
    h3=next(x for x in metrics['comparisons'][0]['gate_comparisons'] if x['gate_id']=='H3')
    assert h3['agreement_fraction']==0.5


def test_cross_source_same_provider_variants_are_not_independent():
    st={g:True for g in ['H2','H3','P3','P4','P5','P6']}
    status,metrics,_=evaluate_cross_source_consistency([_sample('A',st),_sample('A',st)],[],_cfg())
    assert status=='UNRESOLVED'
    assert metrics['n_qualified_cross_source_topologies']==0
