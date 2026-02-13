from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Tenant
from core.models import TenantSubscription
from core.services.landing_service import LandingService
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

class TenantSubscriptionInline(TabularInline):
    model = TenantSubscription
    extra = 1
    can_delete = False

@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = ('name', 'subdomain', 'is_active', 'created_at')
    search_fields = ('name', 'subdomain')
    inlines = [TenantSubscriptionInline]
    actions = ['generate_ai_landing_content']

    @admin.action(description=_("Generate Landing Content & SEO via AI"))
    def generate_ai_landing_content(self, request, queryset):
        success_count = 0
        for tenant in queryset:
            # 1. Generate Description
            content = LandingService.generate_landing_content(tenant)
            if content:
                tenant.description = content
                
            # 2. Generate SEO Metadata
            seo = LandingService.generate_seo_metadata(tenant)
            if seo:
                tenant.seo_title = seo.get('title', tenant.seo_title)
                tenant.seo_description = seo.get('description', tenant.seo_description)
            
            tenant.save()
            success_count += 1
            
        self.message_user(
            request, 
            _("Successfully generated content for %d tenants.") % success_count,
            messages.SUCCESS
        )

    fieldsets = (
        (None, {
            'fields': ('name', 'subdomain', 'is_active', 'logo')
        }),
        (_('Branding & Profile'), {
            'fields': ('description', 'address', 'phone_number'),
        }),
        (_('SEO Metadata'), {
            'fields': ('seo_title', 'seo_description'),
            'classes': ('collapse',),
        }),
    )
