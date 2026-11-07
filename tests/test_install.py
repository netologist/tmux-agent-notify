import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / 'install.py'


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = dict(os.environ, HOME=str(self.home), CLAUDE_CONFIG_DIR=str(self.home / 'claude'),
                        CODEX_HOME=str(self.home / 'codex'), XDG_CONFIG_HOME=str(self.home / 'xdg'))
        self.env.pop('PI_CODING_AGENT_DIR', None)

    def install(self, *args, check=True):
        return subprocess.run([sys.executable, str(INSTALL), *args], env=self.env,
                              text=True, capture_output=True, check=check)

    def test_existing_hooks_survive_install_and_uninstall(self):
        original = {'hooks': {'Stop': [{'hooks': [{'type': 'command', 'command': 'echo existing'}]}]},
                    'keep': {'value': 7}}
        paths = [self.home / 'claude/settings.json', self.home / 'codex/hooks.json']
        for path in paths:
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(original))
        self.install('install', 'claude', 'codex')
        self.install('install', 'claude', 'codex')
        for path in paths:
            data = json.loads(path.read_text())
            self.assertEqual(data['keep'], original['keep'])
            self.assertEqual(len(data['hooks']['Stop']), 2)
            self.assertEqual(data['hooks']['Stop'][0], original['hooks']['Stop'][0])
        self.install('uninstall', 'claude', 'codex')
        for path in paths:
            self.assertEqual(json.loads(path.read_text()), original)

    def test_modified_extension_is_never_overwritten_or_deleted(self):
        self.install('install', 'omp')
        path = self.home / '.omp/agent/extensions/tmux-agent-notify.ts'
        path.write_text('user-owned content')
        for action in ('install', 'uninstall'):
            result = self.install(action, 'omp', check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_text(), 'user-owned content')


if __name__ == '__main__':
    unittest.main()
