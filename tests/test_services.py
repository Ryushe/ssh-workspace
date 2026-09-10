import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import types
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / 'bin/ssh-workspace'
loader = importlib.machinery.SourceFileLoader('workspace', str(path))
spec = importlib.util.spec_from_loader(loader.name, loader)
workspace = importlib.util.module_from_spec(spec)
loader.exec_module(workspace)


class ServiceTests(unittest.TestCase):
    def args(self):
        return types.SimpleNamespace(backend='herdr', tmux_wrapper=None, check=True)

    @patch.object(workspace, 'remote_environment')
    def test_existing_service_is_not_restarted(self, env):
        with patch.object(workspace, 'run', return_value=subprocess.CompletedProcess([], 0)), \
             patch.object(workspace, 'ready', return_value=True), \
             patch.object(workspace, 'verify_owner'), \
             patch.object(workspace, 'verify_backend_owner', create=True), \
             patch.object(workspace, 'checked') as checked:
            workspace.attach(self.args())
        self.assertEqual(checked.call_args_list[0].args[0], ['systemctl', '--user', 'show-environment'])
        self.assertEqual(checked.call_count, 1)

    @patch.object(workspace, 'remote_environment')
    def test_unmanaged_server_is_not_claimed(self, env):
        with patch.object(workspace, 'run', return_value=subprocess.CompletedProcess([], 3)), \
             patch.object(workspace, 'ready', return_value=True), \
             patch.object(workspace, 'checked') as checked:
            with self.assertRaisesRegex(ValueError, 'already exists outside'):
                workspace.attach(self.args())
        self.assertEqual(checked.call_count, 1)

    @patch.object(workspace, 'remote_environment')
    def test_failed_service_start_is_diagnosable(self, env):
        with patch.object(workspace, 'run', return_value=subprocess.CompletedProcess([], 3)), \
             patch.object(workspace, 'ready', return_value=False), \
             patch.object(workspace, 'checked', side_effect=['', ValueError('start failed: no unit')]):
            with self.assertRaisesRegex(ValueError, 'start failed: no unit'):
                workspace.attach(self.args())

    def test_ssh_owned_service_is_rejected(self):
        with patch.object(workspace, 'checked', return_value='/system.slice/ssh.service'):
            with self.assertRaisesRegex(ValueError, 'unexpected ControlGroup'):
                workspace.verify_owner('ssh-workspace-herdr.service')

    def test_backend_process_must_belong_to_selected_unit(self):
        with patch.object(workspace, 'backend_pid', return_value=123, create=True), \
             patch.object(Path, 'read_text', return_value='0::/system.slice/ssh.service\n'):
            self.assertTrue(hasattr(workspace, 'verify_backend_owner'))
            with self.assertRaisesRegex(ValueError, 'does not belong'):
                workspace.verify_backend_owner('herdr', 'ssh-workspace-herdr.service')

    @patch.object(workspace, 'remote_environment')
    def test_inactive_service_starts_then_client_only_executes(self, env):
        args = self.args()
        args.check = False
        inactive = subprocess.CompletedProcess([], 3)
        active = subprocess.CompletedProcess([], 0)
        with patch.object(workspace, 'run', side_effect=[inactive, active]), \
             patch.object(workspace, 'ready', side_effect=[False, True]), \
             patch.object(workspace, 'verify_owner'), \
             patch.object(workspace, 'verify_backend_owner', create=True), \
             patch.object(workspace, 'backend_command', return_value=['/bin/herdr', '--session', 'ssh-workspace']), \
             patch.object(workspace, 'checked') as checked, \
             patch.object(workspace.os, 'execv', side_effect=SystemExit) as execute:
            with self.assertRaises(SystemExit):
                workspace.attach(args)
        self.assertIn(unittest.mock.call(['systemctl', '--user', 'start', 'ssh-workspace-herdr.service']), checked.call_args_list)
        self.assertEqual(execute.call_args.args[1], ['/bin/herdr', '--session', 'ssh-workspace', 'client'])

    @patch.object(workspace, 'remote_environment')
    def test_readiness_timeout_does_not_restart(self, env):
        with patch.object(workspace, 'run', return_value=subprocess.CompletedProcess([], 0)), \
             patch.object(workspace, 'ready', return_value=False), \
             patch.object(workspace.time, 'sleep'), \
             patch.object(workspace, 'checked') as checked:
            with self.assertRaisesRegex(ValueError, 'did not become ready'):
                workspace.attach(self.args())
        self.assertEqual(checked.call_count, 1)


if __name__ == '__main__':
    unittest.main()
