# 🚀 Panduan Alur Pendaftaran Santri Otomatis (Lead Workflow)

Selamat! Sistem pendaftaran di Pondok Anda kini sudah dilengkapi dengan asisten AI dan sistem pembagian tugas otomatis. Panduan ini akan membantu Anda memahami cara kerja sistem dari awal hingga santri resmi terdaftar.

## 🛠️ Persiapan: Akun yang Harus Disiapkan Admin Tenant

Agar alur ini berjalan, Admin Tenant (Pondok) wajib menyiapkan minimal 2 jenis user berikut:

1.  **User Role: `Customer Service`**
    - **Fungsi**: Menerima pendaftar baru, melakukan chat awal, dan memantau dashboard harian.
    - **Akses**: Hanya melihat lead yang ditugaskan kepadanya.
2.  **User Role: `Admin PSB & Interview`**
    - **Fungsi**: Mengatur jadwal interview, memverifikasi pembayaran pendaftaran, dan menentukan kelulusan (Accepted).
    - **Akses**: Memiliki akses ke tombol "Tandai Diterima" dan konversi ke data Santri/Donatur.

> [!IMPORTANT]
> Pastikan setiap user tersebut sudah memiliki **Nomor WhatsApp** yang terisi di profilnya agar bisa menerima notifikasi otomatis dari sistem.

---

## 📱 Tahap 1: Pesan Masuk (Ads / Sapaan Awal)
Wali santri biasanya masuk melalui Klik Iklan (FB/IG Ads) yang mengirimkan pesan pembuka otomatis.

1.  **Trigger (Pemicu)**: Anda harus menyetting **WhatsApp Auto Reply** dengan kata kunci yang ada di iklan Anda (contoh: "Halo, saya tertarik").
2.  **Balasan Instruksi**: Isi balasan Auto Reply tersebut dengan instruksi pengisian data:
    `Silakan daftar dengan format: nama#kota#sekolah`
3.  **Status Lead**: Di tahap ini, pendaftar sudah tercatat di sistem dengan status **"Menunggu Data"**.

---

## 📝 Tahap 2: Pengisian Data (Data Extraction)
Begitu wali santri membalas dengan format yang diminta, sistem akan bekerja secara otomatis.

- **Contoh Pesan**: `Ahmad#Solo#SMA 1`
- **Otomatisasi**: Sistem mengenali pemisah `#` dan langsung memetakan:
    - Nama: Ahmad
    - Kota: Solo
    - Sekolah: SMA 1
- **Status Lead**: Berubah otomatis menjadi **"Baru (Data Lengkap)"**.

---

## 👩‍💻 Tahap 2: Pembagian Tugas ke CS (CS Assignment)
Sistem menggunakan logika **Load-Balancing** untuk membagi tugas secara adil.

- **Alur**: Lead baru akan langsung ditugaskan ke petugas CS yang memiliki jumlah "Lead Baru" paling sedikit saat itu.
- **Notifikasi**: Petugas CS akan menerima pesan WhatsApp otomatis yang memberitahu bahwa ada pendaftar baru yang perlu dibantu.

---

## 📊 Tahap 3: Dashboard CS (Petugas CS)
Petugas CS dapat fokus melayani pendaftarnya sendiri melalui Dashboard.

1.  **Dashboard Scoped**: Petugas CS hanya akan melihat statistik dan daftar lead miliknya sendiri (lebih rapi dan privat).
2.  **AI Sales Coach**: Di detail lead, petugas bisa melihat "Analisis AI" yang memberikan ringkasan minat wali santri dan saran cara membalas pesan mereka agar lebih efektif.
3.  **Prioritas Follow-up**: Gunakan tabel "Prioritas" di dashboard untuk melihat siapa yang paling berminat (HOT) dan perlu segera dihubungi.

---

## 🎤 Tahap 4: Proses Interview & Penerimaan
Setelah CS selesai melakukan penanganan awal, pendaftar bisa dialokasikan ke tahap selanjutnya.

1.  **Lanjutkan ke Interview**:
    - Pilih lead di menu **Pendaftar (Lead)**.
    - Pilih aksi **"Set : Lanjutkan ke Interview"**.
    - **Otomatis**: Wali santri menerima WA bahwa jadwal sedang disiapkan, dan Admin PSB menerima notifikasi untuk mengecek sistem.
2.  **Tandai Diterima**:
    - Setelah interview selesai, pilih aksi **"Set : Tandai Diterima"**.
    - **Otomatis**: Wali santri akan menerima pesan selamat via WhatsApp.

---

## 🔄 Tahap 5: Follow-up Otomatis (AFU)
Jangan khawatir jika wali santri lupa membalas. Sistem akan melakukan **Follow-up Otomatis** sebanyak 5 kali:
- H+1 Jam, H+8 Jam, hingga H+3 hari.
- Jika setelah 5 kali tidak ada respon, Lead otomatis akan ditandai sebagai **Batal/Rejected** agar tim bisa fokus ke pendaftar lain.

---

## 🧪 Cara Mengetes (API StarSender Aktif)
Bapak bisa langsung mencoba di tenant **Rumah IT**:
1. Kirim pesan WA ke nomor Rumah IT.
2. Balas dengan format: `NamaTes#KotaTes#SekolahTes`.
3. Cek di Dashboard: Pastikan pendaftar muncul di kolom "Pendaftar Baru".
4. Gunakan Menu **Pendaftar** untuk mencoba tombol-tombol alur (Interview/Diterima).

---

> [!TIP]
> **Selalu perhatikan label minat AI (Hot/Warm/Cold)**. Fokuskan energi tim pada pendaftar dengan label **Hot** untuk hasil konversi yang maksimal!
