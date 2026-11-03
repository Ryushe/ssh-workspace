import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'bin/ssh-workspace'


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = dict(os.environ, XDG_CONFIG_HOME=str(self.root / 'config'))
        self.fakebin = self.root / 'bin'
        self.fakebin.mkdir()
        self.env['PATH'] = str(self.fakebin) + os.pathsep + self.env['PATH']
        self.env['SSH_RECORD'] = str(self.root / 'ssh.json')
        ssh = self.fakebin / 'ssh'
        ssh.write_text('#!/usr/bin/env python3\nimport json,os,sys\n'
                       'open(os.environ["SSH_RECORD"],"w").write(json.dumps(sys.argv[1:]))\n'
                       'sys.exit(int(os.environ.get("SSH_EXIT",0)))\n')
        ssh.chmod(0o755)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(CLI), *args], env=self.env,
                              capture_output=True, text=True)

    def connect(self, *args, name='hoster'):
        return self.cli('connect', '--name', name, '--host', '192.0.2.10',
                        '--user', 'tester', '--key', '/tmp/a key', *args)

    def test_defaults_are_local_and_per_machine(self):
        self.assertEqual(self.connect('default').stdout.strip(), 'tmux')
        self.assertEqual(self.connect('default', 'herdr').returncode, 0)
        self.assertEqual(self.connect('default', 'nothing').stdout.strip(), 'herdr')
        self.assertEqual(self.connect('default', name='other').stdout.strip(), 'tmux')
        self.assertFalse(Path(self.env['SSH_RECORD']).exists())

    def test_override_does_not_change_default_and_returns_ssh_status(self):
        self.env['SSH_EXIT'] = '23'
        self.assertEqual(self.connect('herdr').returncode, 23)
        argv = json.loads(Path(self.env['SSH_RECORD']).read_text())
        self.assertIn('/tmp/a key', argv)
        self.assertIn('tester@192.0.2.10', argv)
        self.assertIn('attach herdr', argv[-1])
        self.assertEqual(self.connect('default').stdout.strip(), 'tmux')

    def test_generated_wrapper_quotes_and_forwards_arguments(self):
        key = str(self.root / "key ' $(touch SHOULD_NOT_EXIST)")
        generated = self.cli('generate', '--name', 'hoster', '--host', '192.0.2.10',
                             '--user', 'tester', '--key', key, '--launcher', str(CLI))
        self.assertEqual(generated.returncode, 0, generated.stderr)
        wrapper = self.root / 'ssh-hoster'
        wrapper.write_text(generated.stdout)
        result = subprocess.run(['bash', str(wrapper), 'herdr'], env=self.env,
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(key, json.loads(Path(self.env['SSH_RECORD']).read_text()))
        self.assertFalse((self.root / 'SHOULD_NOT_EXIST').exists())

    def test_agent_identity_without_key(self):
        result = self.cli('connect', '--name', 'agent', '--host', 'example.org',
                          '--user', 'tester', 'herdr')
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(Path(self.env['SSH_RECORD']).read_text())
        self.assertNotIn('-i', argv)

    def test_powershell_wrapper_forwards_arguments_and_quotes_values(self):
        import shutil
        if not shutil.which('pwsh'):
            self.skipTest('PowerShell unavailable')
        key = str(self.root / "key ' $(touch SHOULD_NOT_EXIST)")
        wrapper = self.root / 'ssh-hoster.ps1'
        generated = self.cli('generate', '--name', 'hoster', '--host', 'example.org',
                             '--user', 'tester', '--key', key, '--launcher', str(CLI),
                             '--format', 'powershell', '--output', str(wrapper))
        self.assertEqual(generated.returncode, 0, generated.stderr)
        result = subprocess.run(['pwsh', '-NoProfile', '-File', str(wrapper), 'herdr'],
                                env=self.env, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(key, json.loads(Path(self.env['SSH_RECORD']).read_text()))
        self.assertFalse((self.root / 'SHOULD_NOT_EXIST').exists())

    def test_invalid_default_is_rejected_without_changing_saved_value(self):
        self.connect('default', 'herdr')
        self.assertNotEqual(self.connect('default', 'bad').returncode, 0)
        self.assertEqual(self.connect('default').stdout.strip(), 'herdr')

    def test_invalid_name_and_option_host_rejected(self):
        for name, host in [('../escape', 'example.org'), ('valid', '-oProxyCommand=x')]:
            result = self.cli('generate', '--name', name, '--host=' + host,
                              '--user', 'tester', '--key', '/tmp/key')
            self.assertNotEqual(result.returncode, 0)

    def test_generator_resolves_relative_key_paths(self):
        result = self.cli('generate', '--name', 'example', '--host', 'example.org',
                          '--user', 'tester', '--key', './identity')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(Path.cwd() / 'identity'), result.stdout)


if __name__ == '__main__':
    unittest.main()
