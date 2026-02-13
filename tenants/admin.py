from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Tenant
from core.models import TenantSubscription

class TenantSubscriptionInline(TabularInline):
    model = TenantSubscription
    extra = 1
    can_delete = False

@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = ('name', 'subdomain', 'is_active', 'created_at')
    search_fields = ('name', 'subdomain')
    inlines = [TenantSubscriptionInline]
