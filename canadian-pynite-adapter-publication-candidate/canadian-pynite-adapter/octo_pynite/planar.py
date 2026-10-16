"""Reduced Euler-Bernoulli beam submodels using only verified EI.
Inactive axial, torsional and out-of-plane DOFs are restrained everywhere.
Unit dummy properties in those inactive channels are numerical placeholders,
never physical material or section declarations and never used for design.
"""
import math
from .adapter import run,num,InputError

def to_frame(beam):
    L=num(beam['length_m'],'length_m',True);EI=num(beam['EI_kNm2'],'EI_kNm2',True)
    if not beam.get('source_ref') or not beam.get('idealization_status'):raise InputError('Planar beam source and idealization status required')
    supports=beam.get('supports',[])
    if not supports:raise InputError('Explicit beam supports required')
    stations={0.,L};support_map={}
    for s in supports:
        x=num(s['x_m'],'support x_m')
        if not 0<=x<=L:raise InputError('Support outside beam')
        if type(s.get('vertical_fixed')) is not bool or type(s.get('rotation_fixed')) is not bool:raise InputError('Explicit vertical/rotation restraint booleans required')
        if x in support_map:raise InputError('Duplicate support station')
        support_map[x]=s;stations.add(x)
    xs=sorted(stations);bid=beam['id'];nodes=[];members=[]
    for i,x in enumerate(xs):
        s=support_map.get(x,{});nodes.append({'id':f'{bid}:N{i}','xyz':[x,0,0],'supports':[True,s.get('vertical_fixed',False),True,True,True,s.get('rotation_fixed',False)]})
    for i in range(len(xs)-1):members.append({'id':f'{bid}:S{i}','i':nodes[i]['id'],'j':nodes[i+1]['id'],'material':'REDUCED_EB','section':'REDUCED_EB','rotation_deg':0,'releases':[False]*12})
    loads=[]
    for load in beam.get('loads',[]):
        kind=load['type'];case=load['case'];lid=load['id']
        if kind=='distributed':
            a=num(load['x1_m'],'load start');b=num(load['x2_m'],'load end')
            if not 0<=a<b<=L:raise InputError('Distributed interval invalid')
            q1=num(load['w1_kNm'],'w1');q2=num(load['w2_kNm'],'w2')
            for i,(x,y) in enumerate(zip(xs,xs[1:])):
                aa=max(a,x);bb=min(b,y)
                if bb<=aa:continue
                qa=q1+(q2-q1)*(aa-a)/(b-a);qb=q1+(q2-q1)*(bb-a)/(b-a)
                loads.append({'id':f'{lid}:S{i}','type':'member_distributed','target':members[i]['id'],'case':case,'direction':'Fy','w1':qa,'w2':qb,'x1':aa-x,'x2':bb-x})
        elif kind in ('point','moment'):
            x=num(load['x_m'],'point x');value=num(load['value'],'point value')
            if not 0<=x<=L:raise InputError('Point outside beam')
            match=next((i for i,xx in enumerate(xs) if abs(xx-x)<1e-10),None)
            if match is not None:loads.append({'id':lid,'type':'node','target':nodes[match]['id'],'case':case,'direction':'FY' if kind=='point' else 'MZ','value':value})
            else:
                i=next(i for i,(a,b) in enumerate(zip(xs,xs[1:])) if a<x<b)
                loads.append({'id':lid,'type':'member_point','target':members[i]['id'],'case':case,'direction':'Fy' if kind=='point' else 'Mz','value':value,'x':x-xs[i]})
        else:raise InputError('Unsupported reduced beam load type')
    sw=beam.get('self_weight')
    if not isinstance(sw,dict) or sw.get('mode')!='included_in_loads' or not sw.get('source_ref'):raise InputError('Reduced EI model needs explicit self-weight included-in-loads basis; no physical density inferred')
    return {'analysis':'first_order_linear','units':{'length':'m','force':'kN','stress':'kN/m2'},'nodes':nodes,'members':members,'materials':[{'id':'REDUCED_EB','E':EI,'G':1.,'nu':0.,'weight_density':0.}], 'sections':[{'id':'REDUCED_EB','A':1.,'Iy':1.,'Iz':1.,'J':1.}], 'load_cases':beam['load_cases'],'combinations':beam['combinations'],'loads':loads,'self_weight':sw,'canonical_coverage':{'source_member_id':bid,'mode':'REDUCED_PLANAR_EULER_BERNOULLI','source_ref':beam['source_ref'],'idealization_status':beam['idealization_status'],'EI_kNm2':EI,'inactive_channel_properties':'NUMERICAL_PLACEHOLDERS_NOT_PHYSICAL; all inactive DOFs restrained','physical_design_properties_imported':False}}

def run_beam(beam):
    frame=to_frame(beam);result=run(frame)
    result['scope']='Reduced planar EI beam response only. Numerical placeholders in fully restrained inactive channels are not physical properties. No whole-building continuity or code resistance acceptance.'
    return {'source_member_id':beam['id'],'input':frame,'result':result}

