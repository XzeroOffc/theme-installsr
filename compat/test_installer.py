import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location('installer', Path(__file__).with_name('install.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.panel = Path(self.temp.name) / 'panel'
        (self.panel / 'resources/scripts').mkdir(parents=True)
        (self.panel / 'resources/views/layouts').mkdir(parents=True)
        (self.panel / 'resources/views/layouts/admin.blade.php').write_text('<html><head></head><aside class="main-sidebar"><ul class="sidebar-menu">Store and Protection</ul></aside></html>')
        (self.panel / 'routes').mkdir()
        (self.panel / 'routes/admin.php').write_text('<?php\n')
        (self.panel / 'resources/views/templates').mkdir()
        (self.panel / 'resources/views/templates/wrapper.blade.php').write_text('<html><head></head></html>')
        (self.panel / 'resources/scripts/components/dashboard').mkdir(parents=True)
        (self.panel / 'resources/scripts/components/dashboard/DashboardContainer.tsx').write_text("const A = () => <PageContentBlock title={'Dashboard'}></PageContentBlock>;")
        self.entry = self.panel / 'resources/scripts/index.tsx'
        self.entry.write_text("import './i18n';\n// Preserve bootstrap\nstartPanel();\n")
        (self.panel / 'package.json').write_text(json.dumps({'dependencies': {'axios': '^1.13.2'}, 'scripts': {'build:production': 'original'}}))
    def tearDown(self):
        self.temp.cleanup()
    def theme(self, name):
        return next(t for t in m.CATALOG if t['name'] == name)
    def test_manifest_flat_nested_and_query(self):
        assets = self.panel / 'public/assets'
        assets.mkdir(parents=True)
        (assets / 'bundle.abc.js').write_text('console.log(1)')
        for manifest in (
            {'bundle.js': '/assets/bundle.abc.js'},
            {'bundle.js': {'src': '/assets/bundle.abc.js', 'integrity': 'sha384-test'}},
            {'entrypoints': {'main': {'assets': {'js': ['https://cdn.example/assets/bundle.abc.js?v=2']}}}},
        ):
            m.validate_manifest(manifest, assets)
    def test_manifest_rejects_missing_empty_and_traversal(self):
        assets = self.panel / 'public/assets'
        assets.mkdir(parents=True)
        (assets / 'empty.js').touch()
        for manifest in ({}, {'css': 'style.css'}, {'js': '/assets/missing.js'},
                         {'js': '/assets/empty.js'}, {'js': '/assets/../escape.js'}):
            with self.assertRaises(RuntimeError):
                m.validate_manifest(manifest, assets)
    def test_all_original_archives_match(self):
        self.assertEqual(len(m.CATALOG), 18)
        for t in m.CATALOG:
            self.assertTrue(m.payload(t))
    def test_css_switch_preserves_bootstrap_and_removes_previous_import(self):
        t = self.theme('nightcore')
        self.entry.write_text(self.entry.read_text() + "import './IceMinecraftTheme.css';\nimport './theme-installsr-compat.css';\n")
        plan = m.source_plan(t, m.payload(t), self.panel)
        s = plan['resources/scripts/index.tsx'].decode()
        self.assertIn('startPanel();', s)
        self.assertNotIn('IceMinecraftTheme.css', s)
        self.assertNotIn('theme-installsr-compat.css', s)
        self.assertEqual(s.count('Pterodactyl_Nightcore_Theme.css'), 1)
        self.entry.write_text(s)
        second = m.source_plan(t, m.payload(t), self.panel)
        self.assertEqual(second['resources/scripts/index.tsx'], plan['resources/scripts/index.tsx'])
    def test_old_package_does_not_downgrade(self):
        t = self.theme('nook')
        plan = m.source_plan(t, m.payload(t), self.panel)
        pkg = json.loads(plan['package.json'])
        self.assertEqual(pkg['dependencies']['axios'], '^1.13.2')
        self.assertEqual(pkg['scripts']['build:production'], 'original')
        self.assertNotIn('webpack.config.js', plan)
        self.assertNotIn('config/app.php', plan)
        self.assertFalse(any(p.startswith('public/assets/') for p in plan))
    def test_zip_traversal_rejected(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as z:
            z.writestr('../escape', 'x')
        with zipfile.ZipFile(io.BytesIO(data.getvalue())) as z:
            with self.assertRaises(RuntimeError):
                dict(m.members(z))
    def test_target_symlink_escape_rejected(self):
        (self.panel / 'resources/scripts/Pterodactyl_Nightcore_Theme.css').symlink_to(Path(self.temp.name) / 'outside')
        t = self.theme('nightcore')
        with self.assertRaises(RuntimeError):
            m.source_plan(t, m.payload(t), self.panel)
    def test_restore_existing_and_new_files(self):
        backup = Path(self.temp.name) / 'backup'
        m.snapshot(self.panel, ['resources/scripts/index.tsx', 'new.css'], backup)
        original = self.entry.read_bytes()
        self.entry.write_text('broken')
        (self.panel / 'new.css').write_text('new')
        with patch.object(m, 'run'):
            m.restore(self.panel, backup)
        self.assertEqual(self.entry.read_bytes(), original)
        self.assertFalse((self.panel / 'new.css').exists())
    def test_build_failure_never_modifies_live_panel(self):
        t = self.theme('nightcore')
        before = self.entry.read_bytes()
        with patch.object(m, 'stage_build', side_effect=RuntimeError('build failed')):
            with self.assertRaises(RuntimeError):
                m.install_source(t, m.payload(t), self.panel, Path(self.temp.name))
        self.assertEqual(self.entry.read_bytes(), before)
    def test_billing_stops_before_writes(self):
        t = self.theme('billing')
        with self.assertRaisesRegex(RuntimeError, 'bukan tema mandiri'):
            m.install_source(t, m.payload(t), self.panel, Path(self.temp.name))
    def test_ice_uses_original_css_and_compat_overlay(self):
        t = self.theme('iceMinecraft')
        files = m.payload(t)
        plan = m.source_plan(t, files, self.panel)
        self.assertEqual(plan['resources/scripts/IceMinecraftTheme.css'], files['pterodactyl/resources/scripts/IceMinecraftTheme.css'])
        self.assertIn('resources/scripts/theme-installsr-compat.css', plan)
        self.assertNotIn('resources/scripts/components/server/console/Console.tsx', plan)

if __name__ == '__main__':
    unittest.main()
