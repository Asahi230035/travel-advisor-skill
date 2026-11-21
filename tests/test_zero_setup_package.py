"""Contract tests for the zero-configuration, stdlib-only skill package."""
import ast
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ZeroConfigContract(unittest.TestCase):
    def test_skill_descriptor_and_scope(self):
        text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\nname: travel-advisor\n'))
        self.assertIn('## Host tool contract', text)
        self.assertIn('already available', text)
        self.assertIn('Never rely on model memory', text)
        self.assertIn('smallest', (ROOT / 'references/task-routing-and-formats.md').read_text(encoding='utf-8'))
        self.assertIn('## Installation', (ROOT / 'README.md').read_text(encoding='utf-8'))
        self.assertIn('## What makes v2.0 different', (ROOT / 'README.md').read_text(encoding='utf-8'))

    def test_no_key_dependent_or_network_runtime(self):
        files = [*(ROOT / 'travel_core').glob('*.py'), *(ROOT / 'scripts').glob('*.py')]
        code = '\n'.join(p.read_text(encoding='utf-8') for p in files)
        for forbidden in ('AMAP_WEB_KEY', 'TRAVEL_CONTACT_EMAIL', 'getenv(', 'urllib.request', 'requests.', 'http.client', 'socket.'):
            self.assertNotIn(forbidden, code)

    def test_all_skill_reference_paths_exist(self):
        content = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        relative = re.findall(r'\]\((references/[^)]+|examples/[^)]+|docs/[^)]+)\)', content)
        self.assertGreaterEqual(len(relative), 7)
        for f in relative:
            with self.subTest(file=f):
                self.assertTrue((ROOT / f).is_file())

    def test_no_third_party_imports(self):
        allowed = {
            '__future__', 'argparse', 'copy', 'datetime', 'decimal', 'html',
            'json', 'math', 'pathlib', 're', 'sys', 'unittest', 'urllib',
        }
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
                        self.assertTrue(
                            module in allowed or module in {'travel_core', 'scripts'},
                            f'Unrecognized dependency {module} in {path}',
                        )


if __name__ == '__main__':
    unittest.main()
