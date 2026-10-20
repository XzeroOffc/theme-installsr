import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('installer', Path(__file__).with_name('install.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MergeTests(unittest.TestCase):
    def test_transformer_preserves_current_api(self):
        with tempfile.TemporaryDirectory() as temp:
            panel = Path(temp)
            php = 'app/Transformers/Api/Client/ServerTransformer.php'
            ts = 'resources/scripts/api/server/getServer.ts'
            sources = {
                php: "<?php\nreturn [\n 'server_identifier' => $server->identifier,\n 'is_node_under_maintenance' => $server->node->maintenance_mode,\n 'skip_scripts' => $server->skip_scripts,\n];\n",
                ts: 'interface Server {\n    isNodeUnderMaintenance: boolean;\n    skipScripts: boolean;\n}\nconst s = {\n    isNodeUnderMaintenance: data.is_node_under_maintenance,\n    skipScripts: data.skip_scripts,\n};\n',
                'resources/scripts/index.tsx': "import './i18n';\nimport './Pterodactyl_Nightcore_Theme.css';\nstart();\n",
            }
            for path, text in sources.items():
                m.write_data(panel / path, text.encode())
            out = m.merge_source('noobe', {php: b'old', ts: b'old'}, panel)
            self.assertIn(b"'server_identifier'", out[php])
            self.assertIn(b"'skip_scripts'", out[php])
            self.assertIn(b"'nest_id'", out[php])
            self.assertIn(b"'egg_id'", out[php])
            self.assertIn(b'skipScripts', out[ts])
            self.assertNotIn(b'Nightcore', out['resources/scripts/index.tsx'])
            for path, data in out.items():
                m.write_data(panel / path, data)
            self.assertEqual(out, m.merge_source('noobe', out.copy(), panel))

    def test_ice_console_keeps_unicode_support(self):
        with tempfile.TemporaryDirectory() as temp:
            panel = Path(temp)
            path = 'resources/scripts/components/server/console/Console.tsx'
            m.write_data(panel / path, b"import { Unicode11Addon } from 'xterm-addon-unicode11';\nconst theme = {\n    background: th`colors.black`.toString(),\n};\nterminal.loadAddon(unicode11Addon);\n")
            m.write_data(panel / 'resources/scripts/index.tsx', b"import './i18n';\n")
            m.write_data(panel / 'package.json', b'{}')
            m.write_data(panel / 'routes/admin.php', b'<?php')
            m.write_data(panel / 'resources/views/layouts/admin.blade.php', b'<head></head><ul class="sidebar-menu"></ul>')
            m.write_data(panel / 'resources/views/templates/wrapper.blade.php', b'<head></head>')
            m.write_data(panel / 'resources/scripts/components/dashboard/DashboardContainer.tsx', b'<PageContentBlock></PageContentBlock>')
            theme = next(t for t in m.CATALOG if t['name'] == 'iceMinecraft')
            plan = m.source_plan(theme, m.payload(theme), panel)
            self.assertIn(b"background: '#111F26'", plan[path])
            self.assertIn(b'Unicode11Addon', plan[path])
            self.assertIn(b'terminal.loadAddon(unicode11Addon)', plan[path])

    def test_switch_uses_baseline_and_rejects_manual_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            panel = Path(temp) / 'panel'
            panel.mkdir()
            (panel / 'artisan').write_text('php')
            path = 'resources/scripts/a.tsx'
            m.write_data(panel / path, b'custom base')
            backup = Path(temp) / 'backups'
            backup.mkdir()
            def plan(theme, files, baseline):
                self.assertEqual((baseline / path).read_bytes(), b'custom base')
                return {path: theme['name'].encode(), 'resources/scripts/only-first.ts': b'first'} if theme['name'] == 'nightcore' else {path: b'second'}
            with patch.object(m, 'source_plan', side_effect=plan), patch.object(m, 'stage_build', side_effect=lambda p, plan, s: plan), patch.object(m, 'run'):
                m.install_source({'name': 'nightcore'}, {}, panel, backup)
                m.install_source({'name': 'frostcore'}, {}, panel, backup)
                self.assertFalse((panel / 'resources/scripts/only-first.ts').exists())
                self.assertEqual((panel / path).read_bytes(), b'second')
                (panel / path).write_text('user edit')
                with self.assertRaisesRegex(RuntimeError, 'File diubah'):
                    m.install_source({'name': 'nightcore'}, {}, panel, backup)
                self.assertEqual((panel / path).read_text(), 'user edit')

    def test_failed_deploy_restores_files_and_state(self):
        with tempfile.TemporaryDirectory() as temp:
            panel = Path(temp) / 'panel'; panel.mkdir()
            (panel / 'artisan').write_text('php')
            m.write_data(panel / 'resources/a.ts', b'original')
            backup = Path(temp) / 'backups'; backup.mkdir()
            def fail_cache(args, *a, **kw):
                if 'view:cache' in args:
                    raise RuntimeError('cache failed')
            with patch.object(m, 'source_plan', return_value={'resources/a.ts': b'new', 'resources/new.ts': b'new'}), patch.object(m, 'stage_build', side_effect=lambda p, plan, s: plan), patch.object(m, 'run', side_effect=fail_cache):
                with self.assertRaisesRegex(RuntimeError, 'cache failed'):
                    m.install_source({'name': 'nightcore'}, {}, panel, backup)
            self.assertEqual((panel / 'resources/a.ts').read_bytes(), b'original')
            self.assertFalse((panel / 'resources/new.ts').exists())
            self.assertFalse((panel / m.STATE).exists())


if __name__ == '__main__':
    unittest.main()
