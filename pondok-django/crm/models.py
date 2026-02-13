from django.db import models
from core.models import TenantAwareModel

class Program(TenantAwareModel):
    class Jenis(models.TextChoices):
        TAGIHAN = 'TAGIHAN', 'Tagihan / SPP'
        DONASI = 'DONASI', 'Program Donasi'

    nama_program = models.CharField(max_length=150)
    jenis = models.CharField(max_length=20, choices=Jenis.choices, default=Jenis.TAGIHAN)
    nominal_standar = models.DecimalField(max_digits=12, decimal_places=0, default=0, help_text="Nominal default (bisa diubah saat transaksi)")
    keterangan = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Master Program"
        verbose_name_plural = "Master Program"
        ordering = ['nama_program']

    def __str__(self):
        return f"{self.nama_program} ({self.get_jenis_display()})"

class Santri(TenantAwareModel):
    class Status(models.TextChoices):
        AKTIF = 'AKTIF', 'Aktif'
        LULUS = 'LULUS', 'Lulus / Alumni'
        CUTI = 'CUTI', 'Cuti'
        KELUAR = 'KELUAR', 'Keluar / DO'

    nis = models.CharField(max_length=50, help_text="Nomor Induk Santri (Unik per Tenant)")
    nama_lengkap = models.CharField(max_length=150)
    nama_panggilan = models.CharField(max_length=50, blank=True, null=True)
    tgl_lahir = models.DateField(blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    
    nama_wali = models.CharField(max_length=150)
    no_hp_wali = models.CharField(max_length=50, help_text="Nomor WhatsApp Wali")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AKTIF)
    tgl_masuk = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Data Santri"
        verbose_name_plural = "Data Santri"
        unique_together = ('nis', 'tenant')
        ordering = ['nama_lengkap']

    def __str__(self):
        return f"{self.nama_lengkap} ({self.nis})"

class Donatur(TenantAwareModel):
    class Kategori(models.TextChoices):
        TETAP = 'TETAP', 'Donatur Tetap'
        INSIDENTIL = 'INSIDENTIL', 'Donatur Insidentil'

    kode_donatur = models.CharField(max_length=50, blank=True, null=True, help_text="Auto-generated if empty")
    nama_donatur = models.CharField(max_length=150)
    no_hp = models.CharField(max_length=50, help_text="Nomor WhatsApp")
    kategori = models.CharField(max_length=20, choices=Kategori.choices, default=Kategori.INSIDENTIL)
    alamat = models.TextField(blank=True, null=True)
    tgl_bergabung = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Data Donatur"
        verbose_name_plural = "Data Donatur"
        ordering = ['nama_donatur']

    def __str__(self):
        return f"{self.nama_donatur} ({self.get_kategori_display()})"

class Tagihan(TenantAwareModel):
    class Status(models.TextChoices):
        BELUM_LUNAS = 'BELUM', 'Belum Lunas'
        LUNAS = 'LUNAS', 'Lunas'

    santri = models.ForeignKey(Santri, on_delete=models.CASCADE, related_name='tagihan')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, limit_choices_to={'jenis': Program.Jenis.TAGIHAN})
    
    nominal = models.DecimalField(max_digits=12, decimal_places=0)
    bulan = models.CharField(max_length=20, blank=True, null=True, help_text="Contoh: Januari 2024")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BELUM_LUNAS)
    tgl_buat = models.DateTimeField(auto_now_add=True)
    tgl_bayar = models.DateTimeField(blank=True, null=True)
    bukti_bayar = models.ImageField(upload_to='bukti_bayar/', blank=True, null=True)
    keterangan = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Tagihan / SPP"
        verbose_name_plural = "Tagihan / SPP"
        ordering = ['-tgl_buat']

    def __str__(self):
        return f"{self.program.nama_program} - {self.santri.nama_lengkap} ({self.get_status_display()})"

class TransaksiDonasi(TenantAwareModel):
    donatur = models.ForeignKey(Donatur, on_delete=models.CASCADE, related_name='donasi')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, limit_choices_to={'jenis': Program.Jenis.DONASI})
    
    nominal = models.DecimalField(max_digits=12, decimal_places=0)
    tgl_donasi = models.DateTimeField(auto_now_add=True)
    bukti_transfer = models.ImageField(upload_to='bukti_donasi/', blank=True, null=True)
    keterangan = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Transaksi Donasi"
        verbose_name_plural = "Transaksi Donasi"
        ordering = ['-tgl_donasi']

    def __str__(self):
        return f"{self.program.nama_program} - {self.donatur.nama_donatur} ({self.nominal})"
