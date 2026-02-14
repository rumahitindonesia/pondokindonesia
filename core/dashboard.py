from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from tenants.models import Tenant
from core.models import Lead, TenantSubscription, WhatsAppMessage
from crm.models import Santri, Donatur, Tagihan, TransaksiDonasi

def dashboard_callback(request, context):
    """
    Callback function to inject data into Unfold Admin Dashboard.
    """
    user = request.user
    tenant = getattr(request, 'tenant', None)
    
    # Fallback to User's Tenant if accessed via non-subdomain (central)
    if not tenant and not user.is_superuser and hasattr(user, 'tenant'):
        tenant = user.tenant

    if user.is_superuser and not tenant:
        # --- SUPER ADMIN DASHBOARD ---
        total_tenants = Tenant.objects.count()
        total_leads = Lead.objects.count()
        active_subscriptions = TenantSubscription.objects.filter(is_active=True).count()
        
        # WhatsApp Stats (Total messages last 24h)
        last_24h = timezone.now() - timedelta(hours=24)
        wa_messages_count = WhatsAppMessage.objects.filter(created_at__gte=last_24h).count()

        context.update({
            "kpi_cards": [
                {
                    "title": "Total Mitra (Pondok)",
                    "metric": total_tenants,
                    "icon": "business",
                    "color": "blue",
                    "footer": "Total pondok terdaftar",
                },
                {
                    "title": "Total Leads (Pendaftar)",
                    "metric": total_leads,
                    "icon": "group_add",
                    "color": "primary",
                    "footer": "Calon santri & donatur",
                },
                {
                    "title": "Subscription Aktif",
                    "metric": active_subscriptions,
                    "icon": "verified_user",
                    "color": "green",
                    "footer": "Paket berbayar aktif",
                },
                {
                    "title": "Pesan WA (24 Jam)",
                    "metric": wa_messages_count,
                    "icon": "chat",
                    "color": "orange",
                    "footer": "Lalu lintas pesan",
                },
            ],
        })
    else:
        # --- TENANT DASHBOARD ---
        # Scoped to current tenant
        total_santri = Santri.objects.filter(tenant=tenant, status='AKTIF').count()
        total_donatur = Donatur.objects.filter(tenant=tenant).count()
        
        # Financials (This Month)
        now = timezone.now()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total_donasi_month = TransaksiDonasi.objects.filter(
            tenant=tenant, 
            tgl_donasi__gte=first_day_of_month
        ).aggregate(total=Sum('nominal'))['total'] or 0
        
        # Unpaid Bills
        unpaid_bills_count = Tagihan.objects.filter(
            tenant=tenant, 
            status='BELUM'
        ).count()

        # Lead Status Distribution
        leads_new = Lead.objects.filter(tenant=tenant, status='NEW').count()
        
        # --- PRIORITY LISTS (New) ---
        from django.db.models import Case, When, Value, IntegerField
        
        # 1. Hot Leads (Top 5)
        priority_leads = Lead.objects.filter(tenant=tenant).exclude(status__in=['CLOSED', 'REJECTED']).annotate(
            interest_score=Case(
                When(ai_analysis__interest_level='Hot', then=Value(3)),
                When(ai_analysis__interest_level='Warm', then=Value(2)),
                When(ai_analysis__interest_level='Cold', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-interest_score', '-created_at')[:5]

        # 2. Overdue SPP (Top 5)
        overdue_tagihan = Tagihan.objects.filter(
            tenant=tenant, 
            status='BELUM'
        ).order_by('tgl_buat')[:5]

        # 3. Potential Donors (Top 5 - Insidentil or newest)
        potential_donatur = Donatur.objects.filter(tenant=tenant).order_by('-tgl_bergabung')[:5]

        tenant_name = tenant.name if tenant else "Pondok"
        
        context.update({
            "kpi_cards": [
                {
                    "title": "Santri Aktif",
                    "metric": total_santri,
                    "icon": "school",
                    "color": "primary",
                    "footer": f"Total santri di {tenant_name}",
                },
                {
                    "title": "Donasi Bulan Ini",
                    "metric": f"Rp {total_donasi_month:,.0f}",
                    "icon": "volunteer_activism",
                    "color": "green",
                    "footer": "Total pemasukan donasi",
                },
                {
                    "title": "Tagihan Belum Lunas",
                    "metric": unpaid_bills_count,
                    "icon": "payments",
                    "color": "red",
                    "footer": "Perlu segera di-followup",
                },
                {
                    "title": "Pendaftar Baru",
                    "metric": leads_new,
                    "icon": "person_add",
                    "color": "orange",
                    "footer": "Leads status 'Baru'",
                },
            ],
            "priority_leads": priority_leads,
            "overdue_tagihan": overdue_tagihan,
            "potential_donatur": potential_donatur,
        })

    return context
