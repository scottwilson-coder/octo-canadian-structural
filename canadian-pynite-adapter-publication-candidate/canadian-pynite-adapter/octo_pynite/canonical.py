"""Opt-in OSM bridge: never infer FE supports or joint identity from graphics."""
import copy,math
from .adapter import InputError,num

def from_osm(osm):
    binding=copy.deepcopy(osm.get('pynite_binding'))
    if not isinstance(binding,dict):raise InputError('OSM needs explicit pynite_binding nodes, materials, sections, load cases and combinations')
    if osm.get('units')!='m':raise InputError('OSM geometry must explicitly use metres')
    nodes={n['id']:n for n in binding['nodes']};members=[]
    ignored=[]
    for e in osm['elements']:
        spec=e.get('analysis_member')
        if not spec:
            if e.get('type',e.get('kind')) in ('beam','post','column','joist','rafter'):raise InputError('Missing analysis_member binding for '+e['id'])
            ignored.append(e['id']);continue
        row=copy.deepcopy(spec);row['id']=e['id']
        geo=e['geometry']
        for endpoint,node in [('start_m',row['i']),('end_m',row['j'])]:
            if len(geo[endpoint])!=3:raise InputError('Three coordinates required')
            for v in geo[endpoint]:num(v,'OSM coordinate')
            if node not in nodes or math.dist(geo[endpoint],nodes[node]['xyz'])>1e-8:raise InputError('Geometry/node mismatch '+e['id'])
        if e.get('properties',{}).get('wood_design'):row['design_properties']=copy.deepcopy(e['properties'])
        members.append(row)
    binding['members']=members;binding['canonical_coverage']={'excluded_nonframe_element_ids':ignored,'source_project':osm.get('project'),'note':'Area loads, wall/diaphragm stiffness and transfers must be explicitly supplied in analysis binding.'}
    return binding
