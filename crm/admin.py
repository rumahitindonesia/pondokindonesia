from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportMixin
from django.utils import timezone
from django.contrib import messages
from .models import Program, Santri, Donatur, TransaksiDonasi, TagihanSPP, TagihanProgram, PaymentMethodSetting, PembayaranSPP
from users.models import User
from core.services.ipaymu import IPaymuService
from core.services.subscription import SubscriptionService
from core.admin import BaseTenantAdmin
from .resources import SantriResource, DonaturResource, ProgramResource, TransaksiDonasiResource, TagihanSPPResource, TagihanProgramResource

from core.services.starsender import StarSenderService

@admin.register(Program)
class ProgramAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [ProgramResource]

    list_display = ('nama_program', 'jenis', 'nominal_standar', 'scope', 'is_active')
    list_filter = ('jenis', 'is_active', 'tenant')
    search_fields = ('nama_program',)

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_resource_kwargs(request, *args, **kwargs)
        kwargs['request'] = request
        return kwargs
    
    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

from unfold.admin import TabularInline

class TagihanSPPInline(TabularInline):
    model = TagihanSPP
    tab = True
    extra = 0
    fields = ('bulan_display', 'program', 'jumlah_display', 'jatuh_tempo', 'status', 'tanggal_bayar')
    readonly_fields = ('bulan_display', 'jumlah_display', 'created_at')

class TagihanProgramInline(TabularInline):
    model = TagihanProgram
    tab = True
    extra = 0
    fields = ('program', 'nominal_display', 'jatuh_tempo', 'status', 'tanggal_bayar')
    readonly_fields = ('nominal_display', 'created_at')

@admin.register(Santri)
class SantriAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [SantriResource]
    inlines = [TagihanSPPInline, TagihanProgramInline]

    list_display = ('nis', 'nama_lengkap', 'status', 'nama_wali', 'scope')
    list_filter = ('status', 'tenant')
    search_fields = ('nis', 'nama_lengkap', 'nama_wali', 'no_hp_wali')

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_resource_kwargs(request, *args, **kwargs)
        kwargs['request'] = request
        return kwargs

    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

    def save_model(self, request, obj, form, change):
        if not change: # Adding new Santri
            tenant = getattr(request, 'tenant', None)
            if not tenant and not request.user.is_superuser:
                tenant = getattr(request.user, 'tenant', None)
            
            if SubscriptionService.check_quota_reached(tenant, Santri):
                from django.core.exceptions import ValidationError
                limit = tenant.subscription.plan.max_santri if hasattr(tenant, 'subscription') and tenant.subscription.plan else 0
                raise ValidationError(f"Batas kuota Santri untuk paket Anda telah tercapai ({limit} santri). Silakan upgrade paket.")
        
        super().save_model(request, obj, form, change)

@admin.register(Donatur)
class DonaturAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [DonaturResource]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
        self.import_template_name = "admin/import_export/import.html"
        self.export_template_name = "admin/import_export/export.html"
    resource_classes = [DonaturResource]
    list_display = ('nama_donatur', 'kategori', 'no_hp', 'scope', 'tgl_bergabung')
    list_filter = ('kategori', 'tenant')
    search_fields = ('nama_donatur', 'no_hp')
    actions = ['send_solicitation_whatsapp']

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_resource_kwargs(request, *args, **kwargs)
        kwargs['request'] = request
        return kwargs

    @admin.action(description='Send Solicitation (AI Generator)')
    def send_solicitation_whatsapp(self, request, queryset):
        if queryset.exists():
            tenant = queryset.first().tenant
            if not SubscriptionService.check_feature_access(tenant, 'can_use_ai'):
                self.message_user(request, "Fitur AI tidak tersedia di paket Anda.", messages.ERROR)
                return
            if not SubscriptionService.check_feature_access(tenant, 'can_use_whatsapp'):
                self.message_user(request, "Fitur WhatsApp tidak tersedia di paket Anda.", messages.ERROR)
                return

        from core.services.ai_crm_assistant import AICRMAssistant
        count = 0
        for donatur in queryset:
             if not donatur.no_hp:
                continue
             
             # Generate Dynamic Message
             msg = AICRMAssistant.generate_solicitation_message(donatur)
             
             if msg:
                 StarSenderService.send_message(
                     to=donatur.no_hp, 
                     body=msg, 
                     tenant=donatur.tenant
                 )
                 count += 1
        self.message_user(request, f"{count} solicitation messages sent.")

    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

    def save_model(self, request, obj, form, change):
        if not change: # Adding new Donatur
            tenant = getattr(request, 'tenant', None)
            if not tenant and not request.user.is_superuser:
                tenant = getattr(request.user, 'tenant', None)
                
            if SubscriptionService.check_quota_reached(tenant, Donatur):
                from django.core.exceptions import ValidationError
                limit = tenant.subscription.plan.max_donatur if hasattr(tenant, 'subscription') and tenant.subscription.plan else 0
                raise ValidationError(f"Batas kuota Donatur untuk paket Anda telah tercapai ({limit} donatur). Silakan upgrade paket.")
        
        super().save_model(request, obj, form, change)

