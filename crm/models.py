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
    
    # Performance Attribution
    pic_admin = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='santri_handled',
        verbose_name="PIC Admin / Wali Asuh",
        help_text="Staff yang bertanggung jawab atas penagihan SPP santri ini."
    )
    
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
    
    # Performance Attribution
    pic_fundraiser = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='donatur_handled',
        verbose_name="PIC Fundraiser",
        help_text="Staff yang bertanggung jawab atas donatur ini."
    )

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
    external_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID Transaksi iPaymu")
    payment_url = models.URLField(blank=True, null=True, help_text="Link Pembayaran iPaymu")
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
    external_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID Transaksi iPaymu")
    payment_url = models.URLField(blank=True, null=True, help_text="Link Pembayaran iPaymu")
    keterangan = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Transaksi Donasi"
        verbose_name_plural = "Transaksi Donasi"
        ordering = ['-tgl_donasi']

    def __str__(self):
        return f"{self.program.nama_program} - {self.donatur.nama_donatur} ({self.nominal})"

class TagihanSPP(TenantAwareModel):
    """Monthly tuition fee bills for Santri"""
    class Status(models.TextChoices):
        BELUM_LUNAS = 'BELUM_LUNAS', 'Belum Lunas'
        LUNAS = 'LUNAS', 'Lunas'
        TERLAMBAT = 'TERLAMBAT', 'Terlambat'
    
    santri = models.ForeignKey(
        'Santri',
        on_delete=models.CASCADE,
        related_name='tagihan_spp',
        verbose_name="Santri"
    )
    
    bulan = models.DateField(
        verbose_name="Bulan Tagihan",
        help_text="Tanggal 1 dari bulan yang ditagih (e.g., 2026-02-01 untuk Feb 2026)"
    )
    
    jumlah = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="Jumlah Tagihan",
        help_text="Nominal tagihan SPP bulan ini"
    )
    
    jatuh_tempo = models.DateField(
        verbose_name="Jatuh Tempo",
        help_text="Batas waktu pembayaran"
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BELUM_LUNAS,
        verbose_name="Status Pembayaran"
    )
    
    tanggal_bayar = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Tanggal Pembayaran"
    )
    
    catatan = models.TextField(
        blank=True,
        verbose_name="Catatan",
        help_text="Catatan tambahan untuk tagihan ini"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tagihan SPP"
        verbose_name_plural = "Tagihan SPP"
        ordering = ['-bulan', 'santri']
        unique_together = ['santri', 'bulan', 'tenant']
    
    def __str__(self):
        from datetime import datetime
        bulan_str = self.bulan.strftime('%B %Y') if isinstance(self.bulan, datetime) else str(self.bulan)
        return f"{self.santri.nama_lengkap} - {bulan_str}"
    
    def is_overdue(self):
        """Check if payment is overdue"""
        from django.utils import timezone
        if self.status == self.Status.LUNAS:
            return False
        return timezone.now().date() > self.jatuh_tempo
    
    def save(self, *args, **kwargs):
        # Auto-update status to TERLAMBAT if overdue
        if self.is_overdue() and self.status == self.Status.BELUM_LUNAS:
            self.status = self.Status.TERLAMBAT
        super().save(*args, **kwargs)


class PaymentMethodSetting(TenantAwareModel):
    """Payment method settings for manual payments (Bank Transfer & QRIS)"""
    class MethodType(models.TextChoices):
        BANK_TRANSFER = 'BANK_TRANSFER', 'Transfer Bank'
        QRIS = 'QRIS', 'QRIS'
    
    method_type = models.CharField(
        max_length=20,
        choices=MethodType.choices,
        verbose_name="Jenis Metode"
    )
    
    # For Bank Transfer
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nama Bank",
        help_text="Contoh: BCA, Mandiri, BRI"
    )
    account_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Nomor Rekening"
    )
    account_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Nama Pemilik Rekening"
    )
    
    # For QRIS
    qris_image = models.ImageField(
        upload_to='payment_methods/qris/',
        blank=True,
        null=True,
        verbose_name="Gambar QRIS",
        help_text="Upload gambar QRIS untuk pembayaran"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif"
    )
    
    display_order = models.IntegerField(
        default=0,
        verbose_name="Urutan Tampilan",
        help_text="Urutan tampilan di halaman pembayaran (lebih kecil = lebih atas)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Metode Pembayaran"
        verbose_name_plural = "Metode Pembayaran"
        ordering = ['display_order', 'method_type']
    
    def __str__(self):
        if self.method_type == self.MethodType.BANK_TRANSFER:
            return f"{self.bank_name} - {self.account_number}"
        else:
            return "QRIS"


class PembayaranSPP(TenantAwareModel):
    """Manual payment records for SPP bills"""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Menunggu Verifikasi'
        VERIFIED = 'VERIFIED', 'Terverifikasi'
        REJECTED = 'REJECTED', 'Ditolak'
    
    tagihan = models.ForeignKey(
        'TagihanSPP',
        on_delete=models.CASCADE,
        related_name='pembayaran',
        verbose_name="Tagihan SPP"
    )
    
    payment_method = models.ForeignKey(
        'PaymentMethodSetting',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Metode Pembayaran"
    )
    
    jumlah_bayar = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="Jumlah Dibayar"
    )
    
    bukti_transfer = models.ImageField(
        upload_to='bukti_pembayaran/',
        verbose_name="Bukti Transfer"
    )
    
    tanggal_transfer = models.DateField(
        verbose_name="Tanggal Transfer",
        help_text="Tanggal melakukan transfer"
    )
    
    catatan_pembayar = models.TextField(
        blank=True,
        verbose_name="Catatan",
        help_text="Catatan tambahan dari pembayar"
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status Verifikasi"
    )
    
    # Admin verification fields
    verified_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments',
        verbose_name="Diverifikasi Oleh"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Waktu Verifikasi"
    )
    catatan_admin = models.TextField(
        blank=True,
        verbose_name="Catatan Admin",
        help_text="Catatan dari admin saat verifikasi"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pembayaran SPP"
        verbose_name_plural = "Pembayaran SPP"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tagihan.santri.nama_lengkap} - {self.tagihan.bulan.strftime('%B %Y')} - Rp {self.jumlah_bayar:,.0f}"
    
    def save(self, *args, **kwargs):
        # Auto-update tagihan status when payment is verified
        if self.status == self.Status.VERIFIED and self.tagihan.status != 'LUNAS':
            from django.utils import timezone
            self.tagihan.status = 'LUNAS'
            self.tagihan.tanggal_bayar = timezone.now()
            self.tagihan.save()
        super().save(*args, **kwargs)
