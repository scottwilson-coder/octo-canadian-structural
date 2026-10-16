"""Explicit, first-order 3D frame adapter. kN, m, kN/m²; no inferred connectivity."""
import copy, hashlib, json, math
from importlib.metadata import version
from Pynite import FEModel3D
from .extrema import deflection_extrema

class InputError(ValueError): pass

def num(v, name, positive=False):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or (positive and v<=0):
        raise InputError(name+' must be a finite '+('positive ' if positive else '')+'number')
    return float(v)

def unique(rows, name):
    result={}
    for row in rows:
        key=row.get('id')
        if not isinstance(key,str) or not key or key in result: raise InputError('Missing/duplicate '+name+' ID')
        result[key]=row
    if not result: raise InputError('No '+name)
    return result

def validate(data):
    if data.get('units')!={'length':'m','force':'kN','stress':'kN/m2'}: raise InputError('Explicit m/kN/kN/m2 units required')
    if data.get('analysis')!='first_order_linear': raise InputError('Only first_order_linear is implemented; no silently ignored nonlinear requests')
    nodes=unique(data['nodes'],'nodes'); members=unique(data['members'],'members')
    mats=unique(data['materials'],'materials'); sections=unique(data['sections'],'sections')
    cases=unique(data['load_cases'],'load cases'); combos=unique(data['combinations'],'combinations')
    for n in nodes.values():
        if len(n['xyz'])!=3: raise InputError('Node XYZ must have three coordinates')
        for v in n['xyz']: num(v,'coordinate')
        if 'supports' not in n or len(n['supports'])!=6 or any(type(v)!=bool for v in n['supports']): raise InputError('Every node needs six explicit support booleans')
    node_rows=list(nodes.items())
    for idx,(nid,n) in enumerate(node_rows):
        for otherid,other in node_rows[idx+1:]:
            if math.dist(n['xyz'],other['xyz'])<1e-8:raise InputError('Coincident distinct nodes need explicit joint modelling: '+nid+' / '+otherid)
    for m in mats.values():
        for k in ('E','G'): num(m[k],k,True)
        nu=num(m['nu'],'nu'); rho=num(m['weight_density'],'weight_density')
        if not -1<nu<.5 or rho<0: raise InputError('Invalid nu or weight density')
    for s in sections.values():
        for k in ('A','Iy','Iz','J'): num(s[k],k,True)
    for m in members.values():
        if m['i'] not in nodes or m['j'] not in nodes or m['material'] not in mats or m['section'] not in sections: raise InputError('Unresolved member reference')
        if math.dist(nodes[m['i']]['xyz'],nodes[m['j']]['xyz'])<1e-8: raise InputError('Zero length member')
        start=nodes[m['i']]['xyz'];end=nodes[m['j']]['xyz'];delta=[b-a for a,b in zip(start,end)];length2=sum(v*v for v in delta)
        for nid,node in nodes.items():
            if nid in (m['i'],m['j']):continue
            t=sum((p-a)*v for p,a,v in zip(node['xyz'],start,delta))/length2
            if 1e-10<t<1-1e-10 and math.dist(node['xyz'],[a+t*v for a,v in zip(start,delta)])<1e-7:
                raise InputError('Intermediate collinear node '+nid+' would create implicit PyNite connectivity; split member explicitly')
        num(m['rotation_deg'],'rotation_deg')
        if len(m['releases'])!=12 or any(type(v)!=bool for v in m['releases']): raise InputError('Every member needs twelve explicit release booleans')
        if m.get('tension_only') or m.get('compression_only'): raise InputError('Unilateral members require nonlinear analysis')
    sw=data['self_weight']
    if sw.get('mode') not in ('generated','included_in_loads'): raise InputError('Declare self-weight ownership')
    if sw['mode']=='generated' and (sw.get('case') not in cases or sw.get('direction') not in ('FX','FY','FZ')): raise InputError('Invalid self-weight case/direction')
    if sw['mode']=='included_in_loads' and not sw.get('source_ref'): raise InputError('Already included self-weight needs evidence')
    loads=data.get('loads',[])
    if loads: unique(loads,'loads')
    for l in loads:
        if l['case'] not in cases: raise InputError('Unknown load case')
        if sw['mode']=='generated' and l.get('category')=='self_weight': raise InputError('Self-weight would be duplicated')
        if l['type'] not in ('node','member_point','member_distributed'): raise InputError('Unsupported load type: convert area loads explicitly before analysis')
        if l['type']=='node':
            if l['target'] not in nodes or l['direction'] not in ('FX','FY','FZ','MX','MY','MZ'): raise InputError('Invalid node load')
            num(l['value'],'node load')
        else:
            if l['target'] not in members or l['direction'] not in ('FX','FY','FZ','Fx','Fy','Fz','MX','MY','MZ','Mx','My','Mz'): raise InputError('Invalid member load')
            m=members[l['target']]; length=math.dist(nodes[m['i']]['xyz'],nodes[m['j']]['xyz'])
            if l['type']=='member_point':
                if not 0<=num(l['x'],'x')<=length: raise InputError('Load station outside member')
                num(l['value'],'point load')
            else:
                if l['direction'][0].upper()!='F': raise InputError('Distributed moments unsupported')
                if not 0<=num(l['x1'],'x1')<num(l['x2'],'x2')<=length: raise InputError('Invalid distributed interval')
                num(l['w1'],'w1');num(l['w2'],'w2')
    for c in combos.values():
        if c.get('limit_state') not in ('ULS','SLS','TEST') or not c.get('source_ref'): raise InputError('Combination needs limit state and source')
        if not c['factors'] or set(c['factors'])-set(cases): raise InputError('Unknown/empty combination case')
        for f in c['factors'].values(): num(f,'load factor')
    return nodes,members,mats,sections,cases,combos

