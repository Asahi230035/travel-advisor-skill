"""Comprehensive unit & CLI tests for Travel Advisor Skill v2.0 deterministic helpers."""
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travel_core.common import InputError
from travel_core.engine import execute


class EvidenceFreshnessTests(unittest.TestCase):
    def test_stale_blog_retrieved_today_is_rejected(self):
        res = execute({
            'task': 'verify',
            'as_of': '2026-11-21',
            'claims': [{
                'id': 'c1',
                'text': 'Museum opens Mondays',
                'kind': 'opening_hours',
                'evidence': [{
                    'id': 'old_blog',
                    'url': 'https://blog.example.com/2023-guide',
                    'source_type': 'blog',
                    'verification_status': 'checked',
                    'evidence_depth': 'full_page',
                    'stance': 'support',
                    'published_at': '2023-05-01',
                    'retrieved_at': '2026-11-21',
                }],
            }],
        })
        c = res['claims'][0]
        self.assertEqual(c['verdict'], 'stale_needs_recheck')
        self.assertEqual(c['badge'], '⚠️')
        self.assertEqual(c['stale_published_sources'], ['old_blog'])

    def test_snippet_only_blocked_for_operational_claims(self):
        res = execute({
            'task': 'verify',
            'as_of': '2026-11-21',
            'claims': [{
                'id': 'c2',
                'text': 'Entry rule visa free 15 days',
                'kind': 'entry_rules',
                'evidence': [{
                    'id': 'official_snip',
                    'url': 'https://immigration.example.gov/visa',
                    'source_type': 'official',
                    'verification_status': 'checked',
                    'evidence_depth': 'snippet',
                    'stance': 'support',
                    'published_at': '2026-11-20',
                    'retrieved_at': '2026-11-21',
                }],
            }],
        })
        c = res['claims'][0]
        self.assertEqual(c['verdict'], 'not_verified')
        self.assertEqual(c['snippet_only_sources'], ['official_snip'])

    def test_future_retrieved_at_rejected(self):
        res = execute({
            'task': 'verify',
            'as_of': '2026-11-21',
            'claims': [{
                'id': 'c3',
                'text': 'Ticket costs 50',
                'kind': 'price',
                'evidence': [{
                    'id': 'future_src',
                    'url': 'https://museum.example.org/tickets',
                    'source_type': 'official',
                    'verification_status': 'checked',
                    'evidence_depth': 'full_page',
                    'stance': 'support',
                    'published_at': '2026-11-21',
                    'retrieved_at': '2026-11-25',
                }],
            }],
        })
        c = res['claims'][0]
        self.assertEqual(c['verdict'], 'not_verified')
        self.assertEqual(c['future_dated_sources'], ['future_src'])

    def test_authority_must_belong_to_same_checked_directional_record(self):
        res = execute({
            'task': 'verify',
            'as_of': '2026-11-21',
            'claims': [{
                'id': 'c4',
                'text': 'Open late Friday',
                'kind': 'opening_hours',
                'evidence': [
                    {
                        'id': 'official_neutral',
                        'url': 'https://museum.example.org/home',
                        'source_type': 'official',
                        'verification_status': 'checked',
                        'evidence_depth': 'full_page',
                        'stance': 'neutral',
                        'verified_current_on_page': True,
                        'retrieved_at': '2026-11-21',
                    },
                    {
                        'id': 'unchecked_support',
                        'url': 'https://museum.example.org/blog',
                        'source_type': 'official',
                        'verification_status': 'unchecked',
                        'evidence_depth': 'full_page',
                        'stance': 'support',
                        'published_at': '2026-11-15',
                        'retrieved_at': '2026-11-21',
                    },
                ],
            }],
        })
        c = res['claims'][0]
        self.assertEqual(c['verdict'], 'not_verified')

    def test_official_full_page_contradiction_overrides_stale_blog(self):
        payload = json.loads((ROOT / 'examples/runtime-verify.json').read_text(encoding='utf-8'))
        res = execute(payload)
        c1, c2 = res['claims']
        self.assertEqual(c1['verdict'], 'contradicted_by_authoritative_source')
        self.assertEqual(c1['stale_published_sources'], ['old_blog_2023'])
        self.assertEqual(c2['verdict'], 'snippet_only_needs_full_page_check')


