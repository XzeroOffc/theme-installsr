# Installer tema Pterodactyl 1.15.1

Pembaruan ini memakai sumber panel yang diberikan dalam `test.zip` sebagai acuan penggabungan Store dan Protection. Semua arsip tema asli dan kredit pembuat tetap utuh. Menu menggunakan nomor 1–18.

## Menjalankan

Upload ZIP baru ke `/root/theme-installsr.zip`, lalu ekstrak ke folder baru:

```bash
unzip /root/theme-installsr.zip -d /root/theme-installsr-update
cd /root/theme-installsr-update/theme-installsr
sudo bash install.sh
```

Pilih satu tema. Untuk panel pada lokasi lain:

```bash
sudo bash install.sh --panel /var/www/pterodactyl
```

Prasyarat: Python 3, PHP dan vendor panel yang sudah berfungsi, Node.js >=22, Yarn Classic 1.x. Build membutuhkan internet dan ruang untuk salinan source serta dependensi. Installer tidak memasang paket sistem atau menurunkan versi dependensi panel.

```bash
bash install.sh --list
sudo bash install.sh --check
sudo bash install.sh --theme 14
```

`--check` memeriksa prasyarat dan checksum, bukan pengujian tampilan. Pengujian TypeScript dan build production dijalankan ketika memasang tema source.

## Pilihan tema

| Nomor | Tema | Cara pemasangan |
|---|---|---|
| 1 | abysspurple | Ekstensi Blueprint asli |
| 2 | arix | Diblokir: arsip tidak memuat controller Admin/Arix yang diperlukan route |
| 3 | billing | Diblokir: modul pembayaran, autentikasi, cron, dan database; berbenturan dengan Store |
| 4 | darkenate | Ekstensi Blueprint asli |
| 5 | elysium | Frontend asli, tambahan controller/route/settings, tabel `elysium` |
| 6 | enigma | Frontend asli, tambahan `nest_id` pada API aktif |
| 7 | frostcore | CSS asli, build ulang |
| 8 | iceMinecraft | CSS asli, selector tambahan dan warna console digabungkan |
| 9 | lemem | Ekstensi Blueprint asli |
| 10 | navyseals | Ekstensi Blueprint asli; memakai identifier internal paket |
| 11 | nebula_v1.8-3 | Blueprint; pilih salah satu versi Nebula |
| 12 | nebula_v2.0-1 | Blueprint; pilih salah satu versi Nebula |
| 13 | nightcore | CSS asli, build ulang |
| 14 | noobe | Frontend asli, tambahan `nest_id` dan `egg_id` pada API aktif |
| 15 | nook | Frontend/admin asli; sidebar Store/Protection tetap dari panel |
| 16 | nookure | Frontend asli, build ulang |
| 17 | recolor | Ekstensi Blueprint asli |
| 18 | stellar | Frontend asli, route/controller/settings, tabel `theme`, API `/theme` |

Arix memerlukan sumber controller lengkap dari paket pembuat. Billing memerlukan pekerjaan port modul terpisah sebelum dapat digabungkan dengan Store. Installer tidak mengarang controller atau melewati pemeriksaan kedua paket itu.

## Penggabungan dengan panel yang sudah dirombak

- Kernel, provider, model, konfigurasi aplikasi, route Store, dan Protection tidak diganti dengan versi lama dari tema.
- ServerTransformer dan pemetaan API frontend menggunakan file panel aktif. Field baru tema ditambahkan tanpa menghilangkan identifier baru, maintenance, maupun `skip_scripts`.
- Elysium dan Stellar menambahkan kelompok route tema ke route aktif. Endpoint 2FA dan pembatasan resource panel tetap dipertahankan.
- Menu pengaturan tema ditambahkan dengan mengikuti pembatasan Protection. Sidebar Nook menggunakan sidebar aktif yang sudah memuat Store/Protection.
- Sebelum penulisan, installer menolak rencana yang menghapus baris integrasi Store/Protection yang dikenal.
- Komponen frontend yang menjadi bagian tema memang diganti oleh komponen tema. Modifikasi frontend manual pada komponen yang sama perlu digabungkan tersendiri. Backup sebelum pemasangan disediakan.
- CSS Nightcore/Frostcore/IceMinecraft lama dilepas dari entry ketika memilih tema source penuh.
- IceMinecraft mempertahankan console aktif dan dukungan Unicode, hanya menyesuaikan warna terminal serta penanda CSS statistik/grafik. Paket IceMinecraft asli adalah tema CSS; paket ini tidak diubah menjadi desain Pixel3D.

