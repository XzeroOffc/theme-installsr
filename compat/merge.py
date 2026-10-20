import re

SOURCE_THEMES = {'noobe', 'enigma', 'nook', 'nookure', 'elysium', 'stellar'}
BLOCKED = {
    'arix': 'Paket Arix tidak berisi controller Admin/Arix yang dipanggil route. Diperlukan paket sumber Arix lengkap.',
    'billing': 'Billing bukan tema mandiri. Paket mengganti autentikasi, pembayaran, cron, dan database Store; perlu port modul terpisah.',
}


def replace_once(text, before, after, path):
    if text.count(before) != 1:
        raise RuntimeError('Struktur file berbeda; penggabungan dibatalkan: ' + path)
    return text.replace(before, after, 1)


def merge_source(name, out, panel):
    if name not in SOURCE_THEMES:
        return out
    backend = 'app/Transformers/Api/Client/ServerTransformer.php'
    api = 'resources/scripts/api/server/getServer.ts'
    fields = ('nest', 'egg') if name in {'noobe', 'stellar'} else (('nest',) if name == 'enigma' else ())
    if fields:
        php = (panel / backend).read_text()
        ts = (panel / api).read_text()
        for field in fields:
            if not re.search(r"['\"]" + field + r"_id['\"]\s*=>", php):
                anchor = "'is_node_under_maintenance' =>"
                match = re.search(r'(?m)^.*' + re.escape(anchor) + r'.*\n', php)
                if not match:
                    raise RuntimeError('Anchor transformer tidak ditemukan: ' + backend)
                php = replace_once(php, match.group(), match.group() + f"            '{field}_id' => $server->{field}_id,\n", backend)
            if not re.search(r'\b' + field + r'Id\s*:', ts):
                ts = replace_once(ts, '    isNodeUnderMaintenance: boolean;',
                                  f'    {field}Id: number;\n    isNodeUnderMaintenance: boolean;', api)
                ts = replace_once(ts, '    isNodeUnderMaintenance: data.is_node_under_maintenance,',
                                  f'    {field}Id: data.{field}_id,\n    isNodeUnderMaintenance: data.is_node_under_maintenance,', api)
        out[backend] = php.encode()
        out[api] = ts.encode()
    # The activity page controls pagination; keep the live controller and its authorization.
    out.pop('app/Http/Controllers/Api/Client/ActivityLogController.php', None)
    out.pop('app/Console/Commands/love.php', None)
    if name in {'elysium', 'stellar'}:
        prefix = 'elysium' if name == 'elysium' else 'theme'
        route = 'routes/admin.php'
        old = out[route].decode()
        group = re.search(r"Route::group\(\['prefix' => '" + prefix + r"'\], function \(\) \{\n.*?^\}\);", old, re.M | re.S)
        if not group:
            raise RuntimeError('Route tema tidak ditemukan: ' + name)
        current = (panel / route).read_text()
        if f"'prefix' => '{prefix}'" in current:
            raise RuntimeError('Route tema sudah ada di luar catatan installer: ' + prefix)
        out[route] = (current.rstrip() + '\n\n' + group.group() + '\n').encode()
        layout = 'resources/views/layouts/admin.blade.php'
        current = (panel / layout).read_text()
        menu = f'''\n@if(!class_exists('\\Pterodactyl\\ZeroneXProtection\\Policy') || !\\Pterodactyl\\ZeroneXProtection\\Policy::limited(Auth::user()))
<li><a href="{{{{ route('admin.{prefix}') }}}}"><i class="fa fa-paint-brush"></i> <span>{name.title()}</span></a></li>
@endif
'''
        current = replace_once(current, '<ul class="sidebar-menu">', '<ul class="sidebar-menu">' + menu, layout)
        out[layout] = current.encode()
        if name == 'stellar':
            route = 'routes/api-client.php'
            current = (panel / route).read_text()
            if re.search(r"Route::get\(['\"]/theme['\"]", current):
                raise RuntimeError('Endpoint /theme sudah dipakai panel.')
            out[route] = (current.rstrip() + "\nRoute::get('/theme', [\\Pterodactyl\\Http\\Controllers\\Api\\Client\\ClientController::class, 'theme']);\n").encode()
            controller = 'app/Http/Controllers/Api/Client/ClientController.php'
            current = (panel / controller).read_text().rstrip()
            if re.search(r'function\s+theme\s*\(', current) or not current.endswith('}'):
                raise RuntimeError('ClientController tidak sesuai untuk penggabungan.')
            out[controller] = (current[:-1] + '''    public function theme(): array
    {
        return ['success' => true, 'data' => \\Illuminate\\Support\\Facades\\DB::table('theme')->first()];
    }
}
''').encode()
        for path, data in list(out.items()):
            if path.endswith('.php'):
                out[path] = data.replace(b'\\Carbon::now()', b'\\Carbon\\Carbon::now()')
    elif name == 'nook':
        # Preserve the complete live sidebar, including Store links and limited-admin branches.
        path = 'resources/views/layouts/admin.blade.php'
        themed = out[path].decode()
        live = (panel / path).read_text()
        pattern = r'<aside\b[^>]*class="main-sidebar"[^>]*>.*?</aside>'
        old = re.search(pattern, themed, re.S)
        new = re.search(pattern, live, re.S)
        if not old or not new:
            raise RuntimeError('Sidebar admin tidak dikenali; Nook tidak ditulis.')
        out[path] = themed.replace(old.group(), new.group(), 1).encode()
    for rel, data in list(out.items()):
        if not rel.startswith('resources/scripts/') or not rel.endswith(('.ts', '.tsx')):
            continue
        text = data.decode()
        if rel.endswith('/console/Console.tsx'):
            if 'Unicode11Addon' not in text:
                text = "import { Unicode11Addon } from 'xterm-addon-unicode11';\n" + text
                text = replace_once(text, 'const webLinksAddon = new WebLinksAddon();',
                                    'const webLinksAddon = new WebLinksAddon();\n    const unicode11Addon = new Unicode11Addon();', rel)
                text = replace_once(text, 'terminal.loadAddon(webLinksAddon);',
                                    'terminal.loadAddon(webLinksAddon);\n            terminal.loadAddon(unicode11Addon);', rel)
                text = replace_once(text, 'terminal.open(ref.current);',
                                    "terminal.open(ref.current);\n            terminal.unicode.activeVersion = '11';", rel)
            if 'searchBar.addNewStyle(' not in text:
                text = replace_once(text, 'terminal.open(ref.current);',
                                    "terminal.open(ref.current);\n            searchBar.addNewStyle('.xterm-search-bar__addon { z-index: 10; }');", rel)
        if rel.endswith('/CopyOnClick.tsx'):
            text = text.replace('React.isValidElement(children)', 'React.isValidElement<React.HTMLAttributes<HTMLElement>>(children)')
        if rel.endswith(('/SetupTOTPDialog.tsx', '/DisableTOTPDialog.tsx')):
            text = text.replace('onChange={(e) =>', 'onChange={(e: React.ChangeEvent<HTMLInputElement>) =>')
        if rel.endswith('/InputField.tsx'):
            text = text.replace("interface InputFieldProps extends React.ComponentProps<'input'> {", "type InputFieldProps = React.ComponentProps<'input'> & {")
        if rel.endswith('/UploadButton.tsx'):
            text = text.replace('data: ProgressEvent', 'data: { loaded: number }')
        if rel.endswith('/Avatar.tsx') and name == 'enigma':
            text = text.replace('state.user.data?.image ||', "(state.user.data && 'image' in state.user.data && typeof state.user.data.image === 'string' ? state.user.data.image : undefined) ||")
        if rel.endswith(('/Translate.tsx', '/CodemirrorEditor.tsx')) and (panel / rel).exists():
            text = (panel / rel).read_text()
        out[rel] = text.encode()
    entry = 'resources/scripts/index.tsx'
    text = (panel / entry).read_text()
    for css in ('Pterodactyl_Frostcore_Theme.css', 'Pterodactyl_Nightcore_Theme.css', 'IceMinecraftTheme.css', 'theme-installsr-compat.css'):
        text = re.sub(r"^import\s+['\"]\./" + re.escape(css) + r"['\"];?[ \t]*\n?", '', text, flags=re.M)
    if entry in out:
        for line in out[entry].decode().splitlines():
            if re.match(r"import ['\"].*\.css['\"];?", line) and line not in text:
                text += '\n' + line + '\n'
    out[entry] = text.encode()
    return out
