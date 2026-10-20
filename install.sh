#!/usr/bin/env bash
set +x
set -euo pipefail

# Ubah nama dan nilai token sebelum membagikan installer.
TOKEN_NAME='ZeroneXCode Access'
ACCESS_TOKEN='theme'
# Isi URL HTTPS ZIP dan SHA256-nya untuk menjalankan file ini tanpa paket lokal.
PACKAGE_URL=''
PACKAGE_SHA256=''

fail() { printf '\nGAGAL: %s\n' "$*" >&2; exit 1; }
clear_screen() { if [[ -t 1 && ${TERM:-dumb} != dumb ]]; then printf '\033[2J\033[H'; fi; }
[[ ${EUID} -eq 0 ]] || fail 'Jalankan dengan sudo bash install.sh.'
printf 'ZeroneXCode | Memeriksa dependensi dasar...\n'
missing=()
for entry in 'python3:python3' 'curl:curl' 'tar:tar' 'git:git' 'make:build-essential' 'g++:build-essential'; do
    command -v "${entry%%:*}" >/dev/null 2>&1 || missing+=("${entry#*:}")
done
[[ -s /etc/ssl/certs/ca-certificates.crt ]] || missing+=(ca-certificates)
if ((${#missing[@]})); then
    command -v apt-get >/dev/null 2>&1 || fail "Pasang dependensi ini dahulu: ${missing[*]} (otomatis khusus Ubuntu/Debian)."
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${missing[@]}"
fi
clear_screen
printf '\n  ZeroneXCode | ACCESS\n  %s\n\n' "$TOKEN_NAME"
[[ -n "$ACCESS_TOKEN" ]] || fail 'ACCESS_TOKEN belum diisi.'
[[ -r /dev/tty ]] || fail 'Terminal interaktif diperlukan untuk memasukkan token.'
valid=0
for attempt in 1 2 3; do
    printf '  Masukkan token (%s/3): ' "$attempt" >/dev/tty
    entered=''
    IFS= read -r -s entered </dev/tty || fail 'Input token dibatalkan.'
    printf '\n' >/dev/tty
    if [[ "$entered" == "$ACCESS_TOKEN" ]]; then valid=1; break; fi
    printf '  Token tidak valid.\n' >&2
done
unset entered ACCESS_TOKEN
[[ "$valid" == 1 ]] || fail 'Tiga percobaan gagal.'
clear_screen
printf 'Token valid. Menyiapkan menu tema...\n'
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
staging=''
trap '[[ -z "$staging" ]] || rm -rf -- "$staging"' EXIT
if [[ ! -f "$script_dir/compat/install.py" ]]; then
    [[ "$PACKAGE_URL" == https://* && "$PACKAGE_SHA256" =~ ^[a-fA-F0-9]{64}$ ]] || fail 'Isi PACKAGE_URL dan PACKAGE_SHA256 di file .sh, atau ekstrak paket ZIP lengkap.'
    staging="$(mktemp -d)"
    curl --fail --location --proto '=https' --proto-redir '=https' --retry 3 --connect-timeout 20 --max-time 600 --output "$staging/package.zip" "$PACKAGE_URL"
    python3 - "$staging" "$PACKAGE_SHA256" <<'PY'
import hashlib, pathlib, stat, sys, zipfile
root = pathlib.Path(sys.argv[1])
archive = root / 'package.zip'
if hashlib.sha256(archive.read_bytes()).hexdigest() != sys.argv[2].lower():
    raise SystemExit('GAGAL: checksum paket berbeda.')
with zipfile.ZipFile(archive) as z:
    total = 0
    for item in z.infolist():
        p = pathlib.PurePosixPath(item.filename)
        total += item.file_size
        if p.is_absolute() or '..' in p.parts or '\\' in item.filename or stat.S_ISLNK(item.external_attr >> 16) or total > 512*1024*1024:
            raise SystemExit('GAGAL: isi ZIP tidak aman.')
    z.extractall(root / 'payload')
PY
    script_dir="$staging/payload/theme-installsr"
    [[ -f "$script_dir/compat/install.py" ]] || fail 'Struktur paket tidak sesuai.'
fi
python3 "$script_dir/compat/install.py" "$@" </dev/tty
