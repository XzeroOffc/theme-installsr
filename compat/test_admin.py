import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('theme_admin', Path(__file__).with_name('admin.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AdminThemeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.panel = Path(self.temp.name)
        fixtures = {
            'routes/admin.php': "<?php\nrequire base_path('routes/zeronex-store-admin.php');\n",
            'resources/views/layouts/admin.blade.php': '<head></head><ul class="sidebar-menu">@include(\'admin.zeronex-protection.menu\')</ul>',
            'resources/views/templates/wrapper.blade.php': '<head></head>',
            'resources/scripts/components/dashboard/DashboardContainer.tsx': "const A = () => <PageContentBlock title={'Dashboard'}><ServerList /></PageContentBlock>;",
        }
        for rel, text in fixtures.items():
            file = self.panel / rel
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(text)
    def tearDown(self):
        self.temp.cleanup()
    def test_every_supported_palette_integrates_without_database_migration(self):
        for name in a.PALETTES:
            if name == 'enigma':
                continue
            plan = a.admin_plan({'name': name}, {}, self.panel)
            self.assertFalse(any(p.startswith('database/') for p in plan))
            self.assertNotIn('storage/app/theme-installsr/preferences.json', plan)
            self.assertIn(b'zeronex-store-admin.php', plan['routes/admin.php'])
            self.assertIn(b'admin.zeronex-protection.menu', plan['resources/views/layouts/admin.blade.php'])
            self.assertIn(b'Auth::id() === 1', plan['resources/views/layouts/admin.blade.php'])
            self.assertIn(b'<ServerList />', plan['resources/scripts/components/dashboard/DashboardContainer.tsx'])
            self.assertIn(name.encode(), plan['config/theme-installsr.php'])
    def test_repeated_merge_is_idempotent(self):
        plan = a.admin_plan({'name': 'noobe'}, {}, self.panel)
        again = a.admin_plan({'name': 'noobe'}, plan.copy(), self.panel)
        self.assertEqual(plan, again)
    def test_enigma_replaces_placeholder_cards_once(self):
        rel = 'resources/scripts/components/dashboard/DashboardContainer.tsx'
        (self.panel / rel).write_text('<PageContentBlock><h2>SOSIAL MEDIA ADMIN</h2><a href="LINK_ADMIN">CHAT</a><h2>SERVER ANDA</h2><ServerList /></PageContentBlock>')
        plan = a.admin_plan({'name': 'enigma'}, {}, self.panel)
        self.assertNotIn(b'LINK_ADMIN', plan[rel])
        self.assertEqual(plan[rel].count(b'<ThemeCommunityLinks />'), 1)
        self.assertIn(b'<ServerList />', plan[rel])
    def test_unknown_layout_stops_instead_of_dropping_sidebar(self):
        (self.panel / 'resources/views/layouts/admin.blade.php').write_text('custom admin structure')
        with self.assertRaisesRegex(RuntimeError, 'Layout admin berbeda'):
            a.admin_plan({'name': 'noobe'}, {}, self.panel)


if __name__ == '__main__':
    unittest.main()
