import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from travel_core.engine import execute
from travel_core.common import InputError
from travel_core.places import same_place, distance_km

Q={"checkin":"2026-12-02","checkout":"2026-12-04","guests":2,"rooms":1,
   "room_type":"double","currency":"CNY","all_in_price":720,
   "price_basis":"all_in_total","taxes_included":True,"mandatory_fees_included":True,
   "breakfast":"none","cancellation":"free","membership_required":False,
   "payment_terms":"pay_on_arrival"}

class TestTaskRouting(unittest.TestCase):
    def test_capabilities_without_key(self):
        self.assertIn('compare',execute({'task':'capabilities'})['offline'])
    def test_single_question_missing_hotel_date(self):
        x=execute({'task':'preflight','target_task':'compare','kind':'hotel','context':{'live_price_required':True},'options':[{'id':'a'},{'id':'b'}]})
        self.assertFalse(x['may_proceed']); self.assertEqual(x['ask_next']['field'],'checkin')
    def test_no_questions_qualitative(self):
        x=execute({'task':'preflight','target_task':'compare','kind':'hotel','options':[{'id':'a'},{'id':'b'}]})
        self.assertTrue(x['may_proceed'])
    def test_verify_no_claim(self):
        self.assertEqual(execute({'task':'verify'})['status'],'needs_clarification')
    def test_plan_no_destination_and_no_days(self):
        self.assertEqual(execute({'task':'plan'})['question']['field'],'destination')
    def test_plan_with_user_days(self):
        x=execute({'task':'plan','days':[{'date':'2026-12-03','stops':[]}], 'costs':{}})
        self.assertEqual(x['status'],'provided_draft_audited')
        self.assertFalse(x['automatic_offline_planning'])
        self.assertEqual(x['overall_status'],'unknown')

    def test_plan_delegated_to_host_agent(self):
        x=execute({'task':'plan','destination':'成都'})
        self.assertEqual(x['status'],'host_agent_planning_required')
        self.assertFalse(x['automatic_offline_planning'])
        self.assertIn('itinerary-planning.md',x['workflow_reference'])
    def test_reject_unknown_task(self):
        with self.assertRaises(InputError): execute({'task':'pay'})
    def test_budget_missing_envelope(self):
        self.assertIn('total_budget',execute({'task':'budget'})['missing'])

class TestCompare(unittest.TestCase):
    def opts(self):
        return {'task':'compare','kind':'hotel','options':[
            {'id':'a','name':'A','quote':dict(Q),'signals':{'comfort':70}},
            {'id':'b','name':'B','quote':dict(Q,all_in_price=650),'signals':{'comfort':80}}]}
    def test_price_compare_and_pareto(self):
        out=execute(self.opts())
        self.assertEqual(out['price_ranking_low_to_high'],['b','a'])
        self.assertIn({'option_id':'a','dominated_by':'b','scope':'supplied_metrics_only'},out['dominated_options'])
    def test_dates_mismatch_not_comparable(self):
        x=self.opts(); x['options'][1]['quote']['checkin']='2026-12-05'
        self.assertEqual(execute(x)['comparable_option_ids'],[])
    def test_tax_unknown_rejected(self):
        x=self.opts(); x['options'][0]['quote']['taxes_included']=False
        self.assertIn('a',execute(x)['pending_normalization'])
    def test_missing_quote_no_false_price(self):
        x=self.opts(); x['options'][0].pop('quote')
        self.assertEqual(execute(x)['options'][0]['all_in_price'],None)
    def test_cancellation_difference_prevents_pareto_dominance(self):
        x=self.opts(); x['options'][0]['quote']['cancellation']='free'; x['options'][1]['quote']['cancellation']='nonrefundable'
        self.assertEqual(execute(x)['dominated_options'],[])
    def test_different_breakfast_is_not_same_package(self):
        x=self.opts(); x['options'][1]['quote']['breakfast']='included'
        out=execute(x)
        self.assertEqual(out['price_ranking_low_to_high'], [])
        self.assertEqual(out['comparable_option_ids'], [])
        self.assertTrue(all(o['quote_normalized'] for o in out['options']))
        self.assertTrue(all(not o['price_comparable'] for o in out['options']))

    def test_different_refund_is_not_same_package(self):
        x=self.opts(); x['options'][1]['quote']['cancellation']='nonrefundable'
        self.assertEqual(execute(x)['price_ranking_low_to_high'], [])

    def test_payment_terms_difference_prevents_equivalence(self):
        x=self.opts(); x['options'][1]['quote']['payment_terms']='pay_in_advance'
        out=execute(x)
        self.assertEqual(out['price_ranking_low_to_high'],[])
        self.assertTrue(all(not o['price_comparable'] for o in out['options']))

    def test_negative_guests_rejected(self):
        x=self.opts(); x['options'][0]['quote']['guests']=-1
        out=execute(x)
        self.assertIn('a',out['pending_normalization'])

    def test_missing_member_eligibility_not_comparable(self):
        x=self.opts(); x['options'][1]['quote'].pop('membership_required')
        out=execute(x)
        self.assertIn('b', out['pending_normalization'])
        self.assertEqual(out['price_ranking_low_to_high'], [])

    def test_two_separate_comparable_groups(self):
        x=self.opts()
        x['options'] += [
            {'id':'c','quote':dict(Q, breakfast='included',all_in_price=900)},
            {'id':'d','quote':dict(Q, breakfast='included',all_in_price=850)},
        ]
        out=execute(x)
        self.assertEqual(len(out['comparable_groups']),2)
        self.assertEqual(out['price_ranking_low_to_high'], [])
        self.assertEqual(out['comparable_groups'][1]['price_ranking_low_to_high'],['d','c'])

    def test_unlisted_features_prevent_dominance(self):
        x=self.opts(); x['options'][0]['features']={'near_subway':True}
        self.assertEqual(execute(x)['dominated_options'],[])

    def test_weighted_score_requires_shared_signals(self):
        x=self.opts(); x['weights']={'comfort':1.0}
        out=execute(x)
        self.assertEqual(out['options'][1]['indicative_preference_score'],80.0)
    def test_reject_negative_price(self):
        x=self.opts(); x['options'][0]['quote']['all_in_price']=-5
        with self.assertRaises(InputError): execute(x)
    def test_reject_same_id(self):
        x=self.opts(); x['options'][0]['id']='b'
        with self.assertRaises(InputError): execute(x)

