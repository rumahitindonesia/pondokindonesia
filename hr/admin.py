from django.contrib import admin
from unfold.admin import ModelAdmin
from core.admin import BaseTenantAdmin
from .models import Jabatan, Pengurus, Tugas, LokasiKantor, Absensi

@admin.register(LokasiKantor)
class LokasiKantorAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ['nama', 'radius_meter', 'latitude', 'longitude', 'tenant']
    search_fields = ['nama']
    list_filter = ['tenant']

from django.utils import timezone
import json
import base64
from django.core.files.base import ContentFile
from django.shortcuts import redirect
from django.urls import reverse

@admin.register(Absensi)
class AbsensiAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ['pengurus', 'tanggal', 'waktu_masuk', 'waktu_keluar', 'status', 'tenant']
    list_filter = ['status', 'tanggal', 'tenant', 'pengurus__jabatan']
    search_fields = ['pengurus__nama']
    autocomplete_fields = ['pengurus']
    date_hierarchy = 'tanggal'
    readonly_fields = ['waktu_masuk', 'foto_masuk', 'lokasi_masuk', 'waktu_keluar', 'foto_keluar', 'lokasi_keluar']
    # change_form_template = 'admin/hr/absensi/change_form.html'

    fieldsets = (
        (None, {
            'fields': ('pengurus', 'tanggal', 'status', 'catatan')
        }),
        ('Absen Masuk', {
            'fields': ('waktu_masuk', 'foto_masuk', 'lokasi_masuk')
        }),
        ('Absen Pulang', {
            'fields': ('waktu_keluar', 'foto_keluar', 'lokasi_keluar')
        }),
    )

    def get_office_context(self, request):
        try:
            tenant = getattr(request, 'tenant', None)
            # Fallback to User's Tenant
            if not tenant and not request.user.is_superuser and hasattr(request.user, 'tenant'):
                tenant = request.user.tenant

            if tenant:
                lokasi = LokasiKantor.objects.filter(tenant=tenant).first()
                if lokasi:
                    return json.dumps({
                        'nama': lokasi.nama,
                        'latitude': str(lokasi.latitude),
                        'longitude': str(lokasi.longitude),
                        'radius_meter': lokasi.radius_meter
                    })
        except Exception:
            pass
        
        # Default Fallback (Monas)
        return json.dumps({
            'nama': 'Default (Monas)',
            'latitude': '-6.175110', 
            'longitude': '106.827253',
            'radius_meter': 100
        })

    def add_view(self, request, form_url='', extra_context=None):
        from django.http import HttpResponse
        import traceback
        try:
            # Cek apakah user ini Pengurus dan sudah absen hari ini
            try:
                if hasattr(request.user, 'pengurus_profile'):
                    pengurus = request.user.pengurus_profile
                    today = timezone.localdate()
                    existing = Absensi.objects.filter(pengurus=pengurus, tanggal=today).first()
                    if existing:
                        # Redirect ke Change View (Mode Pulang)
                        url = reverse('admin:hr_absensi_change', args=[existing.pk])
                        return redirect(url)
            except Exception:
                pass # User might not have a Pengurus profile

            extra_context = extra_context or {}
            extra_context['office_json'] = self.get_office_context(request)
            return super().add_view(request, form_url, extra_context=extra_context)
        except Exception as e:
            return HttpResponse(f"CRASH REPORT:\n{e}\n\n{traceback.format_exc()}", status=500, content_type="text/plain")

    # def change_view(self, request, object_id, form_url='', extra_context=None):
    #     extra_context = extra_context or {}
    #     extra_context['office_json'] = self.get_office_context(request)
    #     return super().change_view(request, object_id, form_url, extra_context=extra_context)

    # def save_model(self, request, obj, form, change):
    #     # 1. Set Pengurus (jika buat baru)
    #     if not obj.pk and not obj.pengurus_id and hasattr(request.user, 'pengurus_profile'):
    #         obj.pengurus = request.user.pengurus_profile
        
    #     # 2. Handle Foto Base64
    #     foto_b64 = request.POST.get('foto_base64')
    #     lat = request.POST.get('detected_lat')
    #     lon = request.POST.get('detected_lon')

    #     if foto_b64:
    #         format, imgstr = foto_b64.split(';base64,') 
    #         ext = format.split('/')[-1] 
    #         fname = f"absensi_{obj.pengurus.nama}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    #         data = ContentFile(base64.b64decode(imgstr), name=fname)

    #         if not obj.waktu_masuk:
    #             # Absen Masuk
    #             obj.foto_masuk = data
    #             obj.waktu_masuk = timezone.now()
    #             obj.lokasi_masuk = f"{lat}, {lon}"
    #             obj.status = Absensi.Status.HADIR # Default OK
    #         elif obj.waktu_masuk and not obj.waktu_keluar:
    #             # Absen Pulang
    #             obj.foto_keluar = data
    #             obj.waktu_keluar = timezone.now()
    #             obj.lokasi_keluar = f"{lat}, {lon}"

    #     super().save_model(request, obj, form, change)


