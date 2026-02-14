from django.contrib import admin
from unfold.admin import ModelAdmin
from core.admin import BaseTenantAdmin
from .models import Jabatan, Pengurus, Tugas, LokasiKantor, Absensi

@admin.register(LokasiKantor)
class LokasiKantorAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ['nama', 'radius_meter', 'latitude', 'longitude', 'tenant']
    search_fields = ['nama']
    list_filter = ['tenant']

@admin.register(Absensi)
class AbsensiAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ['pengurus', 'tanggal', 'waktu_masuk', 'waktu_keluar', 'status', 'tenant']
    list_filter = ['status', 'tanggal', 'tenant', 'pengurus__jabatan']
    search_fields = ['pengurus__nama']
    autocomplete_fields = ['pengurus']
    date_hierarchy = 'tanggal'
    readonly_fields = ['waktu_masuk', 'foto_masuk', 'lokasi_masuk', 'waktu_keluar', 'foto_keluar', 'lokasi_keluar']

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
