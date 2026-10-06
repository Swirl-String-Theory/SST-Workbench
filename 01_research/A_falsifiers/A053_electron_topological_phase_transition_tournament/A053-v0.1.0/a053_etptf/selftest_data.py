from __future__ import annotations
import math

def _base(h, cid, resolution, source='S1', sham=False, sector='fixed_total_equal_split_same_sign'):
    t=[i/100 for i in range(101)]
    if h in {'H0','H3'}: comp=[1]*101; lk=[0.0]*101
    else: comp=[2]*101; lk=[1.0]*101
    return {'case_id':cid,'hypothesis':h,'source_group':source,'resolution':resolution,'circulation_sector':sector,'sham':sham,'time':t,'component_count':comp,'abs_linking':lk,'energy':[1.0+1e-4*math.sin(2*math.pi*x) for x in t],'helicity':[1.0+2e-4*math.cos(2*math.pi*x) for x in t],'interaction_mask':[1 if .30<x<=.55 else 0 for x in t],'reconnection_events':[]}

def instrument_manifest():
    cases=[]
    for res in [64,96]:
      for src in ['S1','S2']:
        h0=_base('H0',f'H0-{res}-{src}',res,src); cases.append(h0)
        h1=_base('H1',f'H1-{res}-{src}',res,src)
        h1['phase12']=[(35*x if x<.55 else 0.2+0.02*math.sin(20*x)) for x in h1['time']]
        h1['phase_weight']=[1.0]*101; cases.append(h1)
        h2=_base('H2',f'H2-{res}-{src}',res,src)
        for i,x in enumerate(h2['time']):
            if x>=.42: h2['abs_linking'][i]=2.0
        h2['reconnection_events']=[{'time':.42,'rule_id':'LOCAL_TEST_RULE','local_separation':.08}]; cases.append(h2)
        sh=_base('H2',f'H2-sham-{res}-{src}',res,src,sham=True); cases.append(sh)
        h3=_base('H3',f'H3-{res}-{src}',res,src)
        for i,x in enumerate(h3['time']):
            if .40<=x<=.62: h3['component_count'][i]=2; h3['abs_linking'][i]=1.0
        h3['reconnection_events']=[{'time':.40,'rule_id':'LOCAL_TEST_RULE','local_separation':.08},{'time':.62,'rule_id':'LOCAL_TEST_RULE','local_separation':.08}]; cases.append(h3)
        sh3=_base('H3',f'H3-sham-{res}-{src}',res,src,sham=True); cases.append(sh3)
    return {'schema':'A053-PRODUCER-v1','blind':True,'producer':{'name':'A053 deterministic evaluator selftest','version':'0.1.0','physics_class':'finite_core_reconnection','target_aware_reconnection':False,'instrument_only':True},'cases':cases}