class CompareTests(unittest.TestCase):
    def test_fx_conversion_surcharges_and_package_isolation(self):
        payload = json.loads((ROOT / 'examples/runtime-compare.json').read_text(encoding='utf-8'))
        res = execute(payload)
        by_id = {o['id']: o for o in res['options']}
        # 42000 + 400 city tax = 42400 JPY * 0.048 = 2035.20 CNY
        self.assertAlmostEqual(by_id['hotel_shinjuku_a']['all_in_price'], 2035.20, places=2)
        self.assertTrue(by_id['hotel_shinjuku_a']['fx_converted'])
        self.assertEqual(by_id['hotel_shinjuku_a']['per_night_price'], 1017.60)
        self.assertEqual(by_id['hotel_shinjuku_a']['per_person_price'], 1017.60)
        # A and B share identical terms -> ranked together; C has no breakfast & non-refundable -> isolated!
        self.assertEqual(res['price_ranking_low_to_high'], ['hotel_shinjuku_a', 'hotel_shinjuku_b'])
        self.assertIn('hotel_shinjuku_c', res['not_comparable'])

    def test_missing_fx_rate_prevents_false_ranking(self):
        payload = json.loads((ROOT / 'examples/runtime-compare.json').read_text(encoding='utf-8'))
        payload['fx_rates'] = {}
        res = execute(payload)
        by_id = {o['id']: o for o in res['options']}
        self.assertIn('missing_fx_rate_JPY_to_CNY', by_id['hotel_shinjuku_a']['issues'])
        self.assertEqual(res['price_ranking_low_to_high'], [])

    def test_transport_different_baggage_isolated(self):
        def _t(oid, price, baggage):
            return {
                'id': oid,
                'name': oid,
                'quote': {
                    'departure_date': '2026-12-01',
                    'from': 'SHA',
                    'to': 'PEK',
                    'travelers': 1,
                    'currency': 'CNY',
                    'transport_mode': 'flight',
                    'departure_time': '09:00',
                    'arrival_time': '11:20',
                    'transfers': 0,
                    'route_pattern': 'direct',
                    'fare_class': 'economy',
                    'refund_policy': 'fee_applies',
                    'change_policy': 'fee_applies',
                    'baggage_allowance': baggage,
                    'all_in_price': price,
                    'price_basis': 'all_in_total',
                    'taxes_included': True,
                    'mandatory_fees_included': True,
                },
            }
        res = execute({'task': 'compare', 'kind': 'transport', 'options': [_t('a', 800, '20kg'), _t('b', 650, 'carry_on_only')]})
        self.assertEqual(res['price_ranking_low_to_high'], [])
        self.assertEqual(len(res['not_comparable']), 2)


class BudgetAndPassTests(unittest.TestCase):
    def test_balanced_budget_three_tiers_and_sum_check(self):
        payload = json.loads((ROOT / 'examples/runtime-budget.json').read_text(encoding='utf-8'))
        res = execute(payload)
        self.assertEqual(res['sum_check'], 8000.0)
        self.assertEqual(res['reserve'], 800.0)
        self.assertGreater(res['preference_adjusted']['food'], res['balanced_baseline']['food'])
        # Must not starve other categories
        self.assertGreater(res['preference_adjusted']['activities'], 0)
        self.assertIn('tight', res['scenarios'])
        self.assertIn('balanced', res['scenarios'])
        self.assertIn('upgraded', res['scenarios'])
        self.assertEqual(res['scenarios']['balanced']['per_person'], 2000.0)

    def test_pass_check_not_worth_it(self):
        payload = json.loads((ROOT / 'examples/runtime-pass-check.json').read_text(encoding='utf-8'))
        res = execute(payload)
        # Single fares = 3400 + 14170 + 4200 + 2400 = 24170
        # Pass effective = 26000 + 4960 + 2400 = 33360 -> lose 9190/pp
        self.assertEqual(res['verdict'], 'buy_point_to_point')
        self.assertEqual(res['per_person']['net_savings_with_pass'], -9190.0)
        self.assertEqual(res['group_total']['net_savings_with_pass'], -18380.0)

    def test_pass_check_worth_it_and_unverified_guard(self):
        res_worth = execute({
            'task': 'pass_check',
            'pass_name': 'City 2-Day Pass',
            'currency': 'JPY',
            'pass_price': 2000,
            'legs': [
                {'name': 'Trip 1', 'single_fare': 1200, 'verified': True},
                {'name': 'Trip 2', 'single_fare': 1400, 'verified': True},
            ],
        })
        self.assertEqual(res_worth['verdict'], 'worth_it')
        self.assertEqual(res_worth['per_person']['net_savings_with_pass'], 600.0)

        res_unv = execute({
            'task': 'pass_check',
            'pass_name': 'City Pass',
            'currency': 'JPY',
            'pass_price': 2000,
            'legs': [{'name': 'Trip 1', 'single_fare': 2600, 'verified': False}],
        })
        self.assertEqual(res_unv['verdict'], 'provisional_unverified_fares')


