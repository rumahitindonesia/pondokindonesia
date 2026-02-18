from django.db import models
from core.models import TenantAwareModel

class Program(TenantAwareModel):
    class Jenis(models.TextChoices):
        TAGIHAN = 'TAGIHAN', 'Tagihan / SPP'
        DONASI = 'DONASI', 'Program Donasi'
        PENDAFTARAN = 'PENDAFTARAN', 'Biaya Pendaftaran'

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
        CALON = 'CALON', 'Calon Santri'
        AKTIF = 'AKTIF', 'Aktif'
        LULUS = 'LULUS', 'Lulus / Alumni'
        CUTI = 'CUTI', 'Cuti'
        KELUAR = 'KELUAR', 'Keluar / DO'

    class StatusSeleksi(models.TextChoices):
        BELUM_TES = 'BELUM_TES', 'Belum Tes'
        WAWANCARA = 'WAWANCARA', 'Proses Wawancara'
        LULUS = 'LULUS', 'Lulus Seleksi'
        GAGAL = 'GAGAL', 'Tidak Lulus'
        
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
    status_seleksi = models.CharField(
        max_length=20, 
        choices=StatusSeleksi.choices, 
        default=StatusSeleksi.BELUM_TES,
        help_text="Status tahapan seleksi masuk"
    )
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

