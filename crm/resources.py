from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Santri, Donatur, Program, Tagihan, TransaksiDonasi

class BaseTenantResource(resources.ModelResource):
    def __init__(self, request=None, **kwargs):
        super().__init__()
        self.request = request

    def get_tenant(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request and not self.request.user.is_superuser:
            tenant = getattr(self.request.user, 'tenant', None)
        return tenant

    def before_import_row(self, row, **kwargs):
        tenant = self.get_tenant()
        if tenant:
            row['tenant'] = tenant.id

class SantriResource(BaseTenantResource):
    class Meta:
        model = Santri
        fields = ('nis', 'nama_lengkap', 'nama_panggilan', 'tgl_lahir', 'alamat', 'nama_wali', 'no_hp_wali', 'status')
        import_id_fields = ('nis',)
        
class DonaturResource(BaseTenantResource):
    class Meta:
        model = Donatur
        fields = ('kode_donatur', 'nama_donatur', 'no_hp', 'kategori', 'alamat')
        import_id_fields = ('kode_donatur',)

class ProgramResource(BaseTenantResource):
    class Meta:
        model = Program
        fields = ('nama_program', 'jenis', 'nominal_standar', 'keterangan')
        import_id_fields = ('nama_program',)

class TagihanResource(BaseTenantResource):
    santri = fields.Field(
        column_name='santri_nis',
        attribute='santri',
        widget=ForeignKeyWidget(Santri, 'nis')
    )
    program = fields.Field(
        column_name='program_nama',
        attribute='program',
        widget=ForeignKeyWidget(Program, 'nama_program')
    )

    def __init__(self, request=None, **kwargs):
        super().__init__(request, **kwargs)
        tenant = self.get_tenant()
        if tenant:
             self.fields['santri'].widget.queryset = Santri.objects.filter(tenant=tenant)
             self.fields['program'].widget.queryset = Program.objects.filter(tenant=tenant)

    class Meta:
        model = Tagihan
        fields = ('santri', 'program', 'nominal', 'bulan', 'status', 'tgl_bayar', 'keterangan')

class TagihanSPPResource(BaseTenantResource):
    santri = fields.Field(
        column_name='santri_nis',
        attribute='santri',
        widget=ForeignKeyWidget(Santri, 'nis')
    )

    def __init__(self, request=None, **kwargs):
        super().__init__(request, **kwargs)
        tenant = self.get_tenant()
        if tenant:
             self.fields['santri'].widget.queryset = Santri.objects.filter(tenant=tenant)

    class Meta:
        from .models import TagihanSPP
        model = TagihanSPP
        fields = ('santri', 'bulan', 'jumlah', 'jatuh_tempo', 'status', 'tanggal_bayar', 'catatan')
        import_id_fields = ('santri', 'bulan')

class TransaksiDonasiResource(BaseTenantResource):
    donatur = fields.Field(
        column_name='donatur_kode',
        attribute='donatur',
        widget=ForeignKeyWidget(Donatur, 'kode_donatur')
    )
    program = fields.Field(
        column_name='program_nama',
        attribute='program',
        widget=ForeignKeyWidget(Program, 'nama_program')
    )

    def __init__(self, request=None, **kwargs):
        super().__init__(request, **kwargs)
        tenant = self.get_tenant()
        if tenant:
             self.fields['donatur'].widget.queryset = Donatur.objects.filter(tenant=tenant)
             self.fields['program'].widget.queryset = Program.objects.filter(tenant=tenant)

    class Meta:
        model = TransaksiDonasi
        fields = ('donatur', 'program', 'nominal', 'tgl_donasi', 'keterangan')
