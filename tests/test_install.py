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
        self.env.pop('COPILOT_HOME', None)
        self.env.pop('GEMINI_CLI_HOME', None)

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

    def test_modified_notifier_is_not_overwritten(self):
        self.install('install', 'omp')
        path = self.home / '.config/tmux/agent-notify/notify.sh'
        path.write_text('custom notifier')
        result = self.install('install', 'copilot', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_text(), 'custom notifier')

    def test_gemini_and_agy_preserve_other_hooks(self):
        gemini = self.home / '.gemini/settings.json'
        agy = self.home / '.gemini/config/hooks.json'
        gemini.parent.mkdir(parents=True)
        agy.parent.mkdir(parents=True)
        original_gemini = {'hooks': {'AfterAgent': [{'hooks': [{'type': 'command', 'command': 'echo existing'}]}]}}
        original_agy = {'existing': {'Stop': [{'type': 'command', 'command': 'echo existing'}]}}
        gemini.write_text(json.dumps(original_gemini))
        agy.write_text(json.dumps(original_agy))
        self.install('install', 'gemini', 'agy')
        self.install('install', 'gemini', 'agy')
        data = json.loads(gemini.read_text())
        self.assertEqual(data['hooks']['AfterAgent'][0], original_gemini['hooks']['AfterAgent'][0])
        self.assertEqual(len(data['hooks']['AfterAgent']), 2)
        self.assertEqual(json.loads(agy.read_text())['existing'], original_agy['existing'])
        self.install('uninstall', 'gemini', 'agy')
        self.assertEqual(json.loads(gemini.read_text()), original_gemini)
        self.assertEqual(json.loads(agy.read_text()), original_agy)

    def test_gemini_custom_home_is_used_without_touching_default(self):
        self.env['GEMINI_CLI_HOME'] = str(self.home / 'alternate')
        self.install('install', 'gemini')
        self.assertTrue((self.home / 'alternate/.gemini/settings.json').is_file())
        self.assertFalse((self.home / '.gemini/settings.json').exists())
        self.install('uninstall', 'gemini')

    def test_copilot_preserves_unrelated_and_modified_hooks(self):
        hooks = self.home / '.copilot/hooks'
        hooks.mkdir(parents=True)
        unrelated = hooks / 'existing.json'
        unrelated.write_text('unchanged')
        self.install('install', 'copilot')
        self.install('install', 'copilot')
        managed = hooks / 'tmux-agent-notify.json'
        managed.write_text('user modifications')
        for action in ('install', 'uninstall'):
            result = self.install(action, 'copilot', check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(managed.read_text(), 'user modifications')
            self.assertEqual(unrelated.read_text(), 'unchanged')


if __name__ == '__main__':
    unittest.main()
