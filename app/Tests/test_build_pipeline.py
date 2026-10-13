"""Asset-free regressions for partial shader builds and rejected input packages."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1] / 'Scripts'


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class BuildPipelineTests(unittest.TestCase):
    def shader_fixture(self, folder):
        shaders = folder / 'shaders'
        shaders.mkdir()
        (shaders / 'index.json').write_text(json.dumps({
            'first': {'ok': True, 'stage': 'vs'}, 'second': {'ok': True, 'stage': 'ps'}}))
        tool = folder / 'translator'
        tool.touch()
        return shaders, tool

    def test_prebuilt_translator_success_cannot_hide_missing_shader(self):
        build = module('build_metal_shaders')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shaders, tool = self.shader_fixture(root)

            def translator(command, **kwargs):
                Path(command[-1]).write_text('{"h":"first"}\n')
                return subprocess.CompletedProcess(command, 0, '', 'translated 1, failed 1')

            with patch.object(build, 'WORK', str(root / 'work')), patch.object(build, 'OUT', str(root / 'out')), \
                 patch.dict(build.os.environ, {'PGMSL': str(tool)}), \
                 patch.object(build.subprocess, 'run', side_effect=translator) as calls, \
                 patch('sys.argv', ['build_metal_shaders.py', str(shaders), '--sdk', 'iphoneos']):
                with self.assertRaisesRegex(SystemExit, 'translation is incomplete'):
                    build.main()
                self.assertEqual(calls.call_count, 1)

    def test_compile_failure_cannot_link_stale_air(self):
        build = module('build_metal_shaders')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shaders, tool = self.shader_fixture(root)

            def process(command, **kwargs):
                if command[0] == str(tool):
                    Path(command[-1]).write_text('{"h":"first"}\n{"h":"second"}\n')
                    return subprocess.CompletedProcess(command, 0, '', '')
                return subprocess.CompletedProcess(command, 0, '/fake/metal\n', '')

            with patch.object(build, 'WORK', str(root / 'work')), patch.object(build, 'OUT', str(root / 'out')), \
                 patch.dict(build.os.environ, {'PGMSL': str(tool)}), \
                 patch.object(build.subprocess, 'run', side_effect=process), \
                 patch.object(build, 'compile_batch', side_effect=RuntimeError('controlled compiler error')), \
                 patch.object(build, 'run') as link, \
                 patch('sys.argv', ['build_metal_shaders.py', str(shaders), '--sdk', 'iphoneos']):
                with self.assertRaisesRegex(SystemExit, 'refusing to link a partial library'):
                    build.main()
                link.assert_not_called()

    def test_wrong_engine_is_rejected_before_upload(self):
        inputs = module('minimal_inputs')
        with self.assertRaisesRegex(ValueError, 'game.wasm does not match'):
            inputs.required_files(b'not an engine', b'{}', b'{}')

    def test_arbitrary_zip_is_not_an_ipa(self):
        verifier = module('verify_ipa')
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'invalid.zip'
            with zipfile.ZipFile(archive, 'w') as package:
                package.writestr('readme.txt', 'This is a negative test fixture, not an app.')
            with self.assertRaisesRegex(ValueError, 'exactly one Payload'):
                verifier.verify(archive)


if __name__ == '__main__':
    unittest.main()
