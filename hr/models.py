from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import TenantAwareModel
from django.conf import settings

from django.utils import timezone

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

class JadwalKerja(TenantAwareModel):
    """Work Schedule: Define working days and hours"""
    nama = models.CharField(_("Nama Jadwal"), max_length=100, help_text="Contoh: Senin-Jumat, Shift Pagi")
    
    # Working Days
    senin = models.BooleanField(_("Senin"), default=True)
    selasa = models.BooleanField(_("Selasa"), default=True)
    rabu = models.BooleanField(_("Rabu"), default=True)
    kamis = models.BooleanField(_("Kamis"), default=True)
    jumat = models.BooleanField(_("Jumat"), default=True)
    sabtu = models.BooleanField(_("Sabtu"), default=False)
    minggu = models.BooleanField(_("Minggu"), default=False)
    
    # Work Hours
    jam_masuk = models.TimeField(_("Jam Masuk"), default="08:00")
    jam_pulang = models.TimeField(_("Jam Pulang"), default="17:00")
    toleransi_telat = models.IntegerField(
        _("Toleransi Terlambat (Menit)"), 
        default=15,
        help_text="Menit keterlambatan yang masih dianggap 'Hadir'"
    )
    
    is_active = models.BooleanField(_("Aktif"), default=True)

    class Meta:
        verbose_name = _("Jadwal Kerja")
        verbose_name_plural = _("Jadwal Kerja")
        ordering = ['nama']

    def __str__(self):
        return self.nama
    
    def is_working_day(self, date):
        """Check if given date is a working day"""
        weekday = date.weekday()  # 0=Monday, 6=Sunday
        days = [self.senin, self.selasa, self.rabu, self.kamis, self.jumat, self.sabtu, self.minggu]
        return days[weekday]


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
    
    jadwal_kerja = models.ForeignKey(
        'JadwalKerja',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_list',
        verbose_name=_("Jadwal Kerja"),
        help_text=_("Jadwal kerja yang berlaku untuk staff ini")
    )
    
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

    # Linked OKR (Initiative)
    key_result = models.ForeignKey(
        'hr.KeyResult',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initiatives',
        verbose_name=_("Mendukung Key Result"),
        help_text=_("Pilih Key Result yang didukung oleh tugas ini (Inisiatif).")
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
    tanggal = models.DateField(_("Tanggal"), default=timezone.now)
    
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
    
    def save(self, *args, **kwargs):
        # Auto-detect late status based on work schedule
        if self.waktu_masuk and self.pengurus.jadwal_kerja:
            jadwal = self.pengurus.jadwal_kerja
            
            # Check if today is a working day
            if not jadwal.is_working_day(self.tanggal):
                # Optional: Set status to special value or just save as-is
                pass
            else:
                # Compare clock-in time with scheduled time
                from datetime import datetime, timedelta
                
                waktu_masuk_time = self.waktu_masuk.time()
                jam_masuk_scheduled = jadwal.jam_masuk
                
                # Calculate late threshold
                late_threshold = (
                    datetime.combine(self.tanggal, jam_masuk_scheduled) + 
                    timedelta(minutes=jadwal.toleransi_telat)
                ).time()
                
                # Auto-set status if not manually overridden
                if waktu_masuk_time > late_threshold:
                    if self.status == self.Status.HADIR:  # Only auto-change if still default
                        self.status = self.Status.TERLAMBAT
        
        super().save(*args, **kwargs)

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
    tanggal = models.DateField(_("Tanggal"), default=timezone.now)
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

# --- OKR (OBJECTIVES & KEY RESULTS) ---

class Objective(TenantAwareModel):
    judul = models.CharField(_("Objective (Tujuan)"), max_length=255, help_text="Tujuan Strategis, misal: 'Menjadi Market Leader'")
    owner = models.ForeignKey(Pengurus, on_delete=models.CASCADE, related_name='objectives', verbose_name=_("Owner"))
    periode = models.ForeignKey(PeriodePenilaian, on_delete=models.CASCADE, verbose_name=_("Periode"))
    progress = models.DecimalField(_("Progress (%)"), max_digits=5, decimal_places=2, default=0.0)
    is_active = models.BooleanField(_("Aktif"), default=True)

    class Meta:
        verbose_name = _("Objective")
        verbose_name_plural = _("Objectives")
        ordering = ['-id']

    def __str__(self):
        return f"{self.judul} ({self.progress}%)"

    def calculate_progress(self):
        krs = self.key_results.all()
        if not krs.exists():
            return 0.0
        
        # Average of KR progress (normalized to 100%)
        # Logic: Sum(KR.achieved_percent) / Count(KR)
        total_percent = 0
        for kr in krs:
            if kr.target > 0:
                percent = (kr.current_value / kr.target) * 100
                total_percent += min(percent, 100) # Cap at 100% per KR to avoid skewing
            else:
                total_percent += 0 # Avoid division by zero
        
        avg = total_percent / krs.count()
        return round(avg, 2)

class KeyResult(TenantAwareModel):
    class Mode(models.TextChoices):
        MANUAL = 'MANUAL', _('Manual Input')
        AUTO = 'AUTO', _('Otomatis (System)')

    objective = models.ForeignKey(Objective, on_delete=models.CASCADE, related_name='key_results')
    judul = models.CharField(_("Key Result"), max_length=255, help_text="ukuran keberhasilan, misal: '1000 Santri Baru'")
    target = models.DecimalField(_("Target"), max_digits=12, decimal_places=2)
    current_value = models.DecimalField(_("Realisasi Saat Ini"), max_digits=12, decimal_places=2, default=0)
    unit = models.CharField(_("Satuan"), max_length=50, blank=True, help_text="Contoh: Santri, Rp, %, Leads")
    
    # Auto-Calculation
    mode = models.CharField(_("Mode Pengisian"), max_length=20, choices=Mode.choices, default=Mode.MANUAL)
    source = models.CharField(
        _("Sumber Data Otomatis"), 
        max_length=50, 
        choices=KamusKPI.Sumber.choices, 
        blank=True, 
        null=True,
        help_text="Pilih sumber data jika Mode = Otomatis"
    )

    class Meta:
        verbose_name = _("Key Result")
        verbose_name_plural = _("Key Results")

    def __str__(self):
        return f"{self.judul} ({self.current_value}/{self.target} {self.unit})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update Parent Objective Progress
        new_progress = self.objective.calculate_progress()
        self.objective.progress = new_progress
        self.objective.save()