def run(data):
    data=copy.deepcopy(data)
    try: nodes,members,mats,sections,cases,combos=validate(data)
    except (KeyError,TypeError) as exc: raise InputError('Missing or malformed required input: '+str(exc)) from exc
    model=FEModel3D()
    for k,n in nodes.items(): model.add_node(k,*n['xyz']);model.def_support(k,*n['supports'])
    for k,m in mats.items(): model.add_material(k,m['E'],m['G'],m['nu'],m['weight_density'])
    for k,s in sections.items(): model.add_section(k,s['A'],s['Iy'],s['Iz'],s['J'])
    for k,m in members.items():
        model.add_member(k,m['i'],m['j'],m['material'],m['section'],rotation=m['rotation_deg'])
        model.def_releases(k,*m['releases'])
    for l in data.get('loads',[]):
        if l['type']=='node': model.add_node_load(l['target'],l['direction'],l['value'],case=l['case'])
        elif l['type']=='member_point': model.add_member_pt_load(l['target'],l['direction'],l['value'],l['x'],case=l['case'])
        else: model.add_member_dist_load(l['target'],l['direction'],l['w1'],l['w2'],l['x1'],l['x2'],case=l['case'])
    sw=data['self_weight']
    if sw['mode']=='generated': model.add_member_self_weight(sw['direction'],-1,case=sw['case'])
    for k,c in combos.items(): model.add_load_combo(k,c['factors'])
    model.analyze_linear(check_statics=False)
    results={}; reactions={}; equilibrium={}
    for cid,c in combos.items():
        reactions[cid]={nid:{a:float(getattr(n,'Rxn'+a)[cid]) for a in ('FX','FY','FZ','MX','MY','MZ')} for nid,n in model.nodes.items() if any(nodes[nid]['supports'])}
        import numpy as np
        applied=(model.P(cid)-model.FER(cid)).reshape(-1)
        external=np.zeros(6); residual=np.zeros(6)
        for nid,n in model.nodes.items():
            force=applied[6*n.ID:6*n.ID+3];moment=applied[6*n.ID+3:6*n.ID+6]
            arm=np.array(nodes[nid]['xyz']);external[:3]+=force;external[3:]+=moment+np.cross(arm,force)
        residual=external.copy()
        for nid,r in reactions[cid].items():
            force=np.array([r[k] for k in ('FX','FY','FZ')]);moment=np.array([r[k] for k in ('MX','MY','MZ')])
            residual[:3]+=force;residual[3:]+=moment+np.cross(nodes[nid]['xyz'],force)
        equilibrium[cid]={'applied_resultant_about_origin':external.tolist(),'residual_about_origin':residual.tolist(),'balanced':bool(np.max(np.abs(residual))<=1e-7*max(1.,np.max(np.abs(external))))}
        if not equilibrium[cid]['balanced']: raise ValueError('Global force/moment equilibrium failed: '+cid)
        for mid,m in model.members.items():
            demand={'axial_min_kN':float(m.min_axial(cid)),'axial_max_kN':float(m.max_axial(cid))}
            for axis in ('Fy','Fz'):
                demand[axis+'_min_kN']=float(m.min_shear(axis,cid));demand[axis+'_max_kN']=float(m.max_shear(axis,cid))
            for axis in ('My','Mz'):
                demand[axis+'_min_kNm']=float(m.min_moment(axis,cid));demand[axis+'_max_kNm']=float(m.max_moment(axis,cid))
            for axis in ('dy','dz'):
                demand[axis+'_min_m'],demand[axis+'_max_m']=deflection_extrema(m,axis,cid)
            demand['deflection_envelope_method']='Piecewise first-order polynomial extrema: endpoints and all real quartic derivative roots; no serviceability limit assumed'
            demand['torsion_min_kNm']=float(m.min_torque(cid));demand['torsion_max_kNm']=float(m.max_torque(cid))
            results.setdefault(mid,{})[cid]={'demand':demand,'limit_state':c['limit_state'],'design_status':'NOT_CHECKED'}
    return {'status':'ANALYSIS_COMPLETED_NOT_DESIGN_APPROVAL','solver':{'name':'PyniteFEA','version':version('PyniteFEA')},'input_sha256':hashlib.sha256(json.dumps(data,sort_keys=True,allow_nan=False).encode()).hexdigest(),'units':data['units'],'canonical_coverage':data.get('canonical_coverage',{'basis':'explicit frame input only'}),'members':results,'member_local_axes':{mid:model.members[mid].T()[:3,:3].tolist() for mid in members},'support_reactions':reactions,'equilibrium':equilibrium,'combinations':combos,'self_weight':sw,'scope':'Explicit first-order elastic frame; no inferred panel load distribution, diaphragms, stiffness modifiers, stability or code acceptance.'}
