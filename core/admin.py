from django.contrib import admin, messages
from django.db import models
from unfold.admin import ModelAdmin
from .models import get_current_tenant, APISetting

class BaseTenantAdmin(ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        tenant = getattr(request, 'tenant', None)
        
        # Fallback to User's Tenant (crucial for admin panel access)
        if not request.user.is_superuser and hasattr(request.user, 'tenant'):
            tenant = request.user.tenant
            
        if tenant:
            return qs.filter(tenant=tenant)
        return qs

    def save_model(self, request, obj, form, change):
        tenant = getattr(request, 'tenant', None)
        # Fallback to User's Tenant
        if not tenant and not request.user.is_superuser and hasattr(request.user, 'tenant'):
            tenant = request.user.tenant

        if tenant and hasattr(obj, 'tenant'):
            obj.tenant = tenant
            
        super().save_model(request, obj, form, change)

    def get_exclude(self, request, obj=None):
        exclude = super().get_exclude(request, obj) or []
        # Hide 'tenant' field for non-superusers
        if not request.user.is_superuser:
            return list(exclude) + ['tenant']
        return exclude

@admin.register(APISetting)
class APISettingAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ('key_name', 'category', 'scope', 'is_active')
    list_filter = ('category', 'is_active', 'tenant')
    search_fields = ('key_name', 'description')

    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

from .models import WhatsAppMessage

@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ('sender', 'message', 'device', 'scope', 'created_at')
    list_filter = ('created_at', 'tenant')
    search_fields = ('sender', 'message', 'device')
    readonly_fields = ('created_at', 'raw_data')

    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

from .models import WhatsAppAutoReply

@admin.register(WhatsAppAutoReply)
class WhatsAppAutoReplyAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ('keyword', 'response', 'scope', 'is_active', 'created_at')
    list_filter = ('is_active', 'tenant')
    search_fields = ('keyword', 'response')
    
    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

from .models import AIKnowledgeBase

@admin.register(AIKnowledgeBase)
class AIKnowledgeBaseAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ('topic', 'scope', 'is_active', 'updated_at')
    list_filter = ('is_active', 'tenant')
    search_fields = ('topic', 'content')
    
    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

from .models import Lead, WhatsAppForm

@admin.register(Lead)
class LeadAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ('name', 'type', 'phone_number', 'interest_badge', 'has_draft', 'status', 'scope', 'created_at')
    list_filter = ('type', 'status', 'tenant', 'cs')
    search_fields = ('name', 'phone_number', 'notes')
    readonly_fields = ('created_at', 'chat_history', 'ai_insights', 'last_afu_at', 'afu_count')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'role') and request.user.role:
            if request.user.role.slug == 'cs':
                # CS only see their leads
                return qs.filter(cs=request.user)
        return qs


    def has_draft(self, obj):
        return bool(obj.last_draft)
    has_draft.boolean = True
    has_draft.short_description = "Draft Ready?"

    def interest_badge(self, obj):
        try:
            if not obj.ai_analysis:
                return "-"
            
            level = obj.ai_analysis.get('interest_level', 'Unknown')
            color = "gray"
            if "Hot" in level: color = "red"
            elif "Warm" in level: color = "orange"
            elif "Cold" in level: color = "blue"
            
            from django.utils.html import mark_safe, escape
            safe_level = escape(level)
            
            return mark_safe(f'<span style="background: {color}; color: white; padding: 4px 8px; border-radius: 4px;">{safe_level}</span>')
        except: 
            return "Err"
    interest_badge.short_description = "Minat"

    def ai_insights(self, obj):
        if not obj.ai_analysis:
            return "No analysis yet. Select this lead and click 'Analyze Selected Leads'."
        
        data = obj.ai_analysis
        level = data.get('interest_level', 'Unknown')
        color = "gray"
        if "Hot" in level: color = "red"
        elif "Warm" in level: color = "orange"
        elif "Cold" in level: color = "blue"
        
        html = f"""
        <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
            <div style="font-size: 1.2em; margin-bottom: 10px;">
                Interest: <span style="background: {color}; color: white; padding: 4px 8px; border-radius: 4px;">{level}</span>
            </div>
            <p><strong>Summary:</strong><br>{data.get('summary', '-')}</p>
            <p><strong>Coach's Advice:</strong><br>{data.get('recommendation', '-')}</p>
        </div>
        """
        from django.utils.html import format_html
        return format_html(html)
    ai_insights.short_description = "AI Sales Coach"

    actions = [
        'analyze_leads', 'draft_followup', 'send_draft', 
        'mark_interview', 'mark_accepted',
        'convert_to_santri', 'convert_to_donatur'
    ]

    def get_actions(self, request):
        actions = super().get_actions(request)
        role_slug = request.user.role.slug if hasattr(request.user, 'role') and request.user.role else ""
        
        # Admin-PSB only sees interview/accept conversion
        if role_slug == 'admin-psb':
            allowed = ['mark_accepted', 'convert_to_santri', 'convert_to_donatur', 'analyze_leads']
            return {k: v for k, v in actions.items() if k in allowed}
            
        # CS only sees common lead actions + interview trigger
        if role_slug == 'cs':
            allowed = ['analyze_leads', 'draft_followup', 'send_draft', 'mark_interview']
            return {k: v for k, v in actions.items() if k in allowed}
            
        return actions

    @admin.action(description='Set : Lanjutkan ke Interview (Input Biaya)')
    def mark_interview(self, request, queryset):
        from core.services.starsender import StarSenderService
        from users.models import User
        count = 0
        for lead in queryset:
            lead.status = Lead.Status.INTERVIEW
            lead.save()
            count += 1
            
            # 1. Notify Lead
            StarSenderService.send_message(
                to=lead.phone_number,
                body=f"Halo {lead.name}, pembayaran pendaftaran Anda sudah diterima. Kami sedang menjadwalkan interview. Mohon tunggu kabar selanjutnya.",
                tenant=lead.tenant
            )
            
            # 2. Notify Admin-PSB
            admin_psb = User.objects.filter(tenant=lead.tenant, role__slug='admin-psb', is_active=True).first()
            if admin_psb and admin_psb.phone_number:
                StarSenderService.send_message(
                    to=admin_psb.phone_number,
                    body=f"Notifikasi PSB: Lead {lead.name} ({lead.phone_number}) siap untuk di-interview. Silakan update jadwal di sistem.",
                    tenant=lead.tenant
                )
        self.message_user(request, f"{count} leads updated to Interview status and notifications sent.")

    @admin.action(description='Set : Tandai Diterima (Post-Interview)')
    def mark_accepted(self, request, queryset):
        from core.services.starsender import StarSenderService
        count = 0
        for lead in queryset:
            lead.status = Lead.Status.ACCEPTED
            lead.save()
            count += 1
            
            # 1. Notify Lead
            StarSenderService.send_message(
                to=lead.phone_number,
                body=f"Selamat {lead.name}! Anda dinyatakan DITERIMA di Pondok Indonesia. CS kami ({lead.cs.username if lead.cs else 'Pondok'}) akan segera menghubungi Anda untuk proses selanjutnya.",
                tenant=lead.tenant
            )
            
            # 2. Notify CS
            if lead.cs and lead.cs.phone_number:
                StarSenderService.send_message(
                    to=lead.cs.phone_number,
                    body=f"Info Pendaftaran: Lead {lead.name} ({lead.phone_number}) sudah DITERIMA. Silakan follow-up kembali untuk proses pembayaran.",
                    tenant=lead.tenant
                )
        self.message_user(request, f"{count} leads marked as Accepted and notifications sent.")

    def ai_insights(self, obj):
        try:
            if not obj.ai_analysis:
                return "No analysis yet. Select this lead and click 'Analyze Selected Leads'."
            
            data = obj.ai_analysis
            level = data.get('interest_level', 'Unknown')
            color = "gray"
            if "Hot" in level: color = "red"
            elif "Warm" in level: color = "orange"
            elif "Cold" in level: color = "blue"
            
            from django.utils.html import mark_safe, escape
            
            summary = escape(data.get('summary', '-'))
            recommendation = escape(data.get('recommendation', '-'))
            safe_level = escape(level)
            
            # Check for missing knowledge
            missing_info_html = ""
            missing_knowledge = data.get('missing_knowlege', '') or data.get('missing_knowledge', '')
            if missing_knowledge and len(missing_knowledge) > 5:
                 missing_info_html = f"""
                <div style="margin-top: 10px; padding: 10px; background: #fff3cd; border: 1px solid #ffeeba; border-radius: 4px; color: #856404;">
                    <strong>⚠️ Knowledge Gap Detected:</strong><br>
                    {escape(missing_knowledge)}
                </div>
                """

            html = f"""
            <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                <div style="font-size: 1.2em; margin-bottom: 10px;">
                    Interest: <span style="background: {color}; color: white; padding: 4px 8px; border-radius: 4px;">{safe_level}</span>
                </div>
                <p><strong>Summary:</strong><br>{summary}</p>
                <p><strong>Coach's Advice:</strong><br>{recommendation}</p>
                {missing_info_html}
            </div>
            """
            return mark_safe(html)
        except Exception as e:
            return f"Error loading insights: {e}"
    ai_insights.short_description = "AI Sales Coach"

    @admin.action(description='1. Analyze Selected Leads (AI Coach)')
    def analyze_leads(self, request, queryset):
        from core.services.subscription import SubscriptionService
        if queryset.exists():
            tenant = queryset.first().tenant
            if not SubscriptionService.check_feature_access(tenant, 'can_use_ai'):
                self.message_user(request, "Fitur AI Analysis tidak tersedia di paket Anda. Silakan upgrade.", messages.ERROR)
                return

        from core.services.ai_lead_assistant import AILeadAssistant
        count = 0
        for lead in queryset:
            AILeadAssistant.analyze_lead(lead)
            count += 1
        self.message_user(request, f"{count} leads analyzed successfully.")

    @admin.action(description='2. Draft Follow-up (AI Writer)')
    def draft_followup(self, request, queryset):
        from core.services.subscription import SubscriptionService
        if queryset.exists():
            tenant = queryset.first().tenant
            if not SubscriptionService.check_feature_access(tenant, 'can_use_ai'):
                self.message_user(request, "Fitur AI Draft tidak tersedia di paket Anda. Silakan upgrade.", messages.ERROR)
                return

        from core.services.ai_lead_assistant import AILeadAssistant
        from core.models import Lead
        import traceback
        count = 0
        errors = []
        for lead in queryset:
            try:
                AILeadAssistant.generate_followup(lead, user=request.user)
                # Auto-update status
                if lead.status == Lead.Status.NEW:
                    lead.status = Lead.Status.FOLLOW_UP
                    lead.save(update_fields=['status'])
                count += 1
            except Exception as e:
                traceback.print_exc()
                errors.append(f"{lead.name}: {str(e)}")
        
        if errors:
            self.message_user(request, f"{count} drafts generated. Errors: {'; '.join(errors)}", level='error')
        else:
            self.message_user(request, f"{count} drafts generated. Status updated to 'Sedang Diproses'.")

    @admin.action(description='3. Send Last Draft (StarSender)')
    def send_draft(self, request, queryset):
        from core.services.subscription import SubscriptionService
        if queryset.exists():
            tenant = queryset.first().tenant
            if not SubscriptionService.check_feature_access(tenant, 'can_use_whatsapp'):
                self.message_user(request, "Fitur WhatsApp tidak tersedia di paket Anda. Silakan upgrade.", messages.ERROR)
                return

        from core.services.starsender import StarSenderService
        from core.models import Lead
        count = 0
        for lead in queryset:
            if lead.last_draft:
                StarSenderService.send_message(to=lead.phone_number, body=lead.last_draft, tenant=lead.tenant)
                # Auto-update status
                if lead.status == Lead.Status.NEW:
                    lead.status = Lead.Status.FOLLOW_UP
                    lead.save(update_fields=['status'])
                count += 1
        self.message_user(request, f"{count} messages sent. Status updated to 'Sedang Diproses'.")

    @admin.action(description='4. Convert to Santri (CRM)')
    def convert_to_santri(self, request, queryset):
        from crm.services import CRMService
        from core.models import Lead
        from django.contrib import messages
        count = 0
        errors = []
        for lead in queryset:
            res_obj, msg = CRMService.convert_lead(lead, Lead.Type.SANTRI)
            if res_obj:
                count += 1
            else:
                errors.append(f"{lead.name}: {msg}")
            
        if errors:
            self.message_user(request, f"{count} santri created. Errors: {'; '.join(errors)}", messages.WARNING)
        else:
            self.message_user(request, f"{count} santri created successfully.")

    @admin.action(description='5. Convert to Donatur (CRM)')
    def convert_to_donatur(self, request, queryset):
        from crm.services import CRMService
        from core.models import Lead
        from django.contrib import messages
        count = 0
        errors = []
        for lead in queryset:
            res_obj, msg = CRMService.convert_lead(lead, Lead.Type.DONATUR)
            if res_obj:
                count += 1
            else:
                errors.append(f"{lead.name}: {msg}")
            
        if errors:
            self.message_user(request, f"{count} donatur created. Errors: {'; '.join(errors)}", messages.WARNING)
        else:
            self.message_user(request, f"{count} donatur created successfully.")

    def chat_history(self, obj):
        try:
            if not obj or not obj.phone_number:
                return "No phone number available."
                
            # Get messages linked to this phone number
            # Debug: Ensure obj.tenant is handled correctly even if None
            tnt = obj.tenant if obj.tenant else None
            
            messages = WhatsAppMessage.objects.filter(
                tenant=tnt,
                sender=obj.phone_number
            ).order_by('-created_at')[:10] # Last 10 messages
            
            if not messages.exists():
                return "No chat history found."
            
            from django.utils.html import mark_safe, escape

            html = "<div style='max-height: 300px; overflow-y: auto; background: #f9f9f9; padding: 10px; border: 1px solid #ddd;'>"
            for msg in messages:
                sender = "User" if msg.sender == obj.phone_number else "System"
                timestamp = msg.created_at.strftime('%d/%m %H:%M')
                safe_msg = escape(msg.message)
                
                html += f"<div style='margin-bottom: 5px;'><strong>{timestamp}</strong>: {safe_msg}</div>"
            html += "</div>"
            
            return mark_safe(html)
        except Exception as e:
            return f"Error loading chat history: {e}"
    
    chat_history.short_description = "Last 10 Messages"

    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

