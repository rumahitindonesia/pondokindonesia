from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import TenantAwareModel
from django.conf import settings

class Jabatan(TenantAwareModel):
    nama = models.CharField(_("Nama Jabatan"), max_length=150)
    atasan = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='bawahan',
        verbose_name=_("Atasan Langsung"),
        help_text=_("Pilih atasan langsung untuk posisi ini. Kosongkan jika posisi tertinggi.")
    )
    deskripsi = models.TextField(_("Deskripsi Jabatan"), blank=True, null=True)

    class Meta:
        verbose_name = _("Jabatan")
        verbose_name_plural = _("Daftar Jabatan")
        ordering = ['nama']

    def __str__(self):
        return self.nama

class Pengurus(TenantAwareModel):
    nama = models.CharField(_("Nama Lengkap"), max_length=255)
    nik = models.CharField(_("NIK / ID Pegawai"), max_length=50, blank=True, null=True)
    jabatan = models.ForeignKey(
        Jabatan, 
        on_delete=models.PROTECT, 
        related_name='anggota',
        verbose_name=_("Jabatan")
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pengurus_profile',
        verbose_name=_("Akun Login (Username)"),
        help_text=_("Hubungkan dengan akun login untuk tracking kinerja.")
    )
    telepon = models.CharField(_("Nomor WhatsApp"), max_length=20, blank=True, null=True)
    alamat = models.TextField(_("Alamat Tinggal"), blank=True, null=True)
    foto = models.ImageField(_("Foto Profil"), upload_to='pengurus_foto/', blank=True, null=True)
    
    is_active = models.BooleanField(_("Status Aktif"), default=True)
    join_date = models.DateField(_("Tanggal Bergabung"), auto_now_add=True)

    class Meta:
        verbose_name = _("Pengurus / Karyawan")
        verbose_name_plural = _("Daftar Pengurus")
        ordering = ['nama']

    def __str__(self):
        return f"{self.nama} - {self.jabatan.nama if self.jabatan else '-'}"

class Tugas(TenantAwareModel):
    class Status(models.TextChoices):
        BARU = 'BARU', _('Baru')
        PROSES = 'PROSES', _('Sedang Dikerjakan')
        SELESAI = 'SELESAI', _('Selesai')
        DIBATALKAN = 'DIBATALKAN', _('Dibatalkan')
        PENDING_APPROVAL = 'PENDING_APPROVAL', _('Menunggu Persetujuan')
        REVISI = 'REVISI', _('Perlu Revisi')

    class Prioritas(models.TextChoices):
        RENDAH = 'RENDAH', _('Rendah')
        SEDANG = 'SEDANG', _('Sedang')
        TINGGI = 'TINGGI', _('Tinggi')

    class Jenis(models.TextChoices):
        PENUGASAN = 'PENUGASAN', _('Penugasan Langsung')
        PERMINTAAN = 'PERMINTAAN', _('Permintaan Lintas Divisi')

    judul = models.CharField(_("Judul Tugas"), max_length=255)
    deskripsi = models.TextField(_("Deskripsi Detail"), blank=True)
    
    # Relationships
    pembuat = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='tugas_dibuat',
        verbose_name=_("Dibuat Oleh")
    )
    penerima = models.ForeignKey(
        'hr.Pengurus', 
        on_delete=models.CASCADE, 
        related_name='daftar_tugas',
        verbose_name=_("Ditugaskan Kepada")
    )
    
    # Optional: Link to a specific Lead (for ad-hoc follow ups)
    lead = models.ForeignKey(
        'core.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tugas_terkait',
        verbose_name=_("Terkait Lead (Opsional)"),
        help_text=_("Pilih jika tugas ini berkaitan khusus dengan satu Lead.")
    )
    
    # Tracking
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.BARU,
        verbose_name=_("Status")
    )
    prioritas = models.CharField(
        max_length=20, 
        choices=Prioritas.choices, 
        default=Prioritas.SEDANG,
        verbose_name=_("Prioritas")
    )
    jenis = models.CharField(
        max_length=20, 
        choices=Jenis.choices, 
        default=Jenis.PENUGASAN,
        verbose_name=_("Jenis Tugas")
    )
    
    # Dates
    tenggat_waktu = models.DateTimeField(_("Tenggat Waktu"), null=True, blank=True)
    tanggal_selesai = models.DateTimeField(_("Tanggal Selesai"), null=True, blank=True)
    
    # Attachment
    file = models.FileField(upload_to='tugas_files/', blank=True, null=True, verbose_name=_("Lampiran"))
    url_posting = models.URLField(_("Link Posting / Bukti Tayang"), blank=True, null=True, help_text=_("Link konten yang sudah diposting (untuk bukti selesai)."))

    # Penyelesaian & Penilaian (Scoring)
    waktu_diselesaikan = models.DateTimeField(_("Waktu Diselesaikan"), null=True, blank=True)
    catatan_penyelesaian = models.TextField(_("Catatan Penyelesaian"), blank=True, help_text=_("Catatan dari staf saat menyelesaikan tugas."))
    
    # Bobot Tugas (untuk penilaian Manager/Strategis)
    bobot = models.IntegerField(
        _("Bobot Nilai (1-5)"),
        default=3,
        help_text=_("1=Ringan, 3=Standar, 5=Strategis/KPI Utama. Digunakan untuk hitung rata-rata kinerja.")
    )

    skor = models.IntegerField(
        _("Skor Kinerja (0-100)"), 
        null=True, 
        blank=True,
        help_text=_("Nilai kinerja untuk tugas ini (diisi oleh pemberi tugas).")
    )
    review_manager = models.TextField(_("Review Manager"), blank=True, help_text=_("Catatan evaluasi dari pemberi tugas."))

    class Meta:
        verbose_name = _("Tugas")
        verbose_name_plural = _("Daftar Tugas")
        ordering = ['-tenggat_waktu']

    def __str__(self):
        return f"{self.judul} ({self.get_status_display()})"

