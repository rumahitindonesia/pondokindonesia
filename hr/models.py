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
