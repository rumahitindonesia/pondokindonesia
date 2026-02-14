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
