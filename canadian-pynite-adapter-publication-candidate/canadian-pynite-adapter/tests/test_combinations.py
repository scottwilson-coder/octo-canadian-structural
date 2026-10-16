"""Synthetic enumeration tests; not independent adopted-code qualification."""
import unittest
from octo_pynite.combinations import generate_uls


def applicability():
    return dict.fromkeys(('ordinary_occupancy','no_cranes','no_soil_or_fluid_loads',
        'no_storage_or_equipment_live','no_roof_parking','code_revision_checked',
        'registry_complete_or_absent_types_confirmed','no_service_room_live',
        'no_H_P_T_or_other_special_actions','directional_cases_complete'), True)


def cases():
    return [{'id':k,'type':k[0]} for k in ('D','L','S','W+','W-','E+','E-')]


class CombinationTests(unittest.TestCase):
    def test_signed_alternatives(self):
        rows=generate_uls(cases(),applicability())
        self.assertEqual(len(rows),len({r['id'] for r in rows}))
        for row in rows:
            self.assertLessEqual(len(set(row['factors'])&{'W+','W-'}),1)
            self.assertLessEqual(len(set(row['factors'])&{'E+','E-'}),1)
    def test_each_scope_flag_required(self):
        for key in applicability():
            app=applicability();app[key]=False
            with self.assertRaises(ValueError):generate_uls(cases(),app)
    def test_additive_dead_loads(self):
        rows=generate_uls(cases()+[{'id':'D2','type':'D'}],applicability())
        for row in rows:self.assertEqual(row['factors']['D'],row['factors']['D2'])
    def test_supplemental_rows_marked(self):
        rows=generate_uls(cases(),applicability())
        supplemental=[r for r in rows if r['id'].startswith('SUPPLEMENTAL_')]
        self.assertEqual(len(supplemental),4)
        self.assertTrue(all(r.get('supplemental') is True for r in supplemental))
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):generate_uls(cases()+[cases()[0]],applicability())
    def test_special_type_rejected(self):
        with self.assertRaises(ValueError):generate_uls(cases()+[{'id':'H','type':'H'}],applicability())
    def test_multiple_live_rejected(self):
        with self.assertRaises(ValueError):generate_uls(cases()+[{'id':'L2','type':'L'}],applicability())
    def test_dead_required(self):
        with self.assertRaises(ValueError):generate_uls(cases()[1:],applicability())
