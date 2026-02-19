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

from .forms import GSheetSyncForm

@staff_member_required
def gsheet_sync_view(request):
    mapping_info = {
        "lead": "Nama, Phone, Kota, Sekolah, Catatan",
        "santri": "NIS, Nama Lengkap, Nama Panggilan, Nama Wali, No HP Wali, Alamat",
        "donatur": "Nama, Phone, Alamat, Kategori",
        "transaksi": "Tanggal, Phone Donatur, Nama Program, Nominal, Keterangan"
    }

    if request.method == "POST":
        form = GSheetSyncForm(request.POST)
        if form.is_valid():
            spreadsheet_id = form.cleaned_data['spreadsheet_id']
            model_type = form.cleaned_data['model_type']
            sheet_name = form.cleaned_data['sheet_name']
            
            tenant = getattr(request, 'tenant', None) # As per original code
            if not tenant and hasattr(request.user, 'tenant'):
                 tenant = request.user.tenant

            count = 0
            error = None

            try:
                if model_type == "lead":
                    count, error = GSheetSyncService.sync_leads(spreadsheet_id, sheet_name, tenant)
                elif model_type == "donatur":
                    count, error = GSheetSyncService.sync_donaturs(spreadsheet_id, sheet_name, tenant)
                elif model_type == "santri":
                    count, error = GSheetSyncService.sync_santri(spreadsheet_id, sheet_name, tenant)
                elif model_type == "transaksi":
                    count, error = GSheetSyncService.sync_transactions(spreadsheet_id, sheet_name, tenant)
                else:
                    error = "Model tidak valid."

                if error:
                    messages.error(request, f"Gagal Sinkronisasi: {error}")
                else:
                    messages.success(request, f"Berhasil! {count} data {model_type} telah ditarik.")
                    return HttpResponseRedirect(reverse("core:gsheet_sync"))
            
            except Exception as e:
                messages.error(request, f"Terjadi kesalahan: {e}")
    else:
        form = GSheetSyncForm()

    context = {
        **admin.site.each_context(request),
        "title": "Tarik Data Google Spreadsheet",
        "opts": MockOpts("core", "lead", "GSheet Sync"),
        "form": form,
        "mapping_info": mapping_info
    }
    return render(request, "admin/gsheet_sync.html", context)
