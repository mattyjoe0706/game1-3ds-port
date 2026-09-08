"""Build orchestration tests use mocked compilers; they are not native builds."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_native
import build_container


class BuildTests(unittest.TestCase):
    def setup_dkp(self,root):
        dkp=root/'devkit prefix'
        for name in ['include/3ds.h','include/citro2d.h','include/citro3d.h','lib/libctru.a','lib/libcitro2d.a','lib/libcitro3d.a']:
            p=dkp/'libctru'/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b'fixture')
        return dkp

    def test_missing_explicit_makerom_does_not_fall_back(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); dkp=self.setup_dkp(root)
            with patch.object(sys,'argv',['build','--devkitpro',str(dkp),'--check','--cia','--makerom',str(root/'missing')]), \
                 patch.object(build_native,'executable',return_value='mock-tool'), contextlib.redirect_stdout(io.StringIO()) as log:
                self.assertEqual(build_native.main(),2)
                self.assertIn('makerom',log.getvalue())

    def test_stale_output_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); dkp=self.setup_dkp(root); out=root/'out'; out.mkdir(); (out/'old.elf').write_bytes(b'old')
            with patch.object(sys,'argv',['build','--devkitpro',str(dkp),'--output',str(out)]), \
                 patch.object(build_native,'executable',return_value='mock-tool'), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(build_native.main(),2)
                self.assertEqual((out/'old.elf').read_bytes(),b'old')

    def test_failure_is_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); dkp=self.setup_dkp(root); out=root/'out'
            with patch.object(sys,'argv',['build','--devkitpro',str(dkp),'--output',str(out)]), \
                 patch.object(build_native,'executable',return_value='mock-tool'), \
                 patch.object(build_native.subprocess,'run',return_value=subprocess.CompletedProcess([],7)):
                with self.assertRaises(subprocess.CalledProcessError): build_native.main()
            report=json.loads((out/'build-report.json').read_text())
            self.assertEqual(report['status'],'failed'); self.assertEqual(report['exit_code'],7)
            self.assertFalse(report['hardware_tested'])

    def test_command_paths_are_not_shell_strings(self):
        args=build_container.command('docker','sha256:example',Path('/src with spaces'),Path('/out with spaces'))
        self.assertIn(f'type=bind,src={Path("/src with spaces")},dst=/src,readonly',args)
        self.assertIn('none',args); self.assertIn('--read-only',args)
        self.assertNotIn('--privileged',args); self.assertNotIn('--cia',args)

    def test_cia_mount_and_arguments(self):
        args=build_container.command('docker','image',Path('/src'),Path('/out'),Path('/host/makerom'))
        self.assertIn(f'type=bind,src={Path("/host/makerom")},dst=/tool/makerom,readonly',args)
        self.assertEqual(args[-3:],['--cia','--makerom','/tool/makerom'])

    def test_docker_absence_is_explicit(self):
        with patch.object(sys,'argv',['build-container']),patch.object(build_container.shutil,'which',return_value=None), \
             contextlib.redirect_stdout(io.StringIO()) as log:
            self.assertEqual(build_container.main(),2)
            self.assertIn('Docker CLI not found',log.getvalue())


if __name__=='__main__': unittest.main()