class TransaksiDonasi(TenantAwareModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Menunggu Verifikasi'
        VERIFIED = 'VERIFIED', 'Terverifikasi'
        REJECTED = 'REJECTED', 'Ditolak'

    donatur = models.ForeignKey(Donatur, on_delete=models.CASCADE, related_name='donasi')
    program = models.ForeignKey(Program, on_delete=models.CASCADE) # Removed limit_choices_to
    
    nominal = models.DecimalField(max_digits=12, decimal_places=0)
    tgl_donasi = models.DateTimeField(auto_now_add=True)
    bukti_transfer = models.ImageField(upload_to='bukti_donasi/', blank=True, null=True)
    external_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID Transaksi iPaymu")
    payment_url = models.URLField(blank=True, null=True, help_text="Link Pembayaran iPaymu")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    keterangan = models.TextField(blank=True, null=True)

    @property
    def nominal_display(self):
        if self.nominal is None:
            return "-"
        return f"Rp {self.nominal:,.0f}"

    class Meta:
        verbose_name = "Transaksi Donasi"
        verbose_name_plural = "Transaksi Donasi"
        ordering = ['-tgl_donasi']

    def __str__(self):
        return f"{self.program.nama_program} - {self.donatur.nama_donatur} ({self.nominal})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        status_changed_to_verified = False
        
        if not is_new:
            try:
                old = TransaksiDonasi.objects.get(pk=self.pk)
                if old.status != self.Status.VERIFIED and self.status == self.Status.VERIFIED:
                    status_changed_to_verified = True
            except: pass
            
        super().save(*args, **kwargs)
        
        if status_changed_to_verified:
            self.send_success_notification()

    def send_success_notification(self):
        from core.services.starsender import StarSenderService
        
        phone = self.donatur.no_hp
        if not phone: return
        
        # Different message for Donation vs Registration
        if self.program.jenis == Program.Jenis.PENDAFTARAN:
            msg = (
                f"Alhamdulillah, pembayaran biaya pendaftaran santri sebesar *Rp {self.nominal:,.0f}* "
                f"telah kami terima.\n\n"
                f"Silakan lengkapi formulir pendaftaran santri melalui link berikut:\n"
                f"https://pondokindonesia.online/pendaftaran/form/{self.id}\n\n"
                f"Jika ada kendala, silakan hubungi kami kembali. Terima kasih."
            )
        else:
            msg = (
                f"Alhamdulillah, terima kasih atas donasi Anda sebesar *Rp {self.nominal:,.0f}* "
                f"untuk program *{self.program.nama_program}*.\n\n"
                f"Semoga menjadi amal jariah yang tak terputus pahalanya. Aamiin.\n"
                f"_{self.tenant.name if self.tenant else 'Pondok IT'}_"
            )

        try:
            StarSenderService.send_message(to=phone, body=msg, tenant=self.tenant)
        except Exception as e:
            print(f"Failed to send donation notification: {e}")

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

    @property
    def jumlah_display(self):
        if self.jumlah is None:
            return "-"
        return f"Rp {self.jumlah:,.0f}"

    @property
    def bulan_display(self):
        if not self.bulan:
            return "-"
        return self.bulan.strftime('%B %Y')
    
    program = models.ForeignKey(
        Program, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'jenis': Program.Jenis.TAGIHAN},
        related_name='tagihan_spp',
        verbose_name="Program"
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
    
    tanggal_bayar = models.DateField(
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

    # Payment Gateway Fields
    external_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID Transaksi iPaymu (Session ID)")
    payment_url = models.URLField(blank=True, null=True, help_text="Link Pembayaran iPaymu")

    @property
    def tgl_buat(self):
        return self.created_at
    
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
        from django.utils import timezone
        
        # Check if status changed to LUNAS
        is_new = self.pk is None
        status_changed_to_lunas = False
        
        if not is_new:
            try:
                old_instance = TagihanSPP.objects.get(pk=self.pk)
                if old_instance.status != self.Status.LUNAS and self.status == self.Status.LUNAS:
                    status_changed_to_lunas = True
            except TagihanSPP.DoesNotExist:
                pass # Should not happen

        # Auto-update status to LUNAS if tanggal_bayar is set
        if self.tanggal_bayar:
             self.status = self.Status.LUNAS
             # Also trigger if it wasn't lunas before (redundant check but safe)
             if not is_new:
                 try:
                     old = TagihanSPP.objects.get(pk=self.pk)
                     if old.status != self.Status.LUNAS:
                         status_changed_to_lunas = True
                 except: pass
        
        # Auto-fill tanggal_bayar if status is LUNAS but date is missing
        elif self.status == self.Status.LUNAS and not self.tanggal_bayar:
            self.tanggal_bayar = timezone.now().date()
            status_changed_to_lunas = True

        # Auto-update status to TERLAMBAT if overdue and not paid
        elif self.status == self.Status.BELUM_LUNAS and self.jatuh_tempo < timezone.now().date():
            self.status = self.Status.TERLAMBAT
            
        super().save(*args, **kwargs)

        # Send WhatsApp Notification if Lunas
        if status_changed_to_lunas:
            self.send_lunas_notification()
    
    def send_lunas_notification(self):
        """Send WhatsApp notification to Wali Santri when paid"""
        from core.services.starsender import StarSenderService
        
        phone = self.santri.no_hp_wali
        if not phone:
            return

        amount_fmt = f"Rp {self.jumlah:,.0f}"
        bulan_str = self.bulan.strftime('%B %Y')
        santri_name = self.santri.nama_lengkap
        
        message = (
            f"Alhamdulillah, pembayaran SPP Ananda *{santri_name}* untuk bulan *{bulan_str}* "
            f"sebesar *{amount_fmt}* telah kami terima.\n\n"
            f"Semoga Allah memberkahi rezeki Bapak/Ibu dan memudahkan segala urusan.\n"
            f"Jazakumullah Khairan Katsiran.\n"
            f"_{self.tenant.name if self.tenant else 'Pondok IT'}_"
        )
        
        try:
            StarSenderService.send_message(
                to=phone,
                body=message,
                tenant=self.tenant
            )
        except Exception as e:
            # Log error silently
            print(f"Failed to send WA notification: {e}")



class TagihanProgram(TenantAwareModel):
    """
    Tagihan untuk program non-bulanan (Pendaftaran, Wakaf, Pre-program, dll)
    """
    class Status(models.TextChoices):
        BELUM_LUNAS = 'BELUM', 'Belum Lunas'
        LUNAS = 'LUNAS', 'Lunas'
        TERLAMBAT = 'TERLAMBAT', 'Terlambat'

    santri = models.ForeignKey(Santri, on_delete=models.CASCADE, related_name='tagihan_program', verbose_name="Santri")
    program = models.ForeignKey(
        Program, 
        on_delete=models.CASCADE, 
        related_name='tagihan_program_set',
        # Allow both Tagihan/SPP and Pendaftaran
        limit_choices_to=models.Q(jenis='TAGIHAN') | models.Q(jenis='PENDAFTARAN'),
        verbose_name="Program"
    )
    
    nominal = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Nominal")
    jatuh_tempo = models.DateField(verbose_name="Jatuh Tempo")
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BELUM_LUNAS,
        verbose_name="Status"
    )
    
    tanggal_bayar = models.DateField(null=True, blank=True, verbose_name="Tanggal Bayar")

    @property
    def nominal_display(self):
        if self.nominal is None:
            return "-"
        return f"Rp {self.nominal:,.0f}"
    catatan = models.TextField(blank=True, verbose_name="Catatan")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Payment Gateway Fields
    external_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID Transaksi iPaymu (Session ID)")
    payment_url = models.URLField(blank=True, null=True, help_text="Link Pembayaran iPaymu")

    class Meta:
        verbose_name = "Tagihan Program"
        verbose_name_plural = "Tagihan Program"
        ordering = ['-jatuh_tempo']

    def __str__(self):
        return f"{self.program.nama_program} - {self.santri.nama_lengkap}"

    def save(self, *args, **kwargs):
        from django.utils import timezone
        
        # Check if status changed to LUNAS
        is_new = self.pk is None
        status_changed_to_lunas = False
        
        if not is_new:
            try:
                old_instance = TagihanProgram.objects.get(pk=self.pk)
                if old_instance.status != self.Status.LUNAS and self.status == self.Status.LUNAS:
                    status_changed_to_lunas = True
            except TagihanProgram.DoesNotExist:
                pass

        if self.tanggal_bayar:
            self.status = self.Status.LUNAS
            # Also trigger if it wasn't lunas before
            if not is_new:
                 try:
                     old = TagihanProgram.objects.get(pk=self.pk)
                     if old.status != self.Status.LUNAS:
                         status_changed_to_lunas = True
                 except: pass
        elif self.status == self.Status.LUNAS and not self.tanggal_bayar:
            # Auto-fill tanggal_bayar if status is LUNAS but date is missing
            self.tanggal_bayar = timezone.now().date()
            status_changed_to_lunas = True

        super().save(*args, **kwargs)

        # Send WhatsApp Notification if Lunas
        if status_changed_to_lunas:
            self.send_lunas_notification()
    
    def send_lunas_notification(self):
        """Send WhatsApp notification to Wali Santri when paid"""
        from core.services.starsender import StarSenderService
        
        phone = self.santri.no_hp_wali
        if not phone:
            return

        amount_fmt = f"Rp {self.nominal:,.0f}"
        program_name = self.program.nama_program
        santri_name = self.santri.nama_lengkap
        
        # --- LOGIC 1: REGISTRATION (Biaya Pendaftaran) ---
        if self.program.jenis == Program.Jenis.PENDAFTARAN:
            # Send Form Link
            # Link format: https://{subdomain}.pondokindonesia.online/pendaftaran/form/{id}
            subdomain = self.tenant.subdomain if self.tenant else 'www'
            form_link = f"https://{subdomain}.pondokindonesia.online/pendaftaran/form/{self.santri.id}"
            
            message = (
                f"Alhamdulillah, pembayaran *Biaya Pendaftaran* untuk Ananda *{santri_name}* "
                f"sebesar *{amount_fmt}* telah kami terima.\n\n"
                f"Langkah selanjutnya, silakan lengkapi formulir pendaftaran melalui link berikut:\n"
                f"{form_link}\n\n"
                f"Jika ada kendala, silakan hubungi kami kembali. Terima kasih.\n"
                f"_{self.tenant.name if self.tenant else 'Pondok IT'}_"
            )

        # --- LOGIC 2: EDUCATION (Biaya Pendidikan/Uang Pangkal) ---
        elif 'pendidikan' in program_name.lower() or 'pangkal' in program_name.lower():
            # Activate Santri
            if self.santri.status == Santri.Status.CALON:
                self.santri.status = Santri.Status.AKTIF
                self.santri.save()
            
            message = (
                f"Alhamdulillah, pembayaran *{program_name}* untuk Ananda *{santri_name}* "
                f"sebesar *{amount_fmt}* telah kami terima.\n\n"
                f"Selamat! Ananda resmi diterima sebagai Santri di {self.tenant.name if self.tenant else 'Pondok IT'}.\n"
                f"Semoga Allah memberkahi perjalanan menuntut ilmunya. Aamiin.\n\n"
                f"Jazakumullah Khairan Katsiran."
            )

        # --- DEFAULT LOGIC ---
        else:
            message = (
                f"Alhamdulillah, pembayaran tagihan program *{program_name}* untuk Ananda *{santri_name}* "
                f"sebesar *{amount_fmt}* telah kami terima.\n\n"
                f"Semoga Allah memberkahi rezeki Bapak/Ibu dan memudahkan segala urusan.\n"
                f"Jazakumullah Khairan Katsiran.\n"
                f"_{self.tenant.name if self.tenant else 'Pondok IT'}_"
            )
        
        try:
            StarSenderService.send_message(
                to=phone,
                body=message,
                tenant=self.tenant
            )
        except Exception as e:
            print(f"Failed to send WA notification: {e}")

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