@admin.register(Jabatan)
class JabatanAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ['nama', 'atasan', 'tenant']
    search_fields = ['nama']
    list_filter = ['tenant']
    autocomplete_fields = ['atasan']

@admin.register(Pengurus)
class PengurusAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ['nama', 'jabatan', 'user', 'telepon', 'is_active', 'tenant']
    search_fields = ['nama', 'nik', 'telepon']
    list_filter = ['jabatan', 'is_active', 'tenant']
    autocomplete_fields = ['jabatan', 'user']
    
    fieldsets = (
        (None, {
            'fields': ('nama', 'nik', 'jabatan', 'foto')
        }),
        ('Kontak & Alamat', {
            'fields': ('telepon', 'alamat')
        }),
        ('Sistem & Akses', {
            'fields': ('user', 'is_active')
        }),
    )

@admin.register(Tugas)
class TugasAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ['judul', 'pembuat', 'penerima', 'status', 'prioritas', 'jenis', 'tenggat_waktu', 'skor', 'tenant']
    list_filter = ['status', 'prioritas', 'jenis', 'tenant', 'penerima']
    search_fields = ['judul', 'deskripsi', 'penerima__nama', 'pembuat__username']
    autocomplete_fields = ['penerima', 'lead']
    readonly_fields = ['pembuat']
    date_hierarchy = 'tenggat_waktu'
    
    fieldsets = (
        (None, {
            'fields': ('judul', 'deskripsi', 'file', 'pembuat')
        }),
        ('Detail Penugasan', {
            'fields': ('penerima', 'lead', 'jenis', 'prioritas', 'bobot', 'tenggat_waktu')
        }),
        ('Status & Penyelesaian', {
            'fields': ('status', 'url_posting', 'tanggal_selesai', 'waktu_diselesaikan', 'catatan_penyelesaian')
        }),
        ('Penilaian (Manager)', {
            'fields': ('skor', 'review_manager'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.pembuat:
            obj.pembuat = request.user
        super().save_model(request, obj, form, change)

    actions = ['mark_completed', 'delegate_to_staff']

    @admin.action(description="Tandai Selesai (Batch)")
    def mark_completed(self, request, queryset):
        queryset.update(status=Tugas.Status.SELESAI, tanggal_selesai=models.functions.Now())
        self.message_user(request, "Tugas terpilih telah ditandai selesai.")

    @admin.action(description="Delegasikan ke Staf Lain")
    def delegate_to_staff(self, request, queryset):
        # This is a placeholder for a more complex action (maybe an intermediate page)
        # For now, we just update type to PENUGASAN if it was PERMINTAAN
        queryset.filter(jenis=Tugas.Jenis.PERMINTAAN).update(jenis=Tugas.Jenis.PENUGASAN)
        self.message_user(request, "Tugas permintaan telah diubah menjadi penugasan langsung.")