class LokasiKantor(TenantAwareModel):
    nama = models.CharField(_("Nama Kantor"), max_length=100)
    latitude = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6)
    radius_meter = models.IntegerField(_("Radius Toleransi (Meter)"), default=50, help_text=_("Jarak maksimal karyawan bisa absen dari titik kantor."))

    class Meta:
        verbose_name = _("Lokasi Kantor Absensi")
        verbose_name_plural = _("Lokasi Kantor")

    def __str__(self):
        return f"{self.nama} (Radius {self.radius_meter}m)"

class Absensi(TenantAwareModel):
    class Status(models.TextChoices):
        HADIR = 'HADIR', _('Hadir')
        TERLAMBAT = 'TERLAMBAT', _('Terlambat')
        IZIN = 'IZIN', _('Izin')
        SAKIT = 'SAKIT', _('Sakit')
        ALPA = 'ALPA', _('Tanpa Keterangan')

    pengurus = models.ForeignKey(
        'hr.Pengurus', 
        on_delete=models.CASCADE, 
        related_name='riwayat_absensi',
        verbose_name=_("Pengurus")
    )
    tanggal = models.DateField(_("Tanggal"), auto_now_add=True)
    
    # Masuk
    waktu_masuk = models.DateTimeField(_("Waktu Masuk"), null=True, blank=True)
    foto_masuk = models.ImageField(_("Foto Masuk"), upload_to='absensi_masuk/', null=True, blank=True)
    lokasi_masuk = models.CharField(_("Koordinat Masuk"), max_length=100, null=True, blank=True)
    
    # Pulang
    waktu_keluar = models.DateTimeField(_("Waktu Pulang"), null=True, blank=True)
    foto_keluar = models.ImageField(_("Foto Pulang"), upload_to='absensi_keluar/', null=True, blank=True)
    lokasi_keluar = models.CharField(_("Koordinat Pulang"), max_length=100, null=True, blank=True)
    
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.HADIR,
        verbose_name=_("Status Kehadiran")
    )
    catatan = models.TextField(_("Catatan / Keterangan"), blank=True)

    class Meta:
        verbose_name = _("Absensi Harian")
        verbose_name_plural = _("Data Absensi")
        ordering = ['-tanggal', '-waktu_masuk']
        unique_together = ['tenant', 'pengurus', 'tanggal']

    def __str__(self):
        return f"{self.pengurus.nama} - {self.tanggal}"

# --- MANAJEMEN KINERJA (KPI & AMALAN) ---

class PeriodePenilaian(TenantAwareModel):
    nama = models.CharField(_("Nama Periode"), max_length=100, help_text="Contoh: Q1 2025, Semester 1 2025")
    start_date = models.DateField(_("Tanggal Mulai"))
    end_date = models.DateField(_("Tanggal Selesai"))
    is_active = models.BooleanField(_("Aktif"), default=True)

    class Meta:
        verbose_name = _("Periode Penilaian")
        verbose_name_plural = _("Periode Penilaian")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.nama} ({self.start_date} - {self.end_date})"

