#!/usr/bin/env bash
set -euo pipefail

if (( EUID != 0 )); then
    echo "Jalankan sebagai root di VPS."
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    apt-get update
    apt-get install -y git ca-certificates
fi

INSTALL_DIR="$(mktemp -d /root/zeronex-theme.XXXXXX)"
trap 'rm -rf -- "$INSTALL_DIR"' EXIT

git clone --depth 1 \
    https://github.com/XzeroOffc/theme-installsr.git \
    "$INSTALL_DIR"

bash "$INSTALL_DIR/install.sh" "$@" </dev/tty