## Pergantian tema source

Mulai versi ini, pemasangan menyimpan source awal dan hash hasil pemasangan di `storage/theme-installsr-state.json`. File ini bersifat privat.

Pada pergantian berikutnya, installer membuat baseline di direktori sementara, mengembalikan source sebelum tema yang dicatat, menerapkan tema pilihan, lalu menjalankan PHP lint, TypeScript, dan build production. Aset harus tersedia sesuai manifest. Panel aktif baru ditulis setelah semua pemeriksaan itu lolos.

Jika file yang dicatat berubah setelah pemasangan, installer berhenti dan mencantumkan file tersebut. Ini mencegah perubahan manual Anda hilang saat berganti tema. Jangan menghapus catatan state untuk memaksa pergantian.

Tema yang sudah dipasang oleh installer lama tidak mempunyai catatan ini. Pemasangan pertama versi ini memakai kondisi panel saat itu sebagai baseline. Impor tiga tema CSS di atas tetap dibersihkan; modifikasi tema source lama di luar catatan tidak dapat dipulihkan otomatis.

## Elysium dan Stellar

Migrasi dijalankan hanya dengan `--path` ke migrasi milik tema, bukan seluruh migrasi panel. Tabel baru menyimpan pengaturan tema. Jika nama tabel sudah digunakan tetapi catatan migrasinya tidak cocok, instalasi berhenti sebelum menulis panel.

Database Store tidak dimigrasikan oleh installer ini. Backup installer adalah backup file. Saat berganti tema atau memulihkan file, tabel dan catatan migrasi tema tetap disimpan agar pengaturan tidak dihapus. Jika migrasi gagal di tengah proses, file panel dipulihkan, tetapi perubahan database parsial mungkin tetap ada dan perlu diperiksa. Ambil backup database VPS sebelum memilih tema dengan migrasi.

## Backup dan pemulihan

Lokasi backup ditampilkan di terminal, misalnya `/var/www/theme-backups-pterodactyl/...-noobe`.

```bash
sudo bash install.sh --restore /var/www/theme-backups-pterodactyl/NAMA-BACKUP
```

Gunakan path lengkap yang tercetak ketika memasang tema. Pemulihan mengembalikan file, ownership, mode, dan catatan tema sebelumnya. File baru yang tercatat dihapus. Pemulihan juga dapat dijalankan ketika panel berada dalam maintenance. Gunakan backup terbaru sebelum ada edit manual berikutnya.

Saat pemasangan, panel masuk maintenance hanya setelah build selesai. Kegagalan penulisan, route, atau kompilasi view memicu pemulihan file. Bundle lama dipertahankan agar tab browser yang masih terbuka tidak langsung kehilangan aset.

## Blueprint

Tema Blueprint memerlukan framework dan CLI Blueprint yang sudah terpasang:
https://blueprint.zip/guides/admin/install

Installer menjalankan lifecycle asli ekstensi dan tidak mengubah batas versi paket. Kompatibilitas delapan ekstensi dengan framework pada VPS belum diuji langsung. Jangan menumpuk dua tema Blueprint; hapus tema lama melalui Blueprint sesuai panduan paket.

Pergantian langsung antara source dan Blueprint diblokir untuk menghindari saling menimpa integrasi. Pulihkan tema source terlebih dahulu sebelum memasang Blueprint. Untuk panel yang sudah menggunakan Blueprint, gunakan tema Blueprint atau siapkan staging terpisah untuk port source.

Sebelum menjalankan CLI, file panel dicadangkan dalam `panel-files.tar.gz`, tanpa vendor, node_modules, dan log. Ini bukan backup database. `--restore` hanya menerima backup source dengan `manifest.json`, bukan arsip Blueprint.

## Validasi

Lihat `TEST-RESULTS.md` untuk pemeriksaan yang benar-benar dijalankan. Tidak ada klaim bahwa semua tema sudah diuji pada VPS atau di browser. Setelah instalasi, periksa login, dashboard, console, Store, akun admin terbatas, dan tampilan ponsel. Untuk Elysium/Stellar, buka menu pengaturan tema sebagai owner.

Jalankan uji installer:

```bash
python3 -m unittest discover -s compat -p 'test_*.py'
```

Background/font eksternal tetap mengikuti paket asli. Aset eksternal yang tidak tersedia dapat menyebabkan tampilan berbeda.