class KamusKPI(TenantAwareModel):
    class Satuan(models.TextChoices):
        PERCENT = 'PERCENT', 'Persentase (%)'
        NUMBER = 'NUMBER', 'Angka (Nominal/Jumlah)'
        CURRENCY = 'CURRENCY', 'Mata Uang (Rp)'
    
    class Sumber(models.TextChoices):
        MANUAL = 'MANUAL', 'Input Manual'
        AUTO_ABSENSI = 'AUTO_ABSENSI', 'Otomatis: Absensi (Kehadiran)'
        AUTO_TUGAS = 'AUTO_TUGAS', 'Otomatis: Penyelesaian Tugas'
        AUTO_IBADAH = 'AUTO_IBADAH', 'Otomatis: Skor Ibadah (Amalan)'
        AUTO_SALES_LEAD = 'AUTO_SALES_LEAD', 'Otomatis: CRM (Leads Conversion)'
        AUTO_FINANCE_SPP = 'AUTO_FINANCE_SPP', 'Otomatis: Keuangan (Collection Rate)'
        AUTO_FUNDRAISING = 'AUTO_FUNDRAISING', 'Otomatis: Fundraising (Total Donasi)'

    nama = models.CharField(_("Nama Indikator"), max_length=200)
    deskripsi = models.TextField(_("Deskripsi & Cara Hitung"))
    satuan = models.CharField(_("Satuan"), max_length=20, choices=Satuan.choices)
    sumber_data = models.CharField(_("Sumber Data"), max_length=30, choices=Sumber.choices, default=Sumber.MANUAL)
    
    class Meta:
        verbose_name = _("Kamus KPI")
        verbose_name_plural = _("Kamus KPI")
        ordering = ['nama']

    def __str__(self):
        return f"{self.nama} [{self.get_sumber_data_display()}]"

# --- AMALAN YAUMIAH ---
class JenisAmalan(TenantAwareModel):
    nama = models.CharField(_("Nama Amalan"), max_length=150)
    poin = models.IntegerField(_("Bobot Poin"), default=1, help_text="Poin yang didapat jika dikerjakan.")
    is_wajib = models.BooleanField(_("Wajib?"), default=False, help_text="Jika wajib, tidak dikerjakan bisa mengurangi nilai.")
    kategori = models.CharField(_("Kategori"), max_length=50, blank=True, null=True, help_text="Contoh: Harian, Mingguan")

    class Meta:
        verbose_name = _("Jenis Amalan")
        verbose_name_plural = _("Jenis Amalan")
        ordering = ['nama']

    def __str__(self):
        return f"{self.nama} ({self.poin} Poin)"

class LogAmalan(TenantAwareModel):
    pengurus = models.ForeignKey(Pengurus, on_delete=models.CASCADE, related_name='log_amalan')
    tanggal = models.DateField(_("Tanggal"), auto_now_add=True)
    amalan = models.ForeignKey(JenisAmalan, on_delete=models.CASCADE)
    is_done = models.BooleanField(_("Dikerjakan"), default=False)
    keterangan = models.CharField(_("Keterangan"), max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _("Log Amalan")
        verbose_name_plural = _("Log Amalan")
        unique_together = ['pengurus', 'tanggal', 'amalan', 'tenant']
        ordering = ['-tanggal']

    def __str__(self):
        return f"{self.pengurus.nama} - {self.amalan.nama} ({self.tanggal})"

# --- TARGET & REALISASI KPI ---
class TargetKPI(TenantAwareModel):
    pengurus = models.ForeignKey(Pengurus, on_delete=models.CASCADE, related_name='target_kpi')
    periode = models.ForeignKey(PeriodePenilaian, on_delete=models.CASCADE)
    indikator = models.ForeignKey(KamusKPI, on_delete=models.CASCADE)
    target = models.DecimalField(_("Target"), max_digits=12, decimal_places=2)
    bobot = models.IntegerField(_("Bobot (%)"), help_text="Persentase kontribusi nilai ini terhadap total.")

    class Meta:
        verbose_name = _("Target KPI")
        verbose_name_plural = _("Target KPI")
        unique_together = ['pengurus', 'periode', 'indikator', 'tenant']

    def __str__(self):
        return f"{self.pengurus.nama} - {self.indikator.nama} (Target: {self.target})"

class RealisasiKPI(TenantAwareModel):
    target_kpi = models.OneToOneField(TargetKPI, on_delete=models.CASCADE, related_name='realisasi')
    realisasi = models.DecimalField(_("Realisasi"), max_digits=12, decimal_places=2)
    nilai_akhir = models.DecimalField(_("Skor Akhir (0-100)"), max_digits=5, decimal_places=2, blank=True, null=True)
    bukti_lampiran = models.FileField(_("Bukti Lampiran"), upload_to='bukti_kpi/', blank=True, null=True)
    catatan = models.TextField(_("Catatan Evaluasi"), blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Realisasi KPI")
        verbose_name_plural = _("Realisasi KPI")

    def __str__(self):
        return f"Realisasi: {self.target_kpi}"

    def save(self, *args, **kwargs):
        # Simple auto-calculation logic for score
        if self.target_kpi.target > 0:
            achieved = float(self.realisasi)
            target = float(self.target_kpi.target)
            score = (achieved / target) * 100
            self.nilai_akhir = min(score, 100.0) 
        super().save(*args, **kwargs)
