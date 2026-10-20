from pathlib import Path
import re

PALETTES = {
    'enigma': ('#161616', '#212121', '#eeeeee'),
    'noobe': ('#080e26', '#161e41', '#60a5fa'),
    'nook': ('#121212', '#212121', '#a5b4fc'),
    'nookure': ('#202e3d', '#33404d', '#60a5fa'),
    'elysium': ('#0c0c2b', '#1b1c3e', '#ff8600'),
    'stellar': ('#1b1c30', '#2a2f41', '#6493ff'),
    'iceMinecraft': ('#0d181e', '#132537', '#72c8e8'),
    'nightcore': ('#111827', '#1f2937', '#93c5fd'),
    'frostcore': ('#101b25', '#1c3040', '#7dd3fc'),
}


def admin_plan(theme, out, panel):
    name = theme['name']
    if name not in PALETTES:
        return out
    root = Path(__file__).with_name('admin-payload')
    for file in root.rglob('*'):
        if file.is_file():
            out[str(file.relative_to(root))] = file.read_bytes()
    bg, surface, accent = PALETTES[name]
    out['config/theme-installsr.php'] = ("<?php\nreturn ['active' => '" + name + "', 'palette' => [" +
        f"'bg' => '{bg}', 'panel' => '{surface}', 'text' => '#f5f5f5', 'muted' => '#b8c2ce', " +
        f"'border' => '#596574', 'accent' => '{accent}', 'accent-text' => '#101318']];\n").encode()
    def text(path):
        return out[path].decode() if path in out else (panel / path).read_text()
    route = 'routes/admin.php'
    current = text(route)
    if "name('admin.theme-installsr')" not in current:
        current += "\nRoute::get('/theme-installsr', [\\Pterodactyl\\Http\\Controllers\\Admin\\ThemeInstallerController::class, 'index'])->name('admin.theme-installsr');\nRoute::post('/theme-installsr', [\\Pterodactyl\\Http\\Controllers\\Admin\\ThemeInstallerController::class, 'update'])->name('admin.theme-installsr.update');\n"
    out[route] = current.encode()
    layout = 'resources/views/layouts/admin.blade.php'
    current = text(layout)
    if "partials.theme-installsr.admin" not in current:
        if current.count('</head>') != 1 or current.count('<ul class="sidebar-menu">') != 1:
            raise RuntimeError('Layout admin berbeda; penggabungan pengaturan tema dihentikan.')
        current = current.replace('</head>', "@include('partials.theme-installsr.admin')\n</head>")
        current = current.replace('<ul class="sidebar-menu">', '''<ul class="sidebar-menu">
@if((int) Auth::id() === 1)
<li><a href="{{ route('admin.theme-installsr') }}"><i class="fa fa-paint-brush"></i> <span>Pengaturan Tema</span></a></li>
@endif''')
        current = current.replace('initial-scale=1, maximum-scale=1, user-scalable=no', 'initial-scale=1')
    out[layout] = current.encode()
    wrapper = 'resources/views/templates/wrapper.blade.php'
    current = text(wrapper)
    if 'partials.theme-installsr.runtime' not in current:
        if current.count('</head>') != 1:
            raise RuntimeError('Wrapper dashboard berbeda; pengaturan tema tidak dipasang.')
        current = current.replace('</head>', "@include('partials.theme-installsr.runtime')\n</head>")
    out[wrapper] = current.encode()
    dashboard = 'resources/scripts/components/dashboard/DashboardContainer.tsx'
    current = text(dashboard)
    if 'ThemeCommunityLinks' not in current:
        current = "import ThemeCommunityLinks from '@/components/dashboard/ThemeCommunityLinks';\n" + current
        if name == 'enigma':
            current, count = re.subn(r'<h2>SOSIAL MEDIA ADMIN</h2>.*?(?=<h2>SERVER ANDA</h2>)', '<ThemeCommunityLinks />\n                ', current, count=1, flags=re.S)
        else:
            current, count = re.subn(r'(<PageContentBlock\b[^>]*>)', r'\1\n            <ThemeCommunityLinks />', current, count=1)
        if count != 1:
            raise RuntimeError('Dashboard tidak dikenali; tidak dapat menambahkan pengaturan komunitas.')
    out[dashboard] = current.encode()
    return out
