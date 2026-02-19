from core.models import Tutorial

def seed():
    data = [
        {
            'target_key': 'dashboard',
            'title': 'Panduan Dashboard Utama',
            'content': """Selamat datang di Dashboard Utama!
            
Di sini Anda dapat melihat ringkasan performa pondok secara real-time:
1. **KPI Keuangan**: Total tagihan lunas vs belum lunas bulan ini.
2. **KPI SDM**: Persentase kehadiran pengurus dan progres tugas harian.
3. **Statistik Lead**: Jumlah pendaftar baru yang masuk melalui WhatsApp.

Gunakan filter tenant (jika Anda Super Admin) untuk melihat data spesifik salah satu unit/cabang."""
        },
        {
            'target_key': 'core.lead',
            'title': 'Manajemen Leads & Prospek',
            'content': """Halaman ini digunakan untuk mengelola calon pendaftar yang masuk.
            
**Fitur Utama:**
- **Capture Otomatis**: Pesan dari WhatsApp dengan keyword DAFTAR/REG akan otomatis masuk ke sini.
- **AI Sales Coach**: Gunakan tombol 'Analyze Leads' untuk mendapatkan rangkuman minat pendaftar.
- **Auto Follow-up**: Gunakan 'Draft Follow-up' agar AI membuatkan balasan chat yang sopan dan efektif.
- **Konversi**: Jika sudah deal, gunakan aksi 'Convert to Santri' untuk memindahkan data ke database santri aktif."""
        },
        {
            'target_key': 'crm.santri',
            'title': 'Master Data Santri',
            'content': """Pusat data santri aktif dan alumni.
            
**Hal Penting:**
- **Tab Keuangan**: Di dalam detail santri, Anda bisa melihat riwayat pembayaran SPP dan Program secara mendalam.
- **Import/Export**: Gunakan fitur ini untuk memindahkan data dalam jumlah besar via Excel.
- **Status Aktif**: Pastikan status santri diperbarui jika ada yang lulus atau pindah agar penagihan otomatis berhenti."""
        },
        {
            'target_key': 'crm.tagihanspp',
            'title': 'Sistem Tagihan SPP',
            'content': """Kelola iuran bulanan santri secara otomatis.
            
**Langkah Kerja:**
1. **Generate Tagihan**: Sistem otomatis membuat tagihan setiap awal bulan berdasarkan program yang diikuti santri.
2. **Verifikasi Bayar**: Jika ada santri upload bukti bayar via portal, Anda bisa melakukan verifikasi di sini.
3. **WhatsApp Reminder**: Sistem akan mengirimkan pesan pengingat otomatis ke wali santri sebelum jatuh tempo."""
        },
        {
            'target_key': 'hr.pengurus',
            'title': 'Manajemen SDM (Pengurus)',
            'content': """Kelola data staf, pengasuh, dan pengurus pondok.
            
Di sini Anda bisa:
- Menyimpan data pribadi dan kontak pengurus.
- Menugaskan Role (Jabatan) tertentu.
- Memantau performa kerja individu melalui tab Dashboard SDM."""
        },
        {
            'target_key': 'crm.donatur',
            'title': 'Manajemen Donatur',
            'content': """Daftar para dermawan dan penyumbang pondok.
            
**Fitur Unggulan:**
- **AI Solicitation**: Gunakan menu 'Send Solicitation' agar AI membuatkan pesan ajakan donasi yang menyentuh hati sesuai profil donatur.
- **Riwayat Donasi**: Pantau total kontribusi setiap donatur untuk memberikan apresiasi yang tepat."""
        },
        {
            'target_key': 'crm.transaksidonasi',
            'title': 'Catatan Donasi Masuk',
            'content': """Pantau setiap rupiah yang masuk dari para donatur.
            
**Hal Penting:**
- **WhatsApp Receipt**: Gunakan fitur 'Send Receipt via WhatsApp' untuk mengirimkan bukti terima donasi yang profesional secara otomatis.
- **Reporting**: Data ini akan terintegrasi langsung ke Dashboard Keuangan."""
        },
        {
            'target_key': 'crm.tagihanprogram',
            'title': 'Tagihan Program Non-SPP',
            'content': """Gunakan menu ini untuk menagih iuran di luar SPP (misal: Uang Makan, Seragam, atau Gedung).
            
Tagihan di sini biasanya bersifat satu kali atau cicilan tetap sesuai kesepakatan saat santri masuk."""
        }
    ]

    for item in data:
        obj, created = Tutorial.objects.update_or_create(
            target_key=item['target_key'],
            defaults={
                'title': item['title'],
                'content': item['content'],
                'is_active': True
            }
        )
        print(f"{'[NEW]' if created else '[UPDATED]'} {item['title']}")

if __name__ == "__main__":
    seed()
