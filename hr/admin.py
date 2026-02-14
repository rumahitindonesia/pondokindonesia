from django.contrib import admin
from unfold.admin import ModelAdmin
from core.admin import BaseTenantAdmin
from .models import Jabatan, Pengurus

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
