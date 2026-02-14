from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import models
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm
from .forms import UserChangeForm, UserCreationForm
from .models import User, Role
from core.admin import BaseTenantAdmin

from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from core.services.starsender import StarSenderService

from django.utils.translation import gettext_lazy as _

@admin.register(Role)
class RoleAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ('name', 'slug', 'scope', 'is_system')
    list_filter = ('tenant', 'is_system')
    search_fields = ('name', 'slug')
    filter_horizontal = ('permissions',)

    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

    def get_queryset(self, request):
        tenant = getattr(request, 'tenant', None)
        if tenant:
            return Role.global_objects.all()
        return super().get_queryset(request)

@admin.register(User)
class UserAdmin(BaseTenantAdmin, BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('username', 'email', 'phone_number', 'role', 'tenant', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'phone_number')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        ('SaaS Info', {'fields': ('role', 'tenant')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('SaaS Info', {'fields': ('role', 'tenant', 'phone_number')}),
    )
    actions = ['send_whatsapp_action']
    list_after_template = "admin/users/user/whatsapp_modal.html"

    def get_queryset(self, request):
        tenant = getattr(request, 'tenant', None)
        # Central Admin: Show ALL users (including tenant users)
        if not tenant:
            return User.all_objects.all()
        # Tenant Admin: The default 'objects' (TenantUserManager) 
        # already filters strictly by the current tenant.
        return super().get_queryset(request)

    def get_fieldsets(self, request, obj=None):
        # Handle Add View (obj is None)
        if not obj:
            fieldsets = list(self.add_fieldsets)
            if not request.user.is_superuser:
                # Filter out 'tenant' from any fieldset
                new_fieldsets = []
                for name, opts in fieldsets:
                    fields = list(opts.get('fields', []))
                    if 'tenant' in fields:
                        fields.remove('tenant')
                    new_opts = opts.copy()
                    new_opts['fields'] = tuple(fields)
                    new_fieldsets.append((name, new_opts))
                return tuple(new_fieldsets)
            return self.add_fieldsets

        # Handle Change View (obj exists)
        fieldsets = list(super().get_fieldsets(request, obj))
        if not request.user.is_superuser:
            # Filter out 'tenant'
            new_fieldsets = []
            for name, opts in fieldsets:
                fields = list(opts.get('fields', []))
                if 'tenant' in fields:
                    fields.remove('tenant')
                new_opts = opts.copy()
                new_opts['fields'] = tuple(fields)
                new_fieldsets.append((name, new_opts))
            return tuple(new_fieldsets)
        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        return super().get_form(request, obj, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        return super().add_view(request, form_url, extra_context)

    
    def send_whatsapp_action(self, request, queryset):
        """
        Action to send WhatsApp message to selected users via StarSender.
        Can process directly if message_body is present in POST (from Modal),
        or render intermediate page (fallback).
        """
        # 1. Direct Submission from Modal
        if 'message_body' in request.POST:
            message_body = request.POST.get('message_body')
            # 'apply' might be present too if we added it in JS, but message_body is key
            
            if not message_body:
                self.message_user(request, "Message body cannot be empty.", messages.ERROR)
                return HttpResponseRedirect(request.get_full_path())

            success_count = 0
            fail_count = 0
            tenant = getattr(request, 'tenant', None)

            for user in queryset:
                if not user.phone_number:
                    fail_count += 1
                    continue
                
                # Basic formatting: ensure it starts with 08 or 62
                phone = user.phone_number.strip()
                if phone.startswith('0'):
                    phone = '62' + phone[1:]
                
                is_sent, _ = StarSenderService.send_message(
                    to=phone,
                    body=message_body,
                    tenant=tenant
                )
                
                if is_sent:
                    success_count += 1
                else:
                    fail_count += 1
            
            self.message_user(request, f"Sent: {success_count}, Failed: {fail_count}", messages.SUCCESS)
            return HttpResponseRedirect(request.get_full_path())

        # 2. Intermediate Page (Fallback if JS fails or direct access)
        # If "apply" button is clicked in the intermediate form
        if 'apply' in request.POST:
            # Logic repeated? Better to unify. 
            # But the modal submission uses the SAME logic branch above if we send message_body.
            pass

        return render(request, 'admin/users/user/send_whatsapp.html', context={
            'users': queryset,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        })
    send_whatsapp_action.short_description = "Send WhatsApp Message"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        try:
            if db_field.name == "role":
                tenant = getattr(request, 'tenant', None)
                if tenant:
                    # Filter roles for tenant admins:
                    # 1. Roles belonging to this specific tenant
                    # 2. Global roles (tenant=None) but EXCLUDING critical SaaS Admin roles
                    kwargs["queryset"] = Role.global_objects.filter(
                        models.Q(tenant=tenant) | 
                        models.Q(tenant__isnull=True)
                    ).exclude(slug='saas_admin')
            
            # Also restrict the tenant field if present in the form (unlikely for tenant admins, but safe)
            if db_field.name == "tenant":
                tenant = getattr(request, 'tenant', None)
                if tenant:
                    kwargs["queryset"] = db_field.related_model.objects.filter(id=tenant.id)

            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
