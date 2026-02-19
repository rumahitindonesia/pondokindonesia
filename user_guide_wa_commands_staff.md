# 🤖 Panduan WhatsApp Command untuk Staff/Admin

Selamat! Anda kini dapat mengelola data pesantren langsung melalui WhatsApp tanpa perlu membuka dashboard. Fitur ini dirancang untuk memudahkan input data saat Anda sedang di lapangan atau dalam mobilitas tinggi.

---

## 🔐 Syarat Penggunaan
Agar perintah Anda diproses oleh sistem, pastikan:
1. Nomor WhatsApp Anda sudah terdaftar di profil **User (Staff/Admin)** pada dashboard.
2. Status akun Anda adalah **Active**.
3. Kirim pesan ke nomor WhatsApp gateway resmi Pondok.

---

## 🔎 1. Pencarian Data (CARI)
Gunakan perintah ini untuk mencari info Santri atau Donatur secara cepat.
- **Format**: `CARI [nama]`
- **Contoh**: `CARI Ahmad`
- **Output**: Daftar nama, NIS (Santri), atau Kode (Donatur) yang cocok.

---

## ✍️ 2. Input Data Cepat (Shortcut)
Format input data menggunakan akhiran garis miring (`/`) dan pemisah tanda pagar (`#`).

### A. Registrasi Santri Baru
- **Format**: `SANTRI/nama#nohp#alamat`
- **Contoh**: `SANTRI/Budi Santoso#628123#Solo`

### B. Registrasi Donatur Baru
- **Format**: `DONATUR/nama#nohp#alamat`
- **Contoh**: `DONATUR/Hj. Siti#628555#Bandung`

### C. Catat Transaksi Donasi
- **Format**: `TRX/kode#program#nominal#keterangan`
- **Contoh**: `TRX/DON-2402-01#Infaq#50000#Input saat jumatan`
- *Catatan: Kode bisa didapat dari perintah CARI.*

### D. Input Pendaftar (Lead)
- **Format**: `LEAD/nama#nohp#keterangan`
- **Contoh**: `LEAD/Andi#628999#Tanya beasiswa`

---

## 📊 3. Laporan Keuangan (REVENUE)
Pantau omzet Pondok secara real-time.
- **Format**: `REVENUE/[period]`
- **Pilihan Period**: `today` (hari ini), `month` (bulan ini), `total` (seluruh waktu).
- **Contoh**: `REVENUE/month`

---

## 💡 4. Kolaborasi dengan AI (Yasmin)
Selain format kaku di atas, Anda juga bisa bercakap-cakap secara natural dengan asisten AI kami (**Yasmin**).

- **Chat Biasa**: *"Yasmin, tolong cariin data wali santri yang namanya Lira."*
- **Sistem Cerdas**: Yasmin akan membalas dengan info yang ditemukan dan secara otomatis menjalankan perintah pencarian di latar belakang jika data di chat kurang lengkap.

> [!TIP]
> **Yasmin** juga bisa membantu menganalisis minat pendaftar (Lead). Cukup tanya: *"Gimana perkembangan pendaftar Ahmad?"*, dan asisten akan memberikan ringkasan analisis untuk Anda.

---

> [!WARNING]
> **Keamanan**: Jangan pernah membagikan nomor WhatsApp Anda kepada orang lain. Setiap pesan dari nomor Anda akan dianggap sebagai instruksi resmi Admin di sistem.
