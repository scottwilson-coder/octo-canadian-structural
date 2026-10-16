"""Reduced EI beam equilibrium and analytical checks, not whole-building verification."""
import unittest,copy,math
from octo_pynite.planar import run_beam,to_frame
from octo_pynite.adapter import InputError

def planar():
    return {'id':'B','length_m':4,'EI_kNm2':16000,'source_ref':'synthetic benchmark','idealization_status':'TEST_ONLY','supports':[{'x_m':0,'vertical_fixed':True,'rotation_fixed':False},{'x_m':4,'vertical_fixed':True,'rotation_fixed':False}], 'load_cases':[{'id':'D'}],'combinations':[{'id':'C','limit_state':'TEST','source_ref':'synthetic','factors':{'D':1}}],'self_weight':{'mode':'included_in_loads','source_ref':'not applied in benchmark'},'loads':[{'id':'q','case':'D','type':'distributed','x1_m':0,'x2_m':4,'w1_kNm':-5,'w2_kNm':-5}]}
class PlanarIndependentTests(unittest.TestCase):
    def test_simply_supported(self):
        r=run_beam(planar())['result'];d=r['members']['B:S0']['C']['demand'];self.assertAlmostEqual(d['dy_min_m'],-5*5*4**4/(384*16000))
    def test_cantilever(self):
        b=planar();b['supports']=b['supports'][:1];b['supports'][0]['rotation_fixed']=True;r=run_beam(b)['result']
        self.assertAlmostEqual(r['members']['B:S0']['C']['demand']['dy_min_m'],-5*4**4/(8*16000))
    def test_two_equal_spans(self):
        b=planar();b['supports'].insert(1,{'x_m':2,'vertical_fixed':True,'rotation_fixed':False});r=run_beam(b)['result'];a=r['support_reactions']['C']
        for nid,fy in [('B:N0',3.75),('B:N1',12.5),('B:N2',3.75)]:self.assertAlmostEqual(a[nid]['FY'],fy)
        d=r['members']['B:S0']['C']['demand'];self.assertAlmostEqual(max(abs(d['Mz_min_kNm']),abs(d['Mz_max_kNm'])),2.5)
    def test_overhang(self):
        b=planar();b['supports'][1]['x_m']=2;r=run_beam(b)['result'];a=r['support_reactions']['C']
        self.assertAlmostEqual(a['B:N0']['FY'],0);self.assertAlmostEqual(a['B:N1']['FY'],20)
    def test_split_linear_load_balance(self):
        b=planar();b['supports'].insert(1,{'x_m':2,'vertical_fixed':True,'rotation_fixed':False});b['loads'][0]['w1_kNm']=0
        r=run_beam(b)['result'];a=r['support_reactions']['C'];self.assertAlmostEqual(sum(v['FY'] for v in a.values()),10)
        self.assertAlmostEqual(2*a['B:N1']['FY']+4*a['B:N2']['FY'],5*4**2/3)
    def test_support_station_point_load_once(self):
        b=planar();b['supports'].insert(1,{'x_m':2,'vertical_fixed':True,'rotation_fixed':False});b['loads']=[{'id':'P','type':'point','case':'D','x_m':2,'value':-10}]
        r=run_beam(b)['result'];self.assertAlmostEqual(sum(v['FY'] for v in r['support_reactions']['C'].values()),10)
    def test_negative_or_nonfinite_ei_reject(self):
        for v in (-1,0,math.nan,math.inf,True):
            b=planar();b['EI_kNm2']=v
            with self.assertRaises(ValueError):run_beam(b)
    def test_invalid_support_boolean_reject(self):
        b=planar();b['supports'][0]['vertical_fixed']=1
        with self.assertRaises(ValueError):run_beam(b)
    def test_outside_support_reject(self):
        b=planar();b['supports'][0]['x_m']=-1
        with self.assertRaises(ValueError):run_beam(b)
    def test_duplicate_support_reject(self):
        b=planar();b['supports'].append(copy.deepcopy(b['supports'][0]))
        with self.assertRaises(ValueError):run_beam(b)
    def test_outside_load_reject(self):
        b=planar();b['loads'][0]['x2_m']=5
        with self.assertRaises(ValueError):run_beam(b)
    def test_physical_design_not_inferred(self):
        b=planar();b['design_properties']={'anything':'ignored'};r=run_beam(b)
        self.assertFalse(r['input']['canonical_coverage']['physical_design_properties_imported'])
        for m in r['input']['members']:self.assertNotIn('design_properties',m)
        for n in r['input']['nodes']:self.assertTrue(all(n['supports'][j] for j in [0,2,3,4]))
    def test_generated_sw_rejected(self):
        b=planar();b['self_weight']={'mode':'generated','case':'D','direction':'FY'}
        with self.assertRaises(ValueError):run_beam(b)
    def test_no_restraint_mechanism_rejected(self):
        b=planar();b['supports']=[{'x_m':0,'vertical_fixed':True,'rotation_fixed':False}]
        with self.assertRaises(Exception):run_beam(b)
if __name__=='__main__':unittest.main(verbosity=2)
