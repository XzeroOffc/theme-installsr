# Hasil pengujian pembaruan installer

Acuan: source panel 1.15.1 pada test.zip, package.json dan yarn.lock unggahan. Konfigurasi build yang tidak disertakan di unggahan diambil dari tag resmi v1.15.1. Pengujian memakai source yang sudah digabungkan, bukan bundle lama dalam arsip tema.

| Tema | TypeScript | Webpack production | Manifest dan bundle |
|---|---|---|---|
| elysium | Lulus | Lulus | Lulus |
| enigma | Lulus | Lulus | Lulus |
| frostcore | Lulus | Lulus | Lulus |
| iceMinecraft | Lulus | Lulus | Lulus |
| nightcore | Lulus | Lulus | Lulus |
| noobe | Lulus | Lulus | Lulus |
| nook | Lulus | Lulus | Lulus |
| nookure | Lulus | Lulus | Lulus |
| stellar | Lulus | Lulus | Lulus |

- 15 uji installer lulus, mencakup integritas arsip, CSS, manifest bertingkat, path tidak aman, backup/restore, pergantian tema dari baseline, penolakan edit manual, pemulihan setelah kegagalan, dan Unicode console.
- Rencana keenam tema source mempertahankan baris integrasi dalam 26 file Store/Protection pada unggahan.
- Parser PHP memeriksa 21 file backend/migrasi hasil penggabungan. PHP CLI tidak tersedia di lingkungan pengujian ini; installer tetap menjalankan php -l pada VPS sebelum pemasangan.
- Pemeriksaan statis kolom Blade Elysium/Stellar menemukan seluruh kolom yang dirujuk dalam migrasi paket.
- Checksum seluruh 18 arsip tema utama cocok dengan katalog awal. File koleksi asli tidak diedit; ZIP hasil lolos pemeriksaan integritas.

## Batas pengujian

Belum menjalankan Laravel, migrasi database, login, koneksi Wings, atau browser pada VPS. Tidak ada klaim audit visual maupun aksesibilitas lengkap. Kedelapan ekstensi Blueprint belum diuji runtime. Arix dan Billing diblokir dengan alasan pada menu dan INSTALL.md.

Build lokal memakai dependensi dari lockfile unggahan, ditambah react-feather 2.0.10 untuk Stellar. URL registry lokal diarahkan ke registry.npmjs.org untuk unduhan; lockfile panel pengguna tidak diedit untuk pengujian ini. Bundle hasil pengujian tidak disertakan, installer membangun ulang sesuai panel tujuan.
