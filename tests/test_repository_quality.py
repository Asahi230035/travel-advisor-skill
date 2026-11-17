"""Repo-release checks that catch broken docs and metadata."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RepositoryQuality(unittest.TestCase):
    def test_descriptor_and_readmes(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(skill.startswith('---\nname: travel-advisor\n'))
        self.assertIn('description:', skill)
        self.assertIn('Works with the host agent', skill)
        self.assertIn('itinerary-planning.md', skill)
        self.assertTrue((ROOT / 'README.zh-CN.md').exists())
        self.assertTrue((ROOT / 'LICENSE').exists())

    def test_relative_markdown_links_exist(self):
        docs = [ROOT / 'SKILL.md', ROOT / 'README.md', ROOT / 'README.zh-CN.md',
                *(ROOT / 'references').glob('*.md'), *(ROOT / 'docs').glob('*.md')]
        pattern = re.compile(r'(?<!!)\[[^]]+\]\(([^)#]+)(?:#[^)]*)?\)')
        for document in docs:
            for link in pattern.findall(document.read_text(encoding='utf-8')):
                if ':' in link or link.startswith('#'):
                    continue
                with self.subTest(document=document.name, link=link):
                    self.assertTrue((document.parent / link).exists())

    def test_no_accidental_runtime_secrets(self):
        from travel_core.engine import capabilities
        data = capabilities()
        self.assertFalse(data['api_keys_required'])
        self.assertEqual(data['pip_dependencies'], [])
