from django.shortcuts import render
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from crm.services.gsheet_sync import GSheetSyncService
from core.models import APISetting
from tenants.models import Tenant

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
            else:
                count, error = 0, "Model tidak valid."

            if error:
                messages.error(request, f"Gagal Sinkronisasi: {error}")
            else:
                messages.success(request, f"Berhasil! {count} data {model_type} telah ditarik.")
                
        return HttpResponseRedirect(reverse("core:gsheet_sync"))

    context = {
        "title": "Tarik Data Google Spreadsheet",
        "opts": {"app_label": "core"}, # For breadcrumbs
        "available_models": [
            {"id": "lead", "name": "Leads / Pendaftar"},
            {"id": "donatur", "name": "Donatur"},
        ],
    }
    return render(request, "admin/gsheet_sync.html", context)
