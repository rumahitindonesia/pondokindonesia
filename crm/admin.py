from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportMixin
from django.utils import timezone
from django.contrib import messages
from .models import Program, Santri, Donatur, Tagihan, TransaksiDonasi, TagihanSPP, PaymentMethodSetting, PembayaranSPP
from core.services.ipaymu import IPaymuService
from core.services.subscription import SubscriptionService
from core.admin import BaseTenantAdmin
from .resources import SantriResource, DonaturResource, ProgramResource, TagihanResource, TransaksiDonasiResource, TagihanSPPResource

from core.services.starsender import StarSenderService

@admin.register(Program)
class ProgramAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [ProgramResource]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
        self.import_template_name = "admin/import_export/import.html"
        self.export_template_name = "admin/import_export/export.html"
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

@admin.register(Santri)
class SantriAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [SantriResource]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
        self.import_template_name = "admin/import_export/import.html"
        self.export_template_name = "admin/import_export/export.html"
    resource_classes = [SantriResource]
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

@admin.register(Tagihan)
class TagihanAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [TagihanResource]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
        self.import_template_name = "admin/import_export/import.html"
        self.export_template_name = "admin/import_export/export.html"
    resource_classes = [TagihanResource]
    list_display = ('program', 'santri', 'nominal', 'bulan', 'status', 'tgl_buat')
    list_filter = ('program', 'status', 'tenant')
    search_fields = ('santri__nama_lengkap', 'program__nama_program')
    actions = ['send_invoice_whatsapp', 'generate_ipaymu_link']
    list_editable = ['status']

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_resource_kwargs(request, *args, **kwargs)
        kwargs['request'] = request
        return kwargs

    @admin.action(description='Send Invoice via WhatsApp (AI)')
    def send_invoice_whatsapp(self, request, queryset):
        if queryset.exists():
            tenant = queryset.first().tenant
            if not SubscriptionService.check_feature_access(tenant, 'can_use_ai'):
                # Handle gracefully or fallback to standard message
                pass
            if not SubscriptionService.check_feature_access(tenant, 'can_use_whatsapp'):
                self.message_user(request, "Fitur WhatsApp tidak tersedia di paket Anda.", messages.ERROR)
                return

        from core.services.ai_crm_assistant import AICRMAssistant
        count = 0
        for invoice in queryset:
            if not invoice.santri.no_hp_wali:
                continue
            
            # Generate Dynamic Message
            msg = AICRMAssistant.generate_invoice_message(invoice)
            
            if msg:
                StarSenderService.send_message(
                    to=invoice.santri.no_hp_wali, 
                    body=msg, 
                    tenant=invoice.santri.tenant
                )
                count += 1
        
        self.message_user(request, f"{count} invoices sent via WhatsApp.")
    
    @admin.action(description="Buat Link Pembayaran iPaymu")
    def generate_ipaymu_link(self, request, queryset):
        # Check permission for first item (assume same for all in queryset tenant-wise)
        if queryset.exists():
            tenant = queryset.first().tenant
            if not SubscriptionService.check_feature_access(tenant, 'can_use_ipaymu'):
                self.message_user(request, "Fitur iPaymu tidak tersedia di paket Anda. Silakan upgrade.", messages.ERROR)
                return

        for obj in queryset:
            if obj.status == Tagihan.Status.LUNAS:
                self.message_user(request, f"Tagihan untuk {obj.santri.nama_lengkap} sudah lunas, tidak perlu link pembayaran.", messages.WARNING)
                continue
            
            service = IPaymuService(tenant=obj.tenant)
            res, error = service.create_payment(
                amount=obj.nominal,
                reference_id=f"INV-{obj.id}",
                name=obj.santri.nama_lengkap,
                email="ponpes@example.com", # Fallback email
                phone=obj.santri.no_hp_wali,
                description=f"Pembayaran {obj.program.nama_program} - {obj.bulan}"
            )
            
            if res:
                obj.external_id = res['session_id']
                obj.payment_url = res['url']
                obj.save()
                self.message_user(request, f"Link iPaymu berhasil dibuat untuk {obj.santri.nama_lengkap}", messages.SUCCESS)
            else:
                self.message_user(request, f"Gagal untuk {obj.santri.nama_lengkap}: {error}", messages.ERROR)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('santri', 'program')

@admin.register(TransaksiDonasi)
class TransaksiDonasiAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [TransaksiDonasiResource]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
        self.import_template_name = "admin/import_export/import.html"
        self.export_template_name = "admin/import_export/export.html"
    resource_classes = [TransaksiDonasiResource]
    list_display = ('program', 'donatur', 'nominal', 'tgl_donasi')
    list_filter = ('program', 'tenant')
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
    
    list_display = ['santri', 'bulan_display', 'jumlah_display', 'jatuh_tempo', 'status', 'tanggal_bayar', 'tenant']
    list_filter = ['status', 'bulan', 'jatuh_tempo', 'tenant']
    search_fields = ['santri__nama_lengkap', 'santri__nis']
    date_hierarchy = 'bulan'
    
    fieldsets = (
        (None, {
            'fields': ('santri', 'bulan', 'jumlah', 'jatuh_tempo')
        }),
        ('Status Pembayaran', {
            'fields': ('status', 'tanggal_bayar', 'catatan')
        }),
    )
    
    def bulan_display(self, obj):
        return obj.bulan.strftime('%B %Y')
    bulan_display.short_description = 'Bulan'
    
    def jumlah_display(self, obj):
        return f"Rp {obj.jumlah:,.0f}"
    jumlah_display.short_description = 'Jumlah'

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
