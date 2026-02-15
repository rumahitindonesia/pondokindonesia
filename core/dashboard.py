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
        
        # Role-based scoping for leads
        is_cs = user.role.slug == 'cs' if user.role else False
        lead_base_qs = Lead.objects.filter(tenant=tenant)
        if is_cs:
            lead_base_qs = lead_base_qs.filter(cs=user)
        
        # Financials (This Month)
        now = timezone.now()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total_donasi_month = TransaksiDonasi.objects.filter(
            tenant=tenant, 
            tgl_donasi__gte=first_day_of_month
        ).aggregate(total=Sum('nominal'))['total'] or 0

        # Non-Donation Earnings (LUNAS bills paid this month)
        # 1. Old Tagihan
        total_tagihan_old = Tagihan.objects.filter(
            tenant=tenant,
            status='LUNAS',
            tgl_bayar__gte=first_day_of_month
        ).aggregate(total=Sum('nominal'))['total'] or 0
        
        # 2. New TagihanSPP
        from crm.models import TagihanSPP
        total_tagihan_spp = TagihanSPP.objects.filter(
            tenant=tenant,
            status='LUNAS',
            tanggal_bayar__gte=first_day_of_month
        ).aggregate(total=Sum('jumlah'))['total'] or 0

        total_non_donasi_month = total_tagihan_old + total_tagihan_spp
        
        # Unpaid Bills
        unpaid_old = Tagihan.objects.filter(
            tenant=tenant, 
            status='BELUM'
        ).count()
        
        unpaid_spp = TagihanSPP.objects.filter(
            tenant=tenant,
            status__in=['BELUM_LUNAS', 'TERLAMBAT']
        ).count()
        
        unpaid_bills_count = unpaid_old + unpaid_spp

        # Lead Status Distribution
        leads_new = lead_base_qs.filter(status='NEW').count()
        
        # --- PRIORITY LISTS (New) ---
        from django.db.models import Case, When, Value, IntegerField
        
        # 1. Hot Leads (Top 5)
        priority_leads = lead_base_qs.exclude(status__in=['CLOSED', 'REJECTED']).annotate(
            interest_score=Case(
                When(ai_analysis__interest_level='Hot', then=Value(3)),
                When(ai_analysis__interest_level='Warm', then=Value(2)),
                When(ai_analysis__interest_level='Cold', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-interest_score', '-created_at')[:5]

        # 2. Overdue SPP (Top 5)
        # Prioritize TagihanSPP over old Tagihan
        overdue_tagihan_spp = TagihanSPP.objects.filter(
            tenant=tenant,
            status='TERLAMBAT'
        ).order_by('jatuh_tempo')[:5]
        
        overdue_tagihan = overdue_tagihan_spp if overdue_tagihan_spp.exists() else Tagihan.objects.filter(
            tenant=tenant, 
            status='BELUM'
        ).order_by('tgl_buat')[:5]

        # 3. Potential Donors (Top 5 - Insidentil or newest)
        potential_donatur = Donatur.objects.filter(tenant=tenant).order_by('-tgl_bergabung')[:5]

        tenant_name = tenant.name if tenant else "Pondok"

        # --- DAILY CHART DATA ---
        import calendar
        from django.db.models.functions import TruncDate, TruncDay
        
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        chart_labels = [str(i) for i in range(1, days_in_month + 1)]
        
        # Initialize daily data maps
        daily_non_donasi_map = {i: 0 for i in range(1, days_in_month + 1)}
        daily_donasi_map = {i: 0 for i in range(1, days_in_month + 1)}
        
        # Fetch data - OLD Tagihan
        non_donasi_query = Tagihan.objects.filter(
            tenant=tenant,
            status='LUNAS',
            tgl_bayar__year=now.year,
            tgl_bayar__month=now.month
        ).annotate(day=TruncDate('tgl_bayar')).values('day').annotate(total=Sum('nominal'))

        # Fetch data - NEW TagihanSPP
        spp_query = TagihanSPP.objects.filter(
            tenant=tenant,
            status='LUNAS',
            tanggal_bayar__year=now.year,
            tanggal_bayar__month=now.month
        ).annotate(day=TruncDay('tanggal_bayar')).values('day').annotate(total=Sum('jumlah'))

        donasi_query = TransaksiDonasi.objects.filter(
            tenant=tenant,
            tgl_donasi__year=now.year,
            tgl_donasi__month=now.month
        ).annotate(day=TruncDate('tgl_donasi')).values('day').annotate(total=Sum('nominal'))

        # Map to days
        for entry in non_donasi_query:
            if entry['day']:
                daily_non_donasi_map[entry['day'].day] += float(entry['total'])
        
        for entry in spp_query:
             if entry['day']:
                daily_non_donasi_map[entry['day'].day] += float(entry['total'])
        
        for entry in donasi_query:
            if entry['day']:
                daily_donasi_map[entry['day'].day] += float(entry['total'])

        chart_non_donasi_data = [daily_non_donasi_map[i] for i in range(1, days_in_month + 1)]
        chart_donasi_data = [daily_donasi_map[i] for i in range(1, days_in_month + 1)]
        
        import json
        context.update({
            "master_kpis": [
                {
                    "title": "Perolehan Non Donasi",
                    "metric": f"Rp {total_non_donasi_month:,.0f}",
                    "icon": "payments",
                    "color": "blue",
                    "footer": "Total SPP/Tagihan Lunas (Bulan Ini)",
                },
                {
                    "title": "Perolehan Donasi",
                    "metric": f"Rp {total_donasi_month:,.0f}",
                    "icon": "volunteer_activism",
                    "color": "green",
                    "footer": "Total Donasi Masuk (Bulan Ini)",
                },
            ],
            "kpi_cards": [
                {
                    "title": "Santri Aktif",
                    "metric": total_santri,
                    "icon": "school",
                    "color": "primary",
                    "footer": f"Total santri di {tenant_name}",
                },
                {
                    "title": "Total Donatur",
                    "metric": total_donatur,
                    "icon": "favorite",
                    "color": "green",
                    "footer": f"Donatur terdaftar di {tenant_name}",
                },
                {
                    "title": "Tagihan Belum Lunas",
                    "metric": unpaid_bills_count,
                    "icon": "priority_high",
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
            "chart_labels": json.dumps(chart_labels),
            "chart_non_donasi_data": json.dumps(chart_non_donasi_data),
            "chart_donasi_data": json.dumps(chart_donasi_data),
            "priority_leads": priority_leads,
            "overdue_tagihan": overdue_tagihan,
            "potential_donatur": potential_donatur,
        })
    return context
