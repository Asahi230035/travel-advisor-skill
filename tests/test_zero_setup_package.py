"""Contract tests for the user-facing zero-configuration skill."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ZeroConfigContract(unittest.TestCase):
    def test_skill_descriptor_and_scope(self):
        text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\nname: travel-advisor\n'))
        self.assertIn('## Tool usage', text)
        self.assertIn('already available', text)
        self.assertIn('smallest', (ROOT / 'references/task-routing.md').read_text(encoding='utf-8'))
        self.assertIn('## Installation', (ROOT / 'README.md').read_text(encoding='utf-8'))
        self.assertIn('## Features', (ROOT / 'README.md').read_text(encoding='utf-8'))

    def test_no_key_dependent_runtime(self):
        code = '\n'.join(p.read_text(encoding='utf-8') for p in (ROOT / 'travel_core').glob('*.py'))
        for forbidden in ('AMAP_WEB_KEY', 'TRAVEL_CONTACT_EMAIL', 'getenv(', 'urllib.request', 'requests.'):
            self.assertNotIn(forbidden, code)

    def test_all_skill_reference_paths_exist(self):
        import re
        content = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        relative = re.findall(r'\]\((references/[^)]+|examples/[^)]+|docs/[^)]+)\)', content)
        self.assertGreaterEqual(len(relative), 6)
        for f in relative:
            with self.subTest(file=f):
                self.assertTrue((ROOT / f).is_file())

    def test_no_third_party_imports(self):
        # Imports in runnable Python are stdlib or local packages only.
        import ast
        allowed = {'__future__', 'argparse', 'copy', 'datetime', 'decimal', 'difflib',
                   'json', 'math', 'os', 'pathlib', 're', 'sys', 'unittest', 'urllib',
                   'statistics', 'collections', 'typing', 'hashlib', 'itertools', 'unicodedata', 'score_plans'}
        for path in [*(ROOT / 'travel_core').glob('*.py'), *(ROOT / 'scripts').glob('*.py')]:
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [x.name.split('.')[0] for x in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    modules = [node.module.split('.')[0]] if node.module else []
                else:
                    continue
                for module in modules:
                    with self.subTest(file=path.name, module=module):
                        self.assertTrue(module in allowed or module in {'travel_core', 'scripts'},
                                        f'Unrecognized dependency {module} in {path}')
