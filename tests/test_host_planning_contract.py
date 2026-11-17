import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from travel_core.engine import execute

class HostPlanningContractTests(unittest.TestCase):
    def test_plan_has_no_offline_generator(self):
        capabilities=execute({'task':'capabilities'})
        self.assertNotIn('plan',capabilities['offline'])
        self.assertIn('plan',capabilities['host_agent_workflows'])
        response=execute({'task':'plan','destination':'Chengdu'})
        self.assertEqual(response['status'],'host_agent_planning_required')
        self.assertFalse(response['automatic_offline_planning'])

    def test_reference_instructions_exist(self):
        skill=(ROOT/'SKILL.md').read_text(encoding='utf-8')
        guide=ROOT/'references/itinerary-planning.md'
        self.assertIn('itinerary-planning.md',skill)
        self.assertTrue(guide.exists())
        content=guide.read_text(encoding='utf-8')
        self.assertIn('host agent',content.lower())
        self.assertIn('opening',content.lower())
        self.assertIn('route',content.lower())

    def test_no_social_platform_specific_module(self):
        for rel in ('SKILL.md','README.md','README.zh-CN.md'):
            content=(ROOT/rel).read_text(encoding='utf-8').lower()
            self.assertNotIn('xiaohongshu',content)
            self.assertNotIn('social platform',content)
            self.assertNotIn('小红书',content)
        self.assertFalse((ROOT/'references/social-discovery.md').exists())