class TestEvidence(unittest.TestCase):
    def test_unverified_claim(self):
        x=execute({'task':'verify','as_of':'2026-11-17','claims':[{'id':'x','text':'周一开放','kind':'opening_hours','evidence':[]}]})
        self.assertEqual(x['claims'][0]['verdict'],'not_verified')
    def test_official_checked_support(self):
        x=execute({'task':'verify','as_of':'2026-11-17','claims':[{'id':'x','text':'闭馆','kind':'opening_hours','evidence':[
            {'id':'s','url':'https://example.org/official','stance':'support','source_type':'official',
             'verification_status':'checked','retrieved_at':'2026-11-17'}]}]})
        self.assertEqual(x['claims'][0]['verdict'],'supported_by_authoritative_source')
    def test_self_labeled_official_not_enough(self):
        x=execute({'task':'verify','as_of':'2026-11-17','claims':[{'text':'闭馆','kind':'entry_rules','evidence':[
            {'id':'s','url':'https://example.com','stance':'support','source_type':'official','retrieved_at':'2026-11-17'}]}]})
        self.assertEqual(x['claims'][0]['verdict'],'not_verified')
    def test_contested(self):
        claim={'text':'收费','kind':'opening_hours','evidence':[
            {'id':'1','url':'https://official.example/a','stance':'support','source_type':'official','verification_status':'checked','retrieved_at':'2026-11-17'},
            {'id':'2','url':'https://other.example/b','stance':'contradict','retrieved_at':'2026-11-17'}]}
        self.assertEqual(execute({'task':'verify','as_of':'2026-11-17','claims':[claim]})['claims'][0]['verdict'],'contested')
    def test_stale_evidence(self):
        claim={'text':'营业','kind':'opening_hours','evidence':[{'id':'old','url':'https://x.com/a','stance':'support','retrieved_at':'2025-01-01'}]}
        x=execute({'task':'verify','as_of':'2026-11-17','claims':[claim]})
        self.assertEqual(x['claims'][0]['stale_or_undated_sources'],['old'])
    def test_duplicate_origin_one_vote(self):
        claim={'text':'很好','kind':'experience','evidence':[
            {'id':str(i),'url':f'https://same.example/{i}','stance':'support'} for i in range(3)]}
        x=execute({'task':'verify','claims':[claim]})['claims'][0]
        self.assertEqual(x['independent_supporting_origins'],1)

class TestPlaces(unittest.TestCase):
    def test_same_name_different_address_no_merge(self):
        self.assertFalse(same_place({'name':'便利店','address':'北京海淀'}, {'name':'便利店','address':'成都高新'}))
    def test_alias_geocoded_merge(self):
        a={'name':'IFS','aliases':['成都IFS'],'latitude':30.661,'longitude':104.080}
        b={'name':'成都IFS','latitude':30.662,'longitude':104.081}
        self.assertTrue(same_place(a,b))
    def test_coords_only_not_merge(self):
        self.assertFalse(same_place({'name':'Hotel A','latitude':30.1,'longitude':104.1},
                                    {'name':'Hotel B','latitude':30.1,'longitude':104.1}))
    def test_distance_invalid(self):
        with self.assertRaises(InputError): distance_km((91,0),(0,0))
    def test_discover_merging(self):
        o=execute({'task':'discover','places':[{'id':'1','name':'IFS','aliases':['成都IFS'],'address':'成都锦江区A'},
                                                {'id':'2','name':'成都IFS','address':'成都锦江区A'}]})
        self.assertEqual(o['candidate_count'],1)

