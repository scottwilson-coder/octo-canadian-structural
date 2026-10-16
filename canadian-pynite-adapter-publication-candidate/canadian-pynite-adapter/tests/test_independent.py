"""Independent elastic analysis verification. No CSA member-design verification."""
import copy
import math
import unittest
from octo_pynite.adapter import run, validate, InputError


def beam():
    return {'units':{'length':'m','force':'kN','stress':'kN/m2'},'analysis':'first_order_linear',
      'nodes':[{'id':'A','xyz':[0,0,0],'supports':[True]*6},{'id':'B','xyz':[4,0,0],'supports':[False]*6}],
      'members':[{'id':'AB','i':'A','j':'B','material':'steel','section':'S','rotation_deg':0,'releases':[False]*12}],
      'materials':[{'id':'steel','E':200e6,'G':76.923e6,'nu':.3,'weight_density':78.5}],
      'sections':[{'id':'S','A':.01,'Iy':4e-5,'Iz':8e-5,'J':1e-5}],
      'load_cases':[{'id':'D'},{'id':'L'}],
      'combinations':[{'id':'C','factors':{'D':1},'limit_state':'TEST','source_ref':'Independent elastic benchmark'}],
      'self_weight':{'mode':'included_in_loads','source_ref':'Benchmark neglects self-weight'},
      'loads':[{'id':'q','type':'member_distributed','target':'AB','case':'D','direction':'FY','w1':-5,'w2':-5,'x1':0,'x2':4}]}

