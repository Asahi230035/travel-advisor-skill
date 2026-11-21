"""Repo-release checks that catch broken docs, invalid JSON fixtures, and metadata drift."""
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class RepositoryQuality(unittest.TestCase):
    def test_descriptor_and_readmes(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(skill.startswith('---\nname: travel-advisor\n'))
        self.assertIn('description:', skill)
        self.assertIn('version: "2.0.0"', skill)
        self.assertIn('Works with the host agent', skill)
        self.assertIn('itinerary-and-pacing.md', skill)
        self.assertIn('research-and-evidence.md', skill)
        self.assertTrue((ROOT / 'README.zh-CN.md').exists())
        self.assertTrue((ROOT / 'LICENSE').exists())

    def test_relative_markdown_links_exist(self):
        docs = [
            ROOT / 'SKILL.md',
            ROOT / 'README.md',
            ROOT / 'README.zh-CN.md',
            *(ROOT / 'references').glob('*.md'),
            *(ROOT / 'docs').glob('*.md'),
        ]
        pattern = re.compile(r'(?<!!)\[[^]]+\]\(([^)#]+)(?:#[^)]*)?\)')
        for document in docs:
            for link in pattern.findall(document.read_text(encoding='utf-8')):
                if ':' in link or link.startswith('#'):
                    continue
                with self.subTest(document=document.name, link=link):
                    self.assertTrue((document.parent / link).exists(), f'Broken link {link} in {document}')

    def test_all_json_fixtures_and_schemas_parse(self):
        for folder in ('examples', 'schemas'):
            for path in (ROOT / folder).glob('*.json'):
                with self.subTest(file=str(path.relative_to(ROOT))):
                    json.loads(path.read_text(encoding='utf-8'))

    def test_no_accidental_runtime_secrets(self):
        from travel_core.engine import capabilities
        data = capabilities()
        self.assertEqual(data['version'], '2.0.0')
        self.assertFalse(data['api_keys_required'])
        self.assertEqual(data['pip_dependencies'], [])


if __name__ == '__main__':
    unittest.main()
