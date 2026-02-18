from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from tenants.models import Tenant
from core.models import Lead, TenantSubscription, WhatsAppMessage
from crm.models import Santri, Donatur, TagihanSPP, TagihanProgram, TransaksiDonasi
from hr.models import Pengurus, Absensi, Tugas, LogAmalan, JenisAmalan

def _get_db_size():
    """Returns database size in MB."""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT SUM(data_length + index_length) / 1024 / 1024 AS size FROM information_schema.TABLES WHERE table_schema = DATABASE()")
            row = cursor.fetchone()
            return float(row[0]) if row and row[0] else 0
    except Exception:
        return 0

def _get_disk_usage():
    """Returns disk usage percentage and free space in GB."""
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        percent = (used / total) * 100
        return percent, free / (1024**3)
    except Exception:
        return 0, 0

def _get_ram_usage():
    """Returns RAM usage percentage from /proc/meminfo."""
    try:
        mem_info = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    mem_info[parts[0].strip()] = int(parts[1].split()[0])
        
        total = mem_info.get('MemTotal', 0)
        available = mem_info.get('MemAvailable', 0)
        used = total - available
        percent = (used / total) * 100 if total > 0 else 0
        return percent
    except Exception:
        return 0

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

        # Server Metrics
        db_size = _get_db_size()
        disk_percent, disk_free = _get_disk_usage()
        ram_percent = _get_ram_usage()

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
            "server_info": [
                {
                    "title": "Database Size",
                    "metric": f"{db_size:.1f} MB",
                    "icon": "database",
                    "color": "purple",
                    "footer": "Total MySQL Storage",
                },
                {
                    "title": "Disk Usage",
                    "metric": f"{disk_percent:.1f}%",
                    "icon": "storage",
                    "color": "red" if disk_percent > 85 else "blue",
                    "footer": f"{disk_free:.1f} GB Tersedia",
                },
                {
                    "title": "RAM Usage",
                    "metric": f"{ram_percent:.1f}%",
                    "icon": "memory",
                    "color": "red" if ram_percent > 90 else "green",
                    "footer": "Physical Memory Stats",
                },
            ]
        })
    else:
        # --- TENANT DASHBOARD ---
        # Scoped to current tenant
        total_santri = Santri.objects.filter(tenant=tenant, status='AKTIF').count()
        total_donatur = Donatur.objects.filter(tenant=tenant).count()
        
        # --- TARGET BULANAN ---
        now = timezone.now()
        from core.models import MonthlyTarget
        monthly_target = MonthlyTarget.objects.filter(tenant=tenant, month=now.month, year=now.year).first()
        
        target_donasi = monthly_target.target_donasi if monthly_target else 0
        target_santri = monthly_target.target_santri_baru if monthly_target else 0
        
        # Financials (This Month)
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Role-based scoping for leads
        is_cs = (user.role.slug == 'cs' or user.role.slug.startswith('cs-')) if user.role else False
        lead_base_qs = Lead.objects.filter(tenant=tenant)
        if is_cs:
            lead_base_qs = lead_base_qs.filter(cs=user)
            
        total_santri_month = Santri.objects.filter(
            tenant=tenant,
            tgl_masuk__gte=first_day_of_month
        ).count()
        
        total_donasi_month = TransaksiDonasi.objects.filter(
            tenant=tenant, 
            status=TransaksiDonasi.Status.VERIFIED,  # Only count verified donations
            tgl_donasi__gte=first_day_of_month
        ).aggregate(total=Sum('nominal'))['total'] or 0
        
        # Calculate Progress
        donasi_progress = (total_donasi_month / target_donasi * 100) if target_donasi > 0 else 0
        santri_progress = (total_santri_month / target_santri * 100) if target_santri > 0 else 0

        # 1. New TagihanProgram (Registration, Program fees, etc)
        total_tagihan_program = TagihanProgram.objects.filter(
            tenant=tenant,
            status='LUNAS',
            tanggal_bayar__gte=first_day_of_month
        ).aggregate(total=Sum('nominal'))['total'] or 0
        
        # 2. New TagihanSPP (Monthly tuition)
        total_tagihan_spp = TagihanSPP.objects.filter(
            tenant=tenant,
            status='LUNAS',
            tanggal_bayar__gte=first_day_of_month
        ).aggregate(total=Sum('jumlah'))['total'] or 0

        total_non_donasi_month = total_tagihan_program + total_tagihan_spp
        
        # Unpaid Bills
        unpaid_program = TagihanProgram.objects.filter(
            tenant=tenant, 
            status__in=['BELUM', 'TERLAMBAT']
        ).count()
        
        unpaid_spp = TagihanSPP.objects.filter(
            tenant=tenant,
            status__in=['BELUM_LUNAS', 'TERLAMBAT']
        ).count()
        
        unpaid_bills_count = unpaid_program + unpaid_spp

        # Lead Status Distribution
        leads_new = lead_base_qs.filter(status='NEW').count()
        
        # --- SDM & AMALAN METRICS (New) ---
        total_staff = Pengurus.objects.filter(tenant=tenant, is_active=True).count()
        absensi_today = Absensi.objects.filter(
            tenant=tenant, 
            tanggal=now.date(), 
            status__in=['HADIR', 'TERLAMBAT']
        ).count()
        attendance_percent = (absensi_today / total_staff * 100) if total_staff > 0 else 0
        
        active_tasks = Tugas.objects.filter(
            tenant=tenant, 
            status__in=['BARU', 'PROSES']
        ).count()
        
        amalan_today_total = LogAmalan.objects.filter(tenant=tenant, tanggal=now.date()).count()
        amalan_today_done = LogAmalan.objects.filter(tenant=tenant, tanggal=now.date(), is_done=True).count()
        amalan_percent = (amalan_today_done / amalan_today_total * 100) if amalan_today_total > 0 else 0
        
        # --- SDM CHART DATA (Last 7 Days) ---
        sdm_labels = []
        attendance_trend = []
        amalan_trend = []
        
        for i in range(6, -1, -1):
            day = now.date() - timedelta(days=i)
            sdm_labels.append(day.strftime('%d %b'))
            
            # Attendance
            daily_absensi = Absensi.objects.filter(
                tenant=tenant, 
                tanggal=day, 
                status__in=['HADIR', 'TERLAMBAT']
            ).count()
            att_percent = (daily_absensi / total_staff * 100) if total_staff > 0 else 0
            attendance_trend.append(att_percent)
            
            # Amalan
            daily_amalan_total = LogAmalan.objects.filter(tenant=tenant, tanggal=day).count()
            daily_amalan_done = LogAmalan.objects.filter(tenant=tenant, tanggal=day, is_done=True).count()
            amal_percent = (daily_amalan_done / daily_amalan_total * 100) if daily_amalan_total > 0 else 0
            amalan_trend.append(amal_percent)

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

        # 2. Overdue Fees (Top 5)
        # Combine SPP and Program fees
        overdue_tagihan = TagihanSPP.objects.filter(
            tenant=tenant,
            status='TERLAMBAT'
        ).order_by('jatuh_tempo')[:5]
        
        if not overdue_tagihan.exists():
            overdue_tagihan = TagihanProgram.objects.filter(
                tenant=tenant, 
                status='TERLAMBAT'
            ).order_by('jatuh_tempo')[:5]

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
        
        # Fetch data - TagihanProgram
        program_query = TagihanProgram.objects.filter(
            tenant=tenant,
            status='LUNAS',
            tanggal_bayar__year=now.year,
            tanggal_bayar__month=now.month
        ).annotate(day=TruncDate('tanggal_bayar')).values('day').annotate(total=Sum('nominal'))

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
        for entry in program_query:
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
                    "footer": f"Target: Rp {target_donasi:,.0f} ({donasi_progress:.1f}%)",
                },
            ],
            "kpi_cards": [
                {
                    "title": "Santri Aktif",
                    "metric": total_santri,
                    "icon": "school",
                    "color": "primary",
                    "footer": f"Target Baru: {total_santri_month}/{target_santri} ({santri_progress:.1f}%)",
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
                {
                    "title": "Presensi Hari Ini",
                    "metric": f"{attendance_percent:.0f}%",
                    "icon": "fingerprint",
                    "color": "green" if attendance_percent > 80 else "orange",
                    "footer": f"{absensi_today} staff hadir dari {total_staff}",
                },
                {
                    "title": "Tugas On-Progress",
                    "metric": active_tasks,
                    "icon": "assignment",
                    "color": "blue",
                    "footer": "Tugas staff belum selesai",
                },
                {
                    "title": "Progress Amalan",
                    "metric": f"{amalan_percent:.0f}%",
                    "icon": "auto_stories",
                    "color": "purple",
                    "footer": "Rata-rata amalan yaumiah",
                },
            ],
            "chart_labels": json.dumps(chart_labels),
            "chart_non_donasi_data": json.dumps(chart_non_donasi_data),
            "chart_donasi_data": json.dumps(chart_donasi_data),
            "chart_sdm_labels": json.dumps(sdm_labels),
            "chart_attendance_trend": json.dumps(attendance_trend),
            "chart_amalan_trend": json.dumps(amalan_trend),
            "priority_leads": priority_leads,
            "overdue_tagihan": overdue_tagihan,
            "potential_donatur": potential_donatur,
        })

    # --- Group Models by Sidebar Categories ---
    if 'app_list' in context:
        groups = {
            "Manajemen Pengelola": ["Tenants", "Users", "Roles", "Pricing Plans", "Tenant Subscriptions"],
            "CRM & Database": ["Leads / Pendaftar", "Data Santri", "Data Donatur", "Master Program"],
            "Keuangan & Donasi": ["Tagihan SPP", "Tagihan Program", "Metode Pembayaran", "Pembayaran SPP", "Transaksi Donasi"],
            "Integrasi WhatsApp & AI": ["AI Knowledge Base", "WhatsApp Messages", "WhatsApp Auto Replies", "WhatsApp Forms"],
            "Pengaturan & SDM": [
                "API Settings", "Daftar Pengurus", "Daftar Jabatan", "Daftar Tugas", 
                "Jadwal Kerja", "Lokasi Kantor", "Data Absensi", "Log Amalan", 
                "Target KPI", "Periode Penilaian", "Kamus KPI", "Jenis Amalan",
                "Objectives", "Key Results"
            ],
        }
        
        mapped_model_names = set()
        grouped_apps = []
        all_models = {}
        
        # Flatten app_list for easier mapping
        for app in context['app_list']:
            for model in app['models']:
                all_models[model['name']] = model
        
        for group_title, model_names in groups.items():
            group_models = []
            for name in model_names:
                if name in all_models:
                    group_models.append(all_models.pop(name))
            
            if group_models:
                grouped_apps.append({
                    "name": group_title,
                    "models": group_models
                })
        
        # Fallback for models not in explicit groups (prevents missing menus)
        if all_models:
            grouped_apps.append({
                "name": "Fitur Lainnya",
                "models": list(all_models.values())
            })
        
        context['grouped_apps'] = grouped_apps

    return context