class IndependentTests(unittest.TestCase):
    def assertNear(self,a,b): self.assertAlmostEqual(a,b,delta=max(1e-9,abs(b)*1e-6))
    def test_cantilever_uniform(self):
        r=run(beam()); d=r['members']['AB']['C']['demand']; a=r['support_reactions']['C']['A']
        self.assertNear(a['FY'],20);self.assertNear(a['MZ'],40)
        self.assertNear(max(abs(d['Mz_min_kNm']),abs(d['Mz_max_kNm'])),40)
        self.assertNear(d['dy_min_m'],-5*4**4/(8*200e6*8e-5))
        self.assertEqual(r['members']['AB']['C']['design_status'],'NOT_CHECKED')
    def test_simply_supported_midpoint_extrema(self):
        b=beam();b['nodes'][0]['supports']=[True,True,True,True,False,False];b['nodes'][1]['supports']=[False,True,True,False,False,False]
        r=run(b);d=r['members']['AB']['C']['demand']
        self.assertNear(r['support_reactions']['C']['A']['FY'],10);self.assertNear(r['support_reactions']['C']['B']['FY'],10)
        self.assertNear(max(abs(d['Mz_min_kNm']),abs(d['Mz_max_kNm'])),10)
        self.assertNear(d['dy_min_m'],-5*5*4**4/(384*200e6*8e-5))
    def test_tip_point_and_load_factor(self):
        b=beam();b['loads']=[{'id':'P','type':'node','target':'B','case':'L','direction':'FY','value':-10}];b['combinations'][0]['factors']={'L':1.5}
        r=run(b);d=r['members']['AB']['C']['demand'];a=r['support_reactions']['C']['A']
        self.assertNear(a['FY'],15);self.assertNear(a['MZ'],60);self.assertNear(d['dy_min_m'],-15*4**3/(3*200e6*8e-5))
    def test_generated_self_weight_and_balance(self):
        b=beam();b['loads']=[];b['self_weight']={'mode':'generated','case':'D','direction':'FY'}
        r=run(b);self.assertNear(r['support_reactions']['C']['A']['FY'],78.5*.01*4)
        self.assertNear(r['support_reactions']['C']['A']['MZ'],78.5*.01*4*2)
    def test_reject_self_weight_duplicate(self):
        b=beam();b['self_weight']={'mode':'generated','case':'D','direction':'FY'};b['loads'][0]['category']='self_weight'
        with self.assertRaises(ValueError): run(b)
    def test_no_silent_unit_conversion(self):
        b=beam();b['units']['length']='mm'
        with self.assertRaises(ValueError): run(b)
    def test_reject_missing_member_node(self):
        b=beam();b['members'][0]['j']='missing'
        with self.assertRaises(ValueError):run(b)
    def test_reject_duplicate_id(self):
        b=beam();b['nodes'].append(copy.deepcopy(b['nodes'][0]))
        with self.assertRaises(ValueError):run(b)
    def test_reject_nonfinite_properties(self):
        for value in (math.nan,math.inf,-math.inf,0,-1,True):
            with self.subTest(value=value):
                b=beam();b['sections'][0]['Iz']=value
                with self.assertRaises(ValueError):run(b)
    def test_reject_missing_properties_cleanly(self):
        b=beam();del b['materials'][0]['E']
        with self.assertRaises(InputError):run(b)
    def test_reject_missing_combo_case(self):
        b=beam();b['combinations'][0]['factors']={'absent':1}
        with self.assertRaises(ValueError):run(b)
    def test_reject_unstable(self):
        b=beam();b['nodes'][0]['supports']=[False]*6
        with self.assertRaises(Exception):run(b)
    def test_reject_unconstrained_torsion(self):
        b=beam();b['nodes'][0]['supports'][3]=False
        with self.assertRaises(Exception):run(b)
    def test_stiffness_sensitivity(self):
        b=beam();d1=run(b)['members']['AB']['C']['demand']['dy_min_m'];b['sections'][0]['Iz']*=2
        self.assertNear(run(b)['members']['AB']['C']['demand']['dy_min_m'],d1/2)
    def test_global_local_axis_rotation(self):
        b=beam();b['members'][0]['rotation_deg']=90
        r=run(b);d=r['members']['AB']['C']['demand'];self.assertNear(r['support_reactions']['C']['A']['FY'],20)
        self.assertNear(max(abs(d['dz_min_m']),abs(d['dz_max_m'])),5*4**4/(8*200e6*4e-5))
    def test_unloaded_case(self):
        b=beam();b['combinations'][0]['factors']={'L':1}
        r=run(b);self.assertNear(r['support_reactions']['C']['A']['FY'],0)
    def test_member_release_propped_cantilever(self):
        b=beam();b['nodes'][1]['supports']=[True]*6;b['members'][0]['releases'][11]=True
        r=run(b);a=r['support_reactions']['C']['A'];z=r['support_reactions']['C']['B']
        self.assertNear(a['FY'],12.5);self.assertNear(z['FY'],7.5)
        self.assertNear(a['MZ'],10);self.assertNear(z['MZ'],0)
    def test_column_global_load_foundation_reactions(self):
        b=beam();b['nodes'][1]['xyz']=[0,4,0];b['loads']=[{'id':'P','type':'node','target':'B','case':'D','direction':'FX','value':10}]
        r=run(b);a=r['support_reactions']['C']['A']
        self.assertNear(a['FX'],-10);self.assertNear(a['MZ'],40)
    def test_combination_superposition(self):
        b=beam();b['loads'].append({'id':'P','type':'member_point','target':'AB','case':'L','direction':'FY','value':-10,'x':2})
        b['combinations'][0]['factors']={'D':1.25,'L':1.5}
        a=run(b)['support_reactions']['C']['A'];self.assertNear(a['FY'],40);self.assertNear(a['MZ'],80)
    def test_invalid_release_shape(self):
        b=beam();b['members'][0]['releases']=[False]*11
        with self.assertRaises(InputError):run(b)
    def test_zero_length(self):
        b=beam();b['nodes'][1]['xyz']=[0,0,0]
        with self.assertRaises(InputError):run(b)
    def test_outside_member_point(self):
        b=beam();b['loads']=[{'id':'P','type':'member_point','target':'AB','case':'D','direction':'FY','value':-10,'x':4.01}]
        with self.assertRaises(InputError):run(b)
    def test_no_nonlinear_silent_downgrade(self):
        b=beam();b['analysis']='P-delta'
        with self.assertRaises(InputError):run(b)
    def test_reject_unilateral_member(self):
        b=beam();b['members'][0]['tension_only']=True
        with self.assertRaises(InputError):run(b)
    def test_reject_implicit_intermediate_connectivity(self):
        b=beam();b['nodes'].append({'id':'C','xyz':[2,0,0],'supports':[True]*6})
        with self.assertRaises(InputError):run(b)
    def test_reject_nonfinite_osm_geometry(self):
        from octo_pynite.canonical import from_osm
        b=beam();spec=b['members'].pop();osm={'units':'m','pynite_binding':b,'elements':[{'id':'AB','type':'beam','analysis_member':spec,'geometry':{'start_m':[math.nan,0,0],'end_m':[4,0,0]}}]}
        with self.assertRaises(InputError):from_osm(osm)
    def test_triangular_loads_both_axes(self):
        for direction,axis,I in [('FY','dy',8e-5),('FZ','dz',4e-5)]:
            with self.subTest(direction=direction):
                b=beam();b['loads'][0].update(direction=direction,w1=0,w2=-5)
                d=run(b)['members']['AB']['C']['demand']
                self.assertNear(d[axis+'_min_m'],-11*5*4**4/(120*200e6*I))
    def test_partial_uniform_loads_both_axes(self):
        for direction,axis,I in [('FY','dy',8e-5),('FZ','dz',4e-5)]:
            with self.subTest(direction=direction):
                b=beam();b['loads'][0].update(direction=direction,x1=2)
                d=run(b)['members']['AB']['C']['demand']
                exact=-5/(6*200e6*I)*((4*4**3-4**4/4)-(4*2**3-2**4/4))
                self.assertNear(d[axis+'_min_m'],exact)
    def test_end_moments_both_axes(self):
        for direction,axis,I in [('MZ','dy',8e-5),('MY','dz',4e-5)]:
            with self.subTest(direction=direction):
                b=beam();b['loads']=[{'id':'M','type':'node','target':'B','case':'D','direction':direction,'value':10}]
                d=run(b)['members']['AB']['C']['demand']
                self.assertNear(max(abs(d[axis+'_min_m']),abs(d[axis+'_max_m'])),10*4**2/(2*200e6*I))
    def test_simply_supported_triangular_interior_extrema_both_axes(self):
        for direction,axis,I in [('FY','dy',8e-5),('FZ','dz',4e-5)]:
            with self.subTest(direction=direction):
                b=beam();b['nodes'][0]['supports']=[True,True,True,True,False,False];b['nodes'][1]['supports']=[False,True,True,False,False,False]
                b['loads'][0].update(direction=direction,w1=0,w2=-5)
                d=run(b)['members']['AB']['C']['demand'];x=4*math.sqrt(1-math.sqrt(8/15))
                exact=(5*4*x**3/36-5*x**5/(120*4)-7*5*4**3*x/360)/(200e6*I)
                self.assertNear(d[axis+'_min_m'],exact)
    def test_explicit_split_member_continuity(self):
        b=beam();b['nodes'].append({'id':'C','xyz':[2,0,0],'supports':[False]*6})
        b['members'][0]['j']='C';m=copy.deepcopy(b['members'][0]);m.update(id='CB',i='C',j='B');b['members'].append(m)
        b['loads'][0]['x2']=2;l=copy.deepcopy(b['loads'][0]);l.update(id='q2',target='CB');b['loads'].append(l)
        r=run(b);self.assertNear(r['support_reactions']['C']['A']['FY'],20);self.assertNear(r['support_reactions']['C']['A']['MZ'],40)
        self.assertNear(r['members']['CB']['C']['demand']['dy_min_m'],-5*4**4/(8*200e6*8e-5))
    def test_input_not_mutated(self):
        b=beam();old=copy.deepcopy(b);run(b);self.assertEqual(old,b)

if __name__=='__main__': unittest.main(verbosity=2)
