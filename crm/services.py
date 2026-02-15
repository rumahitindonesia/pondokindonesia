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
        Directly create a Santri record.
        """
        # Check duplicate
        phone = data.get('phone')
        if Santri.objects.filter(tenant=tenant, no_hp_wali=phone).exists():
            return None, "Santri dengan nomor HP tersebut sudah terdaftar."

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