class TestAudit(unittest.TestCase):
    def day(self, transfer=20):
        return {'task':'audit','days':[{'date':'2026-12-03','stops':[
            {'id':'a','name':'A','start':'09:00','end':'10:00','opening_window':{'start':'08:00','end':'18:00'},'opening_verified':True},
            {'id':'b','name':'B','start':'10:10','end':'11:00','opening_window':{'start':'09:00','end':'20:00'},'opening_verified':True,
             'transfer_from_previous_minutes':transfer,'transfer_source':'map_route'}]}],
             'costs':{'a':{'amount':60}},'total_budget':100,'currency':'CNY','costs_complete':True}
    def test_infeasible_transfer(self):
        x=execute(self.day())
        self.assertEqual(x['overall_status'],'fail')
        self.assertEqual(x['days'][0]['issues'][0]['code'],'insufficient_transfer_time')
    def test_feasible_checked(self):
        self.assertEqual(execute(self.day(10))['overall_status'],'pass')
    def test_missing_transfer_unknown(self):
        x=self.day(); x['days'][0]['stops'][1].pop('transfer_from_previous_minutes')
        self.assertEqual(execute(x)['overall_status'],'unknown')
    def test_budget_failure(self):
        x=self.day(10); x['total_budget']=20
        self.assertEqual(execute(x)['cost_check']['status'],'fail')
    def test_budget_missing_required_category_is_unknown(self):
        x=self.day(10); x['required_cost_categories']=['a','hotel']
        out=execute(x)
        self.assertEqual(out['cost_check']['status'],'unknown')
        self.assertEqual(out['cost_check']['missing_required_categories'],['hotel'])

    def test_missing_expenses_not_falsely_passed(self):
        x=self.day(10); x.pop('costs_complete')
        self.assertEqual(execute(x)['cost_check']['status'],'unknown')
    def test_unknown_price(self):
        x=self.day(10); x['costs']['hotel']={}
        self.assertEqual(execute(x)['cost_check']['status'],'unknown')
    def test_no_unverified_opening_assurance(self):
        x=self.day(10); x['days'][0]['stops'][0]['opening_verified']=False
        self.assertEqual(execute(x)['overall_status'],'unknown')

class TestRevision(unittest.TestCase):
    def base(self):
        return {'task':'revise','session':{'version':2,'days':[{'date':'2026-12-03','stops':[
            {'id':'a','name':'A','start':'09:00','end':'10:00','decision_status':'locked'},
            {'id':'b','name':'B','start':'11:00','end':'12:00','decision_status':'provisional'}]},
            {'date':'2026-12-04','stops':[{'id':'x','name':'X','start':'13:00','end':'14:00'}]}]},
            'changes':[{'op':'update_stop','date':'2026-12-03','stop_id':'b','fields':{'name':'C'}}]}
    def test_local_edit(self):
        x=execute(self.base())
        self.assertEqual(x['session']['version'],3)
        self.assertEqual(x['session']['days'][0]['stops'][1]['name'],'C')
        self.assertEqual(x['session']['days'][1]['stops'][0]['name'],'X')
        self.assertEqual(x['affected_days'],['2026-12-03'])
    def test_locked_protected(self):
        x=self.base(); x['changes'][0]['stop_id']='a'
        with self.assertRaises(InputError): execute(x)
    def test_bool_version_rejected(self):
        x=self.base(); x['session']['version']=True
        with self.assertRaises(InputError): execute(x)

    def test_stale_version_protected(self):
        x=self.base(); x['expected_version']=1
        with self.assertRaises(InputError): execute(x)
    def test_no_arbitrary_fields(self):
        x=self.base(); x['changes'][0]['fields']={'decision_status':'booked'}
        with self.assertRaises(InputError): execute(x)

class TestZeroConfigRuntime(unittest.TestCase):
    def test_no_user_configuration_needed(self):
        with patch.dict(os.environ, {}, clear=True):
            result = execute({'task': 'capabilities'})
        self.assertFalse(result['setup_required'])
        self.assertFalse(result['api_keys_required'])
        self.assertFalse(result['environment_variables_required'])
        self.assertEqual(result['pip_dependencies'], [])
        self.assertIn('Host agent', result['live_research']['execution'])

    def test_key_requiring_operations_not_exposed(self):
        for task in ('amap_geocode', 'amap_walk', 'poi_search'):
            with self.assertRaises(InputError):
                execute({'task': task})

    def test_offline_compare_works_with_empty_environment(self):
        payload = TestCompare().opts()
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(execute(payload)['price_ranking_low_to_high'], ['b', 'a'])

if __name__ == '__main__': unittest.main()
