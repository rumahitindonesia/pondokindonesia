from django.utils import timezone
from core.models import Lead
from crm.models import Santri, Donatur, TransaksiDonasi, Program

class CRMService:
    @staticmethod
    def convert_lead(lead, target_type):
        """
        Convert a Lead to Santri or Donatur.
        """
        if target_type == Lead.Type.SANTRI:
            return CRMService.direct_insert_santri(
                tenant=lead.tenant,
                data={
                    'nama': lead.name,
                    'phone': lead.phone_number,
                    'alamat': lead.data.get('alamat', '-')
                },
                source_lead=lead
            )
        elif target_type == Lead.Type.DONATUR:
            return CRMService.direct_insert_donatur(
                tenant=lead.tenant,
                data={
                    'nama': lead.name,
                    'phone': lead.phone_number,
                    'alamat': lead.data.get('alamat', '-')
                },
                source_lead=lead
            )
        return None

    @staticmethod
    def direct_insert_santri(tenant, data, staff_user=None, source_lead=None):
        """
        Directly create a Santri record or update linked one.
        """
        # 1. Check if Lead is already linked to a Santri
        if source_lead and getattr(source_lead, 'santri', None):
            santri = source_lead.santri
            # Update fields if needed (optional, but good for consistency)
            if data.get('alamat') and (not santri.alamat or santri.alamat == '-'):
                santri.alamat = data.get('alamat')
            if not santri.pic_admin and staff_user:
                santri.pic_admin = staff_user
            
            # Ensure status is ACTIVE if coming from conversion
            if santri.status == Santri.Status.CALON:
                 santri.status = Santri.Status.AKTIF
            
            santri.save()
            
            # Close Lead
            source_lead.status = Lead.Status.CLOSED
            source_lead.save()
            
            return santri, "Santri berhasil diperbarui (Link Existing)."

        # 2. Check duplicate by phone
        phone = data.get('phone')
        if Santri.objects.filter(tenant=tenant, no_hp_wali=phone).exists():
            return None, "Santri dengan nomor HP tersebut sudah terdaftar."

        # 3. Create New
        # Generate NIS: REG-YYMM-ID
        today = timezone.now()
        suffix = source_lead.id if source_lead else "WA"
        nis = f"REG-{today.strftime('%y%m')}-{suffix}"
        
        santri = Santri.objects.create(
            tenant=tenant,
            nis=nis,
            nama_lengkap=data.get('nama'),
            nama_wali=data.get('nama'),
            no_hp_wali=phone,
            alamat=data.get('alamat', '-'),
            pic_admin=staff_user,
            status=Santri.Status.AKTIF
        )
        
        if source_lead:
            source_lead.status = Lead.Status.CLOSED
            source_lead.santri = santri # Link it for future reference
            source_lead.save()
            
        return santri, "Santri berhasil dibuat."

    @staticmethod
    def direct_insert_donatur(tenant, data, staff_user=None, source_lead=None):
        """
        Directly create a Donatur record.
        """
        phone = data.get('phone')
        if Donatur.objects.filter(tenant=tenant, no_hp=phone).exists():
            return None, "Donatur dengan nomor HP tersebut sudah terdaftar."

        # Generate Kode: DON-YYMM-ID
        today = timezone.now()
        suffix = source_lead.id if source_lead else "WA"
        kode = f"DON-{today.strftime('%y%m')}-{suffix}"
        
        donatur = Donatur.objects.create(
            tenant=tenant,
            kode_donatur=kode,
            nama_donatur=data.get('nama'),
            no_hp=phone,
            alamat=data.get('alamat', '-'),
            pic_fundraiser=staff_user,
            kategori=Donatur.Kategori.INSIDENTIL
        )
        
        if source_lead:
            source_lead.status = Lead.Status.CLOSED
            source_lead.save()
            
        return donatur, "Donatur berhasil dibuat."

    @staticmethod
    def direct_insert_donation(tenant, data, staff_user=None):
        """
        Directly create a TransaksiDonasi record.
        data: { 'donatur_kode': 'D001', 'program_nama': 'Zakat', 'nominal': 50000, 'keterangan': '...' }
        """
        try:
            donatur = Donatur.objects.get(tenant=tenant, kode_donatur=data.get('donatur_kode'))
            program = Program.objects.get(tenant=tenant, nama_program__iexact=data.get('program_nama'))
            
            transaksi = TransaksiDonasi.objects.create(
                tenant=tenant,
                donatur=donatur,
                program=program,
                nominal=data.get('nominal'),
                keterangan=data.get('keterangan', 'Input via WA'),
                status=TransaksiDonasi.Status.VERIFIED # Staff input assumes verified
            )
            return transaksi, f"Donasi Rp {transaksi.nominal} berhasil dicatat untuk {donatur.nama_donatur}."
        except Donatur.DoesNotExist:
            return None, "Error: Kode Donatur tidak ditemukan."
        except Program.DoesNotExist:
            return None, "Error: Nama Program tidak ditemukan."
        except Exception as e:
            return None, f"Error: {str(e)}"

    @staticmethod
    def search_records(tenant, target_type, query):
        """
        Search for records (Santri or Donatur) by name and return formatted string.
        """
        if target_type == 'donatur':
            results = Donatur.objects.filter(tenant=tenant, nama_donatur__icontains=query)[:5]
            if not results: return f"Pencarian donatur '{query}' tidak ditemukan."
            
            msg = f"Hasil pencarian Donatur '{query}':\n"
            for d in results:
                msg += f"- {d.kode_donatur}: {d.nama_donatur}\n"
            return msg
        
        elif target_type == 'santri':
            results = Santri.objects.filter(tenant=tenant, nama_lengkap__icontains=query)[:5]
            if not results: return f"Pencarian santri '{query}' tidak ditemukan."
            
            msg = f"Hasil pencarian Santri '{query}':\n"
            for s in results:
                msg += f"- {s.nis}: {s.nama_lengkap}\n"
            return msg
        
    @staticmethod
    def get_revenue_stats(tenant, period='total'):
        """
        Calculate total revenue from verified donations and paid tuition fees.
        period: 'today', 'month', 'total'
        """
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import datetime
        
        now = timezone.now()
        
        # 1. Base Querysets
        donations = TransaksiDonasi.objects.filter(tenant=tenant, status=TransaksiDonasi.Status.VERIFIED)
        spp = TagihanSPP.objects.filter(tenant=tenant, status=TagihanSPP.Status.LUNAS)
        programs = TagihanProgram.objects.filter(tenant=tenant, status=TagihanProgram.Status.LUNAS)
        
        # 2. Date Filtering
        date_label = "Keseluruhan"
        if period == 'today':
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            donations = donations.filter(tgl_donasi__gte=start_of_day)
            spp = spp.filter(tanggal_bayar=now.date())
            programs = programs.filter(tanggal_bayar=now.date())
            date_label = f"Hari Ini ({now.strftime('%d %b %Y')})"
        elif period == 'month':
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            donations = donations.filter(tgl_donasi__gte=start_of_month)
            # SPP uses tanggal_bayar for actual cash flow
            spp = spp.filter(tanggal_bayar__year=now.year, tanggal_bayar__month=now.month)
            programs = programs.filter(tanggal_bayar__year=now.year, tanggal_bayar__month=now.month)
            date_label = f"Bulan Ini ({now.strftime('%B %Y')})"
        
        # 3. Aggregation
        total_donasi = donations.aggregate(total=Sum('nominal'))['total'] or 0
        total_spp = spp.aggregate(total=Sum('jumlah'))['total'] or 0
        total_program = programs.aggregate(total=Sum('nominal'))['total'] or 0
        
        grand_total = total_donasi + total_spp + total_program
        
        def fmt_idr(val): return f"Rp {val:,.0f}"
        
        msg = f"📊 *Laporan Omzet ({date_label})*\n\n"
        msg += f"💰 Donasi: {fmt_idr(total_donasi)}\n"
        msg += f"🏫 SPP: {fmt_idr(total_spp)}\n"
        msg += f"🏷️ Program: {fmt_idr(total_program)}\n"
        msg += f"--------------------------\n"
        msg += f"🏆 *TOTAL: {fmt_idr(grand_total)}*"
        
        return msg
