#!/usr/bin/env python3
import argparse
import base64
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge import merge_source, SOURCE_THEMES, BLOCKED
from admin import admin_plan
from terminal import show_menu

ROOT = Path(__file__).resolve().parent.parent
STATE = 'storage/theme-installsr-state.json'
CATALOG = json.loads((ROOT / 'compat/catalog.json').read_text())
CSS_THEMES = {'frostcore', 'nightcore', 'iceMinecraft'}
EXTRA = {
    'arix': {'bbcode-to-react': '0.2.9', 'i18next-browser-languagedetector': '7.2.2',
             'md5': '2.3.0', 'react-icons': '4.12.0'},
    'stellar': {'react-feather': '2.0.10'},
}
SKIP = {'package.json', 'yarn.lock', 'package-lock.json', 'webpack.config.js',
        'composer.json', 'composer.lock', 'config/app.php', '.env', 'artisan'}


def run(args, cwd, capture=False, env=None):
    print('+ ' + ' '.join(str(x) for x in args), flush=True)
    return subprocess.run(args, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None, env=env)


def members(z):
    total = 0
    for item in z.infolist():
        p = PurePosixPath(item.filename)
        if p.is_absolute() or '..' in p.parts or '\\' in item.filename:
            raise RuntimeError('Path tidak aman dalam ZIP: ' + item.filename)
        if stat.S_ISLNK(item.external_attr >> 16):
            raise RuntimeError('Symlink dalam ZIP tidak didukung.')
        total += item.file_size
        if total > 512 * 1024 * 1024:
            raise RuntimeError('Isi ZIP melebihi batas 512 MiB.')
        if not item.is_dir():
            yield item.filename, z.read(item)


def payload(theme):
    p = ROOT / theme['archive']
    if hashlib.sha256(p.read_bytes()).hexdigest() != theme['sha256']:
        raise RuntimeError('Checksum arsip berbeda: ' + p.name)
    with zipfile.ZipFile(p) as z:
        return dict(members(z))


def require_panel(panel, allow_maintenance=False):
    for name in ('artisan', 'package.json', 'vendor/autoload.php', 'config/app.php'):
        if not (panel / name).is_file():
            raise RuntimeError('File panel tidak ditemukan: ' + str(panel / name))
    config = (panel / 'config/app.php').read_text()
    match = re.search(r"['\"]version['\"]\s*=>\s*['\"]v?([^'\"]+)", config)
    if not match or match.group(1) != '1.15.1':
        raise RuntimeError('Installer ini khusus 1.15.1. Versi config/app.php: ' +
                           (match.group(1) if match else 'tidak terdeteksi'))
    for cmd in ('php', 'node', 'yarn'):
        if not shutil.which(cmd):
            raise RuntimeError(cmd + ' belum tersedia. Lihat INSTALL.md.')
    version = run(['node', '-p', 'process.versions.node'], panel, True).stdout.strip()
    if int(version.split('.')[0]) < 22:
        raise RuntimeError('Panel 1.15.1 membutuhkan Node.js >=22.')
    yarn = run(['yarn', '--version'], panel, True).stdout.strip()
    if not yarn.startswith('1.'):
        raise RuntimeError('Gunakan Yarn Classic 1.x untuk paket panel ini.')
    if (panel / 'storage/framework/down').exists() and not allow_maintenance:
        raise RuntimeError('Panel sedang maintenance. Selesaikan maintenance dahulu.')


