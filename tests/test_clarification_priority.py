import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from clarification_priority import select_questions


class ClarificationTests(unittest.TestCase):
    def test_missing_budget_outweighs_optional_preference(self):
        data = {'candidates': [
            {'key': 'budget', 'question': '预算多少、人均还是总额？', 'impact': 5, 'blocking': True},
            {'key': 'pace', 'question': '喜欢慢节奏吗？', 'impact': 2, 'defaultable': True},
        ]}
        result = select_questions(data)
        self.assertEqual(result['questions'][0]['field'], 'budget')
        self.assertFalse(result['may_proceed_provisionally'])

    def test_skips_already_asked(self):
        data = {'candidates': [
            {'key': 'budget', 'question': '预算？', 'impact': 5, 'blocking': True, 'already_asked': True},
            {'key': 'food', 'question': '爱吃什么？', 'impact': 3}
        ]}
        self.assertEqual(select_questions(data)['questions'][0]['field'], 'food')

    def test_defaultable_low_impact_is_skipped(self):
        res = select_questions({'candidates': [
            {'key': 'hotel_brand', 'question': '品牌？', 'impact': 1, 'defaultable': True}
        ]})
        self.assertEqual(res['questions'], [])
        self.assertTrue(res['may_proceed_provisionally'])

    def test_previously_asked_unresolved_blocker_remains_blocker(self):
        data = {'candidates': [
            {'key': 'budget', 'question': '预算？', 'impact': 5, 'blocking': True, 'already_asked': True},
        ]}
        result = select_questions(data)
        self.assertEqual(result['questions'], [])
        self.assertFalse(result['may_proceed_provisionally'])

    def test_no_question_overflow(self):
        cs = [{'key': str(i), 'question': 'Q', 'impact': 3} for i in range(5)]
        self.assertEqual(len(select_questions({'candidates': cs, 'max_questions': 2})['questions']), 2)


if __name__ == '__main__':
    unittest.main()
