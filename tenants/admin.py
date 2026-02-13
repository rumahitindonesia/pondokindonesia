from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Tenant

@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = ('name', 'subdomain', 'is_active', 'created_at')
    search_fields = ('name', 'subdomain')
