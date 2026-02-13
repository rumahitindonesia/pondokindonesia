from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportMixin
from .models import Program, Santri, Donatur, Tagihan, TransaksiDonasi
from core.admin import BaseTenantAdmin
from .resources import SantriResource, DonaturResource, ProgramResource, TagihanResource, TransaksiDonasiResource

from core.services.starsender import StarSenderService

@admin.register(Program)
class ProgramAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [ProgramResource]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
    resource_classes = [ProgramResource]
    list_display = ('nama_program', 'jenis', 'nominal_standar', 'scope', 'is_active')
    list_filter = ('jenis', 'is_active', 'tenant')
    search_fields = ('nama_program',)

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_resource_kwargs(request, *args, **kwargs)
        kwargs['request'] = request
        kwargs.pop('form', None)
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
    resource_classes = [SantriResource]
    list_display = ('nis', 'nama_lengkap', 'status', 'nama_wali', 'scope')
    list_filter = ('status', 'tenant')
    search_fields = ('nis', 'nama_lengkap', 'nama_wali', 'no_hp_wali')

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_resource_kwargs(request, *args, **kwargs)
        kwargs['request'] = request
        kwargs.pop('form', None)
        return kwargs

    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

@admin.register(Donatur)
class DonaturAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [DonaturResource]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
    resource_classes = [DonaturResource]
    list_display = ('nama_donatur', 'kategori', 'no_hp', 'scope', 'tgl_bergabung')
    list_filter = ('kategori', 'tenant')
    search_fields = ('nama_donatur', 'no_hp')
    actions = ['send_solicitation_whatsapp']

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_resource_kwargs(request, *args, **kwargs)
        kwargs['request'] = request
        kwargs.pop('form', None)
        return kwargs

    @admin.action(description='Send Solicitation (AI Generator)')
    def send_solicitation_whatsapp(self, request, queryset):
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

@admin.register(Tagihan)
class TagihanAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [TagihanResource]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
    resource_classes = [TagihanResource]
    list_display = ('program', 'santri', 'nominal', 'bulan', 'status', 'tgl_buat')
    list_filter = ('program', 'status', 'tenant')
    search_fields = ('santri__nama_lengkap', 'program__nama_program')
    actions = ['send_invoice_whatsapp']

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_resource_kwargs(request, *args, **kwargs)
        kwargs['request'] = request
        kwargs.pop('form', None)
        return kwargs

    @admin.action(description='Send Invoice via WhatsApp (AI)')
    def send_invoice_whatsapp(self, request, queryset):
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
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('santri', 'program')

@admin.register(TransaksiDonasi)
class TransaksiDonasiAdmin(ImportExportMixin, BaseTenantAdmin, ModelAdmin):
    resource_classes = [TransaksiDonasiResource]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_list_template = "admin/import_export/change_list_custom.html"
    resource_classes = [TransaksiDonasiResource]
    list_display = ('program', 'donatur', 'nominal', 'tgl_donasi')
    list_filter = ('program', 'tenant')
    search_fields = ('donatur__nama_donatur', 'program__nama_program')
    actions = ['send_receipt_whatsapp']

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_import_resource_kwargs(request, *args, **kwargs)
        kwargs['request'] = request
        kwargs.pop('form', None)
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