class AuditAndReviseTests(unittest.TestCase):
    def _valid_session(self):
        return {
            'version': 1,
            'currency': 'CNY',
            'total_budget': 2000,
            'costs_complete': True,
            'costs': {'hotel': {'amount': 800}, 'food': {'amount': 400}},
            'days': [
                {
                    'date': '2026-11-28',
                    'end_location_id': 'hotel_a',
                    'end_location_verified': True,
                    'stops': [
                        {
                            'id': 's1',
                            'name': 'Museum',
                            'start': '09:30',
                            'end': '11:30',
                            'opening_window': {'start': '09:00', 'end': '17:00', 'last_entry': '16:00'},
                            'opening_verified': True,
                            'decision_status': 'booked',
                        },
                        {
                            'id': 's2',
                            'name': 'Tea House',
                            'start': '12:30',
                            'end': '14:00',
                            'opening_window': {'start': '10:00', 'end': '20:00'},
                            'opening_verified': True,
                            'transfer_from_stop_id': 's1',
                            'transfer_from_previous_minutes': 25,
                            'transfer_source': 'map_route',
                            'decision_status': 'provisional',
                        },
                    ],
                },
                {
                    'date': '2026-11-29',
                    'start_location_id': 'hotel_a',
                    'start_location_verified': True,
                    'stops': [
                        {
                            'id': 's3',
                            'name': 'Park',
                            'start': '09:00',
                            'end': '11:00',
                            'opening_window': {'start': '07:00', 'end': '19:00'},
                            'opening_verified': True,
                            'decision_status': 'locked',
                        }
                    ],
                },
            ],
        }

    def test_audit_pass_and_last_entry_and_pace_warning(self):
        session = self._valid_session()
        res = execute({'task': 'audit', **session})
        self.assertEqual(res['overall_status'], 'pass')

        # Violate last_entry
        session['days'][0]['stops'][0]['start'] = '16:15'
        session['days'][0]['stops'][0]['end'] = '16:50'
        session['days'][0]['stops'].pop(1)
        res_late = execute({'task': 'audit', **session})
        codes = [i['code'] for i in res_late['days'][0]['issues']]
        self.assertIn('after_last_entry_time', codes)
        self.assertEqual(res_late['overall_status'], 'fail')

    def test_revise_protects_booked_item_and_allows_provisional_edit(self):
        session = self._valid_session()
        with self.assertRaises(InputError):
            execute({
                'task': 'revise',
                'session': session,
                'changes': [{'op': 'remove_stop', 'date': '2026-11-28', 'stop_id': 's1'}],
            })

        res = execute({
            'task': 'revise',
            'session': session,
            'changes': [{'op': 'update_stop', 'date': '2026-11-28', 'stop_id': 's2', 'fields': {'name': 'Quiet Tea House'}}],
        })
        self.assertEqual(res['session']['version'], 2)
        self.assertEqual(res['affected_days'], ['2026-11-28'])
        self.assertEqual(res['post_edit_audit']['overall_status'], 'pass')


class ExportAndCLITests(unittest.TestCase):
    def test_export_ics_preserves_unverified_prefix_and_rfc5545_structure(self):
        payload = json.loads((ROOT / 'examples/runtime-export-trip.json').read_text(encoding='utf-8'))
        payload['task'] = 'export_ics'
        res = execute(payload)
        ics = res['ics']
        self.assertIn('BEGIN:VCALENDAR', ics)
        self.assertIn('END:VCALENDAR', ics)
        self.assertEqual(res['event_count'], 2)
        self.assertIn('[估算]', ics)
        self.assertIn('TZID=Asia/Shanghai', ics)

    def test_export_html_escapes_xss_and_renders_trip_and_compare(self):
        payload = json.loads((ROOT / 'examples/runtime-export-trip.json').read_text(encoding='utf-8'))
        payload['title'] = '<script>alert("xss")</script>成都游'
        res = execute(payload)
        self.assertNotIn('<script>alert', res['html'])
        self.assertIn('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;', res['html'])
        self.assertIn('badge-ok', res['html'])
        self.assertIn('Plan B', res['html'])

        cmp_payload = {
            'task': 'export_html',
            'export_kind': 'compare',
            'lang': 'en',
            'title': 'Hotel Comparison',
            'bottom_line': 'Pick A for transit.',
            'options': [
                {'id': 'a', 'name': 'Hotel A', 'all_in_price': 200.0, 'currency': 'USD', 'evidence_status': 'verified'},
                {'id': 'b', 'name': 'Hotel B', 'all_in_price': 180.0, 'currency': 'USD', 'evidence_status': 'unverified'},
            ],
            'flip_conditions': ['Choose B only if non-refundable risk is acceptable.'],
        }
        cmp_res = execute(cmp_payload)
        self.assertIn('Hotel Comparison', cmp_res['html'])
        self.assertIn('Flip Conditions', cmp_res['html'])

    def test_cli_stdin_and_bilingual_markdown(self):
        sample = (ROOT / 'examples/runtime-pass-check.json').read_text(encoding='utf-8')
        proc_en = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/travel.py'), '--stdin', '--format', 'md', '--lang', 'en'],
            input=sample,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn('Buy point-to-point', proc_en.stdout)

        proc_zh = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/travel.py'), '--stdin', '--format', 'md', '--lang', 'zh'],
            input=sample,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn('建议单买更划算', proc_zh.stdout)


if __name__ == '__main__':
    unittest.main()
