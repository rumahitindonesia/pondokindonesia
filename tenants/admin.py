from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Tenant
from core.models import TenantSubscription, TenantGalleryImage
from core.services.landing_service import LandingService
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

class TenantSubscriptionInline(TabularInline):
    model = TenantSubscription
    extra = 1
    can_delete = False

class TenantGalleryImageInline(TabularInline):
    model = TenantGalleryImage
    extra = 3
    max_num = 3

@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = ('name', 'subdomain', 'is_active', 'created_at')
    search_fields = ('name', 'subdomain')
    inlines = [TenantSubscriptionInline, TenantGalleryImageInline]
    actions = ['generate_ai_landing_content', 'discover_ai_gallery_images']

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

    @admin.action(description=_("Discover & Auto-Populate Gallery via AI"))
    def discover_ai_gallery_images(self, request, queryset):
        from core.models import TenantGalleryImage
        import requests
        from django.core.files.base import ContentFile
        import logging
        logger = logging.getLogger(__name__)

        success_count = 0
        for tenant in queryset:
            # Only populate if gallery is empty or less than 3
            existing_count = tenant.gallery_images.count()
            if existing_count >= 3:
                continue
            
            image_urls = LandingService.suggest_gallery_images(tenant)
            added_this_time = 0
            for i, url in enumerate(image_urls):
                if existing_count + added_this_time >= 3:
                    break
                
                try:
                    res = requests.get(url, timeout=10)
                    if res.status_code == 200:
                        filename = f"ai_suggest_{tenant.id}_{existing_count+added_this_time+1}.jpg"
                        TenantGalleryImage.objects.create(
                            tenant=tenant,
                            image=ContentFile(res.content, name=filename),
                            order=existing_count + added_this_time + 1,
                            caption=f"AI Suggested Image for {tenant.name}"
                        )
                        added_this_time += 1
                except Exception as e:
                    logger.error(f"Failed to download AI image for {tenant.name}: {e}")
            
            if added_this_time > 0:
                success_count += 1
            
        self.message_user(
            request, 
            _("Gallery images discovered and added for %d tenants.") % success_count,
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