@admin.register(TransaksiDonasi)
class TransaksiDonasiAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [TransaksiDonasiResource]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
        self.import_template_name = "admin/import_export/import.html"
        self.export_template_name = "admin/import_export/export.html"
    resource_classes = [TransaksiDonasiResource]
    list_display = ('program', 'donatur', 'nominal', 'status', 'tgl_donasi')
    list_filter = ('program', 'status', 'tenant')
    search_fields = ('donatur__nama_donatur', 'program__nama_program')
    actions = ['send_receipt_whatsapp', 'generate_ipaymu_link']

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_resource_kwargs(request, *args, **kwargs)
        kwargs['request'] = request
        return kwargs

    @admin.action(description='Send Receipt (Bukti Terima) via WhatsApp')
    def send_receipt_whatsapp(self, request, queryset):
        count = 0
        for trx in queryset:
            if not trx.donatur.no_hp:
                continue
                
            nominal = "{:,.0f}".format(trx.nominal).replace(',', '.')
            
            msg = f"Assalamualaikum Warahmatullahi Wabarakatuh.\n\nTerima kasih kepada Bpk/Ibu *{trx.donatur.nama_donatur}* atas donasinya sebesar *Rp {nominal}* untuk program *{trx.program.nama_program}*.\n\nSemoga menjadi amal jariyah dan dibalas dengan kebaikan berlipat ganda oleh Allah SWT.\n\nJazakumullah Khairan Katsiran.\n{trx.donatur.tenant.name}"
            
            StarSenderService.send_message(
                to=trx.donatur.no_hp,
                body=msg,
                tenant=trx.donatur.tenant
            )
            count += 1

        self.message_user(request, f"{count} receipts sent via WhatsApp.")

@admin.register(TagihanSPP)
class TagihanSPPAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [TagihanSPPResource]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
        self.import_template_name = "admin/import_export/import.html"
        self.export_template_name = "admin/import_export/export.html"
    
    list_display = ['santri', 'program', 'bulan_display', 'jumlah_display', 'jatuh_tempo', 'status', 'tanggal_bayar', 'tenant']
    list_filter = ['status', 'program', 'bulan', 'jatuh_tempo', 'tenant']
    search_fields = ['santri__nama_lengkap', 'santri__nis']
    date_hierarchy = 'bulan'
    
    fieldsets = (
        (None, {
            'fields': ('santri', 'program', 'bulan', 'jumlah', 'jatuh_tempo')
        }),
        ('Status Pembayaran', {
            'fields': ('status', 'tanggal_bayar', 'catatan')
        }),
    )
    
    search_fields = ['santri__nama_lengkap', 'santri__nis']
    date_hierarchy = 'bulan'

@admin.register(TagihanProgram)
class TagihanProgramAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [TagihanProgramResource]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
        self.import_template_name = "admin/import_export/import.html"
        self.export_template_name = "admin/import_export/export.html"
    
    list_display = ['santri', 'program', 'nominal_display', 'jatuh_tempo', 'status', 'tanggal_bayar', 'tenant']
    list_filter = ['status', 'program', 'jatuh_tempo', 'tenant']
    search_fields = ['santri__nama_lengkap', 'program__nama_program']
    
    fieldsets = (
        (None, {
            'fields': ('santri', 'program', 'nominal', 'jatuh_tempo')
        }),
        ('Status Pembayaran', {
            'fields': ('status', 'tanggal_bayar', 'catatan')
        }),
    )
    
    search_fields = ['santri__nama_lengkap', 'program__nama_program']

@admin.register(PaymentMethodSetting)
class PaymentMethodSettingAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ['method_type', 'bank_name', 'account_number', 'account_name', 'is_active', 'display_order', 'tenant']
    list_filter = ['method_type', 'is_active', 'tenant']
    search_fields = ['bank_name', 'account_number', 'account_name']
    
    fieldsets = (
        (None, {
            'fields': ('method_type', 'is_active', 'display_order')
        }),
        ('Bank Transfer', {
            'fields': ('bank_name', 'account_number', 'account_name'),
            'description': 'Isi jika metode pembayaran adalah Transfer Bank'
        }),
        ('QRIS', {
            'fields': ('qris_image',),
            'description': 'Upload gambar QRIS jika metode pembayaran adalah QRIS'
        }),
    )


@admin.register(PembayaranSPP)
class PembayaranSPPAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ['tagihan', 'jumlah_display', 'payment_method', 'tanggal_transfer', 'status', 'verified_by', 'tenant']
    list_filter = ['status', 'tanggal_transfer', 'tenant']
    search_fields = ['tagihan__santri__nama_lengkap', 'tagihan__santri__nis']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informasi Pembayaran', {
            'fields': ('tagihan', 'payment_method', 'jumlah_bayar', 'tanggal_transfer', 'bukti_transfer', 'catatan_pembayar')
        }),
        ('Verifikasi Admin', {
            'fields': ('status', 'verified_by', 'verified_at', 'catatan_admin')
        }),
    )
    
    readonly_fields = ['verified_at']
    
    def jumlah_display(self, obj):
        return f"Rp {obj.jumlah_bayar:,.0f}"
    jumlah_display.short_description = 'Jumlah'
    
    actions = ['verify_payment', 'reject_payment']
    
    def verify_payment(self, request, queryset):
        from django.utils import timezone
        count = 0
        for pembayaran in queryset.filter(status='PENDING'):
            pembayaran.status = 'VERIFIED'
            pembayaran.verified_by = request.user
            pembayaran.verified_at = timezone.now()
            pembayaran.save()
            count += 1
        self.message_user(request, f"{count} pembayaran berhasil diverifikasi.")
    verify_payment.short_description = "✅ Verifikasi pembayaran terpilih"
    
    def reject_payment(self, request, queryset):
        from django.utils import timezone
        count = 0
        for pembayaran in queryset.filter(status='PENDING'):
            pembayaran.status = 'REJECTED'
            pembayaran.verified_by = request.user
            pembayaran.verified_at = timezone.now()
            pembayaran.save()
            count += 1
        self.message_user(request, f"{count} pembayaran ditolak.")
    reject_payment.short_description = "❌ Tolak pembayaran terpilih"