def source_plan(theme, files, panel):
    out = {}
    for name, data in files.items():
        if not name.startswith('pterodactyl/'):
            continue
        rel = name[len('pterodactyl/'):]
        if rel in SKIP or rel.startswith('public/assets/'):
            continue
        if theme['name'] in CSS_THEMES:
            if not rel.endswith('.css'):
                continue
        elif not rel.startswith(('app/', 'routes/', 'database/migrations/', 'resources/', 'public/', 'config/')) and rel != 'tailwind.config.js':
            continue
        out[rel] = data
    if theme['name'] in CSS_THEMES:
        css = [x for x in out if x.endswith('.css')]
        if len(css) != 1:
            raise RuntimeError('Paket CSS tidak sesuai format.')
        entry = panel / 'resources/scripts/index.tsx'
        text = entry.read_text()
        for old_css in ('Pterodactyl_Frostcore_Theme.css', 'Pterodactyl_Nightcore_Theme.css',
                        'IceMinecraftTheme.css', 'theme-installsr-compat.css'):
            text = re.sub(r"^import\s+['\"]\./" + re.escape(old_css) +
                          r"['\"];?[ \t]*\n?", '', text, flags=re.M)
        css_name = Path(css[0]).name
        line = "import './" + css_name + "';"
        if line not in text:
            text = text.rstrip('\n') + '\n\n' + line + '\n'
        if theme['name'] == 'iceMinecraft':
            patch = 'resources/scripts/theme-installsr-compat.css'
            out[patch] = (ROOT / 'compat/iceMinecraft.css').read_bytes()
            console = 'resources/scripts/components/server/console/Console.tsx'
            if (panel / console).exists():
                source = (panel / console).read_text()
                pattern = r'(const theme\s*=\s*\{\s*background:)\s*[^\n]+,'
                source, count = re.subn(pattern, r"\1 '#111F26',", source, count=1)
                if count != 1:
                    raise RuntimeError('Warna console tidak dapat digabungkan dengan struktur panel ini.')
                out[console] = source.encode()
            for component, key in (('StatBlock', 'stat_block'), ('ChartBlock', 'chart_container')):
                rel = 'resources/scripts/components/server/console/' + component + '.tsx'
                if (panel / rel).exists():
                    source = (panel / rel).read_text()
                    anchor = 'classNames(styles.' + key + ','
                    alias = 'theme-installsr-' + key
                    if alias not in source:
                        if source.count(anchor) != 1:
                            raise RuntimeError('Komponen console berbeda: ' + rel)
                        source = source.replace(anchor, "classNames('" + alias + "', styles." + key + ',', 1)
                    out[rel] = source.encode()
            patch_import = "import './theme-installsr-compat.css';"
            if patch_import not in text:
                text += patch_import + '\n'
        out['resources/scripts/index.tsx'] = text.encode()
    pkg = json.loads((panel / 'package.json').read_text())
    for key, value in EXTRA.get(theme['name'], {}).items():
        if key not in pkg.get('dependencies', {}) and key not in pkg.get('devDependencies', {}):
            pkg.setdefault('dependencies', {})[key] = value
    original = files.get('pterodactyl/package.json')
    if original:
        old = json.loads(original)
        for group in ('dependencies', 'devDependencies'):
            for key, value in old.get(group, {}).items():
                if key not in pkg.get('dependencies', {}) and key not in pkg.get('devDependencies', {}):
                    pkg.setdefault(group, {})[key] = value
    out = merge_source(theme['name'], out, panel)
    out = admin_plan(theme, out, panel)
    out['package.json'] = (json.dumps(pkg, indent=4) + '\n').encode()
    for rel in out:
        target = panel / rel
        if panel not in target.resolve().parents:
            raise RuntimeError('Target keluar direktori panel: ' + rel)
    return out


def snapshot(panel, paths, backup):
    backup.mkdir(mode=0o700, parents=True)
    state = {}
    for rel in sorted(set(paths)):
        src = panel / rel
        state[rel] = {'exists': src.exists()}
        if src.exists():
            info = src.stat()
            state[rel].update(uid=info.st_uid, gid=info.st_gid, mode=stat.S_IMODE(info.st_mode))
        if src.exists():
            if not src.is_file() or src.is_symlink():
                raise RuntimeError('Target bukan file biasa: ' + rel)
            dst = backup / 'files' / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    (backup / 'manifest.json').write_text(json.dumps(state, indent=2))
    (backup / 'panel.txt').write_text(str(panel))


def restore(panel, backup):
    if (backup / 'panel.txt').read_text() != str(panel):
        raise RuntimeError('Backup berasal dari path panel berbeda.')
    state = json.loads((backup / 'manifest.json').read_text())
    for rel, info in state.items():
        dst = panel / rel
        if panel not in dst.resolve().parents:
            raise RuntimeError('Path backup tidak aman.')
        if info['exists']:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup / 'files' / rel, dst)
            os.chmod(dst, info['mode'])
            if os.geteuid() == 0:
                os.chown(dst, info['uid'], info['gid'])
        elif dst.exists():
            dst.unlink()
    run(['php', 'artisan', 'optimize:clear'], panel)
    print('File dipulihkan. Database tidak diubah oleh pemulihan file.')


