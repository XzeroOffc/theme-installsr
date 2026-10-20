from pathlib import Path
import shutil

p = Path(__file__).with_name('install.py')
s = p.read_text()
old = "    if not assets or not any(str(v).endswith('.js') for v in assets.values()):\n        raise RuntimeError('Manifest tidak memuat bundle JavaScript.')"
new = "    validate_manifest(assets, stage / 'public/assets')"
helper = '''def validate_manifest(assets, directory):
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


'''
if old in s:
    shutil.copy2(p, p.with_suffix('.py.before-manifest-fix'))
    s = s.replace(old, new, 1)
    s = s.replace('def stage_build(', helper + 'def stage_build(', 1)
    compile(s, str(p), 'exec')
    p.write_text(s)
    print('Pemeriksaan manifest diperbaiki.')
elif new in s and 'def validate_manifest(' in s:
    print('Patch manifest sudah terpasang.')
else:
    raise SystemExit('Versi installer berbeda; tidak ada perubahan.')