@admin.register(WhatsAppForm)
class WhatsAppFormAdmin(BaseTenantAdmin, ModelAdmin):
    list_display = ('keyword', 'lead_type', 'auto_insert', 'is_staff_only', 'scope', 'is_active')
    list_filter = ('lead_type', 'auto_insert', 'is_staff_only', 'is_active', 'tenant')
    search_fields = ('keyword', 'response_template')
    
    def scope(self, obj):
        return "Global" if not obj.tenant else f"Tenant: {obj.tenant}"
    scope.short_description = 'Scope'

from .models import PricingPlan, TenantSubscription

@admin.register(PricingPlan)
class PricingPlanAdmin(ModelAdmin):
    list_display = ('name', 'price', 'is_popular', 'max_santri', 'max_donatur', 'can_use_ai', 'is_active', 'order')
    list_editable = ('is_popular', 'is_active', 'order', 'can_use_ai')
    search_fields = ('name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'price', 'period', 'description', 'features', 'cta_text', 'cta_url', 'is_popular', 'is_active', 'order')
        }),
        ('Technical Limits', {
            'fields': ('max_santri', 'max_donatur', 'can_use_ai', 'can_use_ipaymu', 'can_use_whatsapp')
        }),
    )

@admin.register(TenantSubscription)
class TenantSubscriptionAdmin(ModelAdmin):
    list_display = ('tenant', 'plan', 'expiry_date', 'is_active', 'is_valid_status')
    list_filter = ('plan', 'is_active')
    search_fields = ('tenant__name', 'tenant__subdomain')
    
    def is_valid_status(self, obj):
        return obj.is_valid()
    is_valid_status.boolean = True
    is_valid_status.short_description = 'Valid & Active?'
