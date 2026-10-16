"""BCBC 2024 Table 4.1.3.2.-A, ordinary D/L/S/W/E subset only.
Alternative companions remain alternatives. Not a blanket project code selection.
"""
import itertools
SOURCE='https://www2.gov.bc.ca/assets/gov/farming-natural-resources-and-industry/construction-industry/building-codes-and-standards/revisions-and-mo/bcbc_2024_web_version_revision2.pdf'

def generate_uls(cases, applicability):
    required=('ordinary_occupancy','no_cranes','no_soil_or_fluid_loads','no_storage_or_equipment_live','no_roof_parking','code_revision_checked','registry_complete_or_absent_types_confirmed','no_service_room_live','no_H_P_T_or_other_special_actions','directional_cases_complete')
    if any(applicability.get(k) is not True for k in required): raise ValueError('Ordinary Table A scope requires explicit applicability: '+', '.join(required))
    by={k:[] for k in 'DLSWE'};seen=set()
    for case in cases:
        if case['id'] in seen: raise ValueError('Duplicate case ID')
        seen.add(case['id'])
        if case['type'] not in by: raise ValueError('Special load types require a separately reviewed generator')
        by[case['type']].append(case['id'])
    if not by['D']: raise ValueError('Dead load case required')
    if len(by['L'])>1: raise ValueError('Live-load pattern/additive semantics must be resolved into one basic L case')
    rows=[]
    def add(label,factors):
        if any(not by[k] for k in factors):return
        choices=[([by[k]] if k=='D' else [[v] for v in by[k]]) for k in factors]
        for selection in itertools.product(*choices):
            named={cid:f for (k,f),ids in zip(factors.items(),selection) for cid in ids}
            rows.append({'id':label+'__'+'__'.join('+'.join(v) for v in selection),'limit_state':'ULS','factors':named,'source_ref':SOURCE+' Table 4.1.3.2.-A','code':'BCBC2024','applicability':dict(applicability)})
    add('A1',{'D':1.4})
    for df in (1.25,.9):
        for label,principal,pf,companions in [('A2','L',1.5,[{}, {'S':1.}, {'W':.4}]),('A3','S',1.5,[{}, {'L':1.}, {'W':.4}]),('A4','W',1.4,[{}, {'L':.5}, {'S':.5}])]:
            for i,comp in enumerate(companions):add(f'{label}_D{df}_C{i}',{'D':df,principal:pf,**comp})
    add('A5_zero_companion',{'D':1.,'E':1.})
    seismic={'D':1.,'E':1.}
    if by['L']:seismic['L']=.5
    if by['S']:seismic['S']=.25
    if len(seismic)>2:add('A5_companions',seismic)
    if by['L'] and by['S']:
        start=len(rows)
        add('SUPPLEMENTAL_A5_L_only',{'D':1.,'E':1.,'L':.5})
        add('SUPPLEMENTAL_A5_S_only',{'D':1.,'E':1.,'S':.25})
        for row in rows[start:]:
            row['source_ref']='Supplemental companion-subset response envelope; not asserted as a prescribed BCBC table row. '+SOURCE
            row['supplemental']=True
    return rows
