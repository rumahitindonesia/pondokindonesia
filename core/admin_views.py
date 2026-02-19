from django.shortcuts import render
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from crm.services.gsheet_sync import GSheetSyncService
from core.models import APISetting
from tenants.models import Tenant

class MockAppConfig:
    def __init__(self, verbose_name):
        self.verbose_name = verbose_name

class MockOpts:
    def __init__(self, app_label, model_name, verbose_name):
        self.app_label = app_label
        self.model_name = model_name
        self.verbose_name = verbose_name
        self.verbose_name_plural = verbose_name + "s"
        self.object_name = model_name
        self.app_config = MockAppConfig("Core") # Or whatever app name you want to display

@staff_member_required
def gsheet_sync_view(request):
    if request.method == "POST":
        spreadsheet_id = request.POST.get("spreadsheet_id")
        model_type = request.POST.get("model_type")
        sheet_name = request.POST.get("sheet_name")
        
        if not spreadsheet_id:
            messages.error(request, "Spreadsheet ID wajib diisi.")
        else:
            tenant = getattr(request, 'tenant', None)
            
            if model_type == "lead":
                count, error = GSheetSyncService.sync_leads(spreadsheet_id, sheet_name, tenant)
            elif model_type == "donatur":
                count, error = GSheetSyncService.sync_donaturs(spreadsheet_id, sheet_name, tenant)
            elif model_type == "santri":
                count, error = GSheetSyncService.sync_santri(spreadsheet_id, sheet_name, tenant)
            elif model_type == "transaksi":
                count, error = GSheetSyncService.sync_transactions(spreadsheet_id, sheet_name, tenant)
            else:
                count, error = 0, "Model tidak valid."

            if error:
                messages.error(request, f"Gagal Sinkronisasi: {error}")
            else:
                messages.success(request, f"Berhasil! {count} data {model_type} telah ditarik.")
                
        return HttpResponseRedirect(reverse("core:gsheet_sync"))

    context = {
        **admin.site.each_context(request),
        "title": "Tarik Data Google Spreadsheet",
        "opts": MockOpts("core", "lead", "GSheet Sync"),
        "available_models": [
            {"id": "lead", "name": "Leads / Pendaftar"},
            {"id": "santri", "name": "Data Santri"},
            {"id": "donatur", "name": "Data Donatur"},
            {"id": "transaksi", "name": "Transaksi Donasi"},
        ],
        "mapping_info": {
            "lead": "Nama, Phone, Kota, Sekolah, Catatan",
            "santri": "NIS, Nama Lengkap, Nama Panggilan, Nama Wali, No HP Wali, Alamat",
            "donatur": "Nama, Phone, Alamat, Kategori",
            "transaksi": "Phone Donatur, Nama Program, Nominal, Keterangan"
        }
    }
    return render(request, "admin/gsheet_sync.html", context)