def validate_manifest(assets, directory):
    from urllib.parse import urlsplit, unquote

    pending = [assets]
    bundles = []
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, str):
            path = unquote(urlsplit(value).path)
            if path.endswith('.js'):
                if '..' in PurePosixPath(path).parts:
                    raise RuntimeError('Path bundle tidak aman dalam manifest.')
                relative = path.split('/assets/', 1)[-1].removeprefix('assets/').lstrip('/')
                bundle = directory / relative
                if directory.resolve() not in bundle.resolve().parents:
                    raise RuntimeError('Path bundle keluar direktori aset.')
                bundles.append(bundle)
    if not bundles:
        raise RuntimeError('Manifest tidak memuat referensi JavaScript.')
    if any(not p.is_file() or p.stat().st_size == 0 for p in bundles):
        raise RuntimeError('Bundle dalam manifest hilang atau kosong.')


def stage_build(panel, plan, stage):
    for name in ('resources', 'public'):
        shutil.copytree(panel / name, stage / name, symlinks=False)
    for p in panel.iterdir():
        if p.is_file() and p.name != '.env':
            shutil.copy2(p, stage / p.name)
    for rel, data in plan.items():
        p = stage / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        if p.suffix == '.php' and not p.name.endswith('.blade.php'):
            run(['php', '-l', str(p)], stage, True)
    env = os.environ.copy()
    env['NODE_ENV'] = 'development'
    run(['yarn', 'install', '--non-interactive', '--production=false'], stage, env=env)
    run(['yarn', 'tsc', '--noEmit'], stage, env=env)
    env['NODE_ENV'] = 'production'
    run(['yarn', 'build:production'], stage, env=env)
    manifest = stage / 'public/assets/manifest.json'
    if not manifest.is_file():
        raise RuntimeError('Build tidak menghasilkan manifest aset.')
    assets = json.loads(manifest.read_text())
    validate_manifest(assets, stage / 'public/assets')
    for p in (stage / 'public/assets').rglob('*'):
        if p.is_file():
            plan[str(p.relative_to(stage))] = p.read_bytes()
    if (stage / 'yarn.lock').exists():
        plan['yarn.lock'] = (stage / 'yarn.lock').read_bytes()
    return plan


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def write_data(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def check_theme_database(theme, panel, migrations):
    table = 'elysium' if theme['name'] == 'elysium' else 'theme'
    script = """require 'vendor/autoload.php';
$app = require 'bootstrap/app.php';
$app->make(Illuminate\\Contracts\\Console\\Kernel::class)->bootstrap();
$table = $argv[1];
if (Illuminate\\Support\\Facades\\Schema::hasTable($table)) {
    if (!Illuminate\\Support\\Facades\\DB::table($table)->exists()) {
        fwrite(STDERR, 'Tabel tema kosong. Pulihkan pengaturan tema sebelum memasang.'); exit(1);
    }
    foreach (array_slice($argv, 2) as $migration) {
        if (!Illuminate\\Support\\Facades\\DB::table('migrations')->where('migration', $migration)->exists()) {
            fwrite(STDERR, 'Tabel tema sudah ada tetapi migrasi tidak cocok. Tidak diubah.'); exit(1);
        }
    }
}
"""
    run(['php', '-r', script, table] + [Path(m).stem for m in migrations], panel, True)


def install_source(theme, files, panel, backup_root):
    if theme['name'] in BLOCKED:
        raise RuntimeError(BLOCKED[theme['name']])
    if (panel / '.blueprint').exists():
        raise RuntimeError('Panel memakai Blueprint. Pergantian source harus dilakukan pada staging tanpa Blueprint agar ekstensi tidak tertimpa.')
    previous = json.loads((panel / STATE).read_text()) if (panel / STATE).exists() else {'original': {}, 'applied': {}}
    changed = [rel for rel, digest in previous['applied'].items() if file_digest(panel / rel) != digest]
    if changed:
        raise RuntimeError('File diubah setelah pemasangan tema. Simpan/gabungkan perubahan terlebih dahulu: ' + ', '.join(changed[:12]))
    with tempfile.TemporaryDirectory(prefix='theme-build-', dir=backup_root) as temp:
        stage = Path(temp)
        print('Build dilakukan di direktori sementara. Panel belum berubah.', flush=True)
        for rel in previous['original']:
            if panel not in (panel / rel).resolve().parents:
                raise RuntimeError('Path catatan tema tidak aman: ' + rel)
        baseline = stage / 'baseline'
        baseline.mkdir()
        for name in ('resources', 'public', 'app', 'routes', 'config', 'database'):
            if (panel / name).exists():
                shutil.copytree(panel / name, baseline / name)
        for source in panel.iterdir():
            if source.is_file() and source.name != '.env':
                shutil.copy2(source, baseline / source.name)
        originals = previous['original'].copy()
        for rel, encoded in originals.items():
            write_data(baseline / rel, base64.b64decode(encoded) if encoded is not None else None)
        plan = source_plan(theme, files, baseline)
        for rel in plan:
            if rel not in originals:
                file = baseline / rel
                originals[rel] = base64.b64encode(file.read_bytes()).decode() if file.exists() else None
        allowed = {'app/Http/Controllers/Admin/ThemeInstallerController.php', 'app/Services/ThemeInstallerSettings.php', 'config/theme-installsr.php', 'app/Transformers/Api/Client/ServerTransformer.php', 'routes/admin.php',
                   'routes/api-client.php', 'app/Http/Controllers/Api/Client/ClientController.php'}
        for rel, data in plan.items():
            if rel.startswith(('app/', 'routes/', 'config/')) and rel not in allowed and not rel.startswith(('app/Http/Controllers/Admin/Elysium/', 'app/Http/Controllers/Admin/Theme/')):
                raise RuntimeError('Backend belum memiliki aturan penggabungan: ' + rel)
            live = baseline / rel
            if live.is_file():
                for marker in re.findall(rb'[^\r\n]*(?:ZeroneXProtection|zeronex-store|zeronex-protection|admin\.store\.)[^\r\n]*', live.read_bytes()):
                    if marker.strip() not in data:
                        raise RuntimeError('Integrasi panel tidak boleh hilang: ' + rel)
        live_before = {rel: file_digest(panel / rel) for rel in set(plan) | set(originals) | {STATE}}
        build = stage / 'build'
        build.mkdir()
        plan = stage_build(baseline, plan, build)
        migrations = sorted(rel for rel in plan if rel.startswith('database/migrations/'))
        if migrations:
            check_theme_database(theme, panel, migrations)
        for rel, encoded in originals.items():
            if rel not in plan:
                plan[rel] = base64.b64decode(encoded) if encoded is not None else None
        if 'yarn.lock' not in originals:
            lockfile = panel / 'yarn.lock'
            originals['yarn.lock'] = base64.b64encode(lockfile.read_bytes()).decode() if lockfile.exists() else None
        applied = {rel: hashlib.sha256(data).hexdigest() if data is not None else None
                   for rel, data in plan.items() if not rel.startswith('public/assets/')}
        state = {'theme': theme['name'], 'original': originals, 'applied': applied}
        plan[STATE] = (json.dumps(state) + '\n').encode()
        backup = backup_root / (time.strftime('%Y%m%d-%H%M%S') + '-' + str(time.time_ns() % 1000000000) + '-' + theme['name'])
        for rel in plan:
            if panel not in (panel / rel).resolve().parents:
                raise RuntimeError('Target aset keluar direktori panel: ' + rel)
        changed = [rel for rel, digest in live_before.items() if file_digest(panel / rel) != digest]
        if changed:
            raise RuntimeError('File panel berubah selama build. Tidak dipasang: ' + ', '.join(changed[:12]))
        snapshot(panel, plan, backup)
        print('Backup:', backup)
        down = False
        try:
            run(['php', 'artisan', 'down'], panel)
            down = True
            for rel, data in plan.items():
                target = panel / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                owner = target.stat() if target.exists() else (panel / 'artisan').stat()
                write_data(target, data)
                if data is None:
                    continue
                os.chmod(target, 0o600 if rel == STATE else stat.S_IMODE(owner.st_mode) & ~0o111)
                if os.geteuid() == 0:
                    os.chown(target, 0 if rel == STATE else owner.st_uid, 0 if rel == STATE else owner.st_gid)
            for migration in migrations:
                run(['php', 'artisan', 'migrate', '--force', '--path=' + migration], panel)
            run(['php', 'artisan', 'optimize:clear'], panel)
            run(['php', 'artisan', 'route:list', '--json'], panel, True)
            run(['php', 'artisan', 'view:cache'], panel)
        except BaseException:
            restore(panel, backup)
            if migrations:
                print('File dipulihkan. Periksa migrasi tema: tabel/pengaturan database tidak dihapus otomatis.', file=sys.stderr)
            raise
        finally:
            if down:
                run(['php', 'artisan', 'up'], panel)
    print('Build dan pemasangan selesai. Muat ulang browser tanpa cache, lalu cek login, server, dan console.')


def install_blueprint(theme, files, panel, backup_root):
    if (panel / STATE).exists():
        raise RuntimeError('Pulihkan tema source dengan --restore sebelum memasang Blueprint. Jangan menumpuk dua pengelola tema.')
    cli = shutil.which('blueprint')
    if not cli or not (panel / '.blueprint').is_dir():
        raise RuntimeError('Blueprint belum terpasang pada panel ini. Ikuti https://blueprint.zip/guides/admin/install lalu jalankan menu lagi.')
    entries = [(n, b) for n, b in files.items() if n.endswith('.blueprint')]
    if len(entries) != 1:
        raise RuntimeError('Paket Blueprint tidak valid.')
    name, data = entries[0]
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        inner = dict(members(z))
    conf = inner.get('conf.yml', b'').decode()
    found = re.search(r'^\s*identifier:\s*[\"\']?([A-Za-z0-9_-]+)', conf, re.M)
    if not found:
        raise RuntimeError('Identifier Blueprint tidak ditemukan.')
    identifier = found.group(1)
    target = panel / (identifier + '.blueprint')
    if target.exists() and target.read_bytes() != data:
        raise RuntimeError(str(target) + ' sudah berisi paket berbeda. Pindahkan file itu terlebih dahulu.')
    backup = backup_root / (time.strftime('%Y%m%d-%H%M%S') + '-' + str(time.time_ns() % 1000000000) + '-' + theme['name'])
    backup.mkdir(mode=0o700)
    print('Membuat backup file panel sebelum Blueprint dijalankan:', backup)
    run(['tar', '--exclude=./node_modules', '--exclude=./vendor', '--exclude=./storage/logs',
         '-czf', str(backup / 'panel-files.tar.gz'), '.'], panel)
    target.write_bytes(data)
    os.chmod(target, 0o644)
    print('Blueprint menjalankan lifecycle asli paket. Backup ini hanya file, bukan database.')
    run([cli, '-install', identifier], panel)
    run(['php', 'artisan', 'optimize:clear'], panel)
    print('Perintah Blueprint selesai. Periksa pengaturan ekstensi dan tampilan panel.')


def main():
    parser = argparse.ArgumentParser(description='Menu tema untuk Pterodactyl 1.15.1')
    parser.add_argument('--panel', default='/var/www/pterodactyl')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--theme', type=int)
    parser.add_argument('--restore', type=Path)
    args = parser.parse_args()
    show_menu(CATALOG, CSS_THEMES, SOURCE_THEMES, BLOCKED)
    if args.list:
        return
    panel = Path(args.panel).resolve()
    require_panel(panel, allow_maintenance=bool(args.restore))
    if args.check:
        for t in CATALOG:
            payload(t)
        print('Versi panel, Node, Yarn, dan checksum 18 arsip lolos. Ini bukan uji kompatibilitas runtime.')
        return
    if os.geteuid() != 0:
        raise RuntimeError('Jalankan dengan sudo agar ownership file panel dapat dipertahankan.')
    lock = open(panel / 'storage/theme-installsr.lock', 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.restore:
        run(['php', 'artisan', 'down'], panel)
        try:
            restore(panel, args.restore.resolve())
        finally:
            run(['php', 'artisan', 'up'], panel)
        return
    choice = args.theme
    if choice is None:
        while True:
            raw = input('  Pilih nomor tema > ').strip()
            if raw.isdigit() and int(raw) in {0, *(t['number'] for t in CATALOG)}:
                choice = int(raw)
                break
            print('  Nomor tidak tersedia. Pilih angka pada menu.')
    if choice == 0:
        return
    theme = next((t for t in CATALOG if t['number'] == choice), None)
    if not theme:
        raise RuntimeError('Nomor tema tidak tersedia.')
    backup_root = panel.parent / ('theme-backups-' + panel.name)
    backup_root.mkdir(mode=0o700, exist_ok=True)
    files = payload(theme)
    if theme['kind'] == 'blueprint':
        install_blueprint(theme, files, panel, backup_root)
    else:
        install_source(theme, files, panel, backup_root)


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        print('\nGAGAL: ' + str(error), file=sys.stderr)
        sys.exit(1)
