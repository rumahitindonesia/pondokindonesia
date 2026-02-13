from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Santri, Donatur, Program, Tagihan, TransaksiDonasi

class SantriResource(resources.ModelResource):
    def __init__(self, request=None):
        super().__init__()
        self.request = request

    def before_import_row(self, row, **kwargs):
        if self.request and hasattr(self.request, 'tenant'):
            row['tenant'] = self.request.tenant.id

    class Meta:
        model = Santri
        fields = ('nis', 'nama_lengkap', 'nama_panggilan', 'tgl_lahir', 'alamat', 'nama_wali', 'no_hp_wali', 'status')
        import_id_fields = ('nis',)
        
class DonaturResource(resources.ModelResource):
    def __init__(self, request=None):
        super().__init__()
        self.request = request

    def before_import_row(self, row, **kwargs):
        if self.request and hasattr(self.request, 'tenant'):
            row['tenant'] = self.request.tenant.id

    class Meta:
        model = Donatur
        fields = ('kode_donatur', 'nama_donatur', 'no_hp', 'kategori', 'alamat')
        import_id_fields = ('kode_donatur',)

class ProgramResource(resources.ModelResource):
    def __init__(self, request=None):
        super().__init__()
        self.request = request

    def before_import_row(self, row, **kwargs):
        if self.request and hasattr(self.request, 'tenant'):
            row['tenant'] = self.request.tenant.id

    class Meta:
        model = Program
        fields = ('nama_program', 'jenis', 'nominal_standar', 'keterangan')
        import_id_fields = ('nama_program',)

class TagihanResource(resources.ModelResource):
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

    def __init__(self, request=None):
        super().__init__()
        self.request = request

    def before_import_row(self, row, **kwargs):
        if self.request and hasattr(self.request, 'tenant'):
            row['tenant'] = self.request.tenant.id

    class Meta:
        model = Tagihan
        fields = ('santri', 'program', 'nominal', 'bulan', 'status', 'tgl_bayar', 'keterangan')

class TransaksiDonasiResource(resources.ModelResource):
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

    def __init__(self, request=None):
        super().__init__()
        self.request = request

    def before_import_row(self, row, **kwargs):
        if self.request and hasattr(self.request, 'tenant'):
            row['tenant'] = self.request.tenant.id

    class Meta:
        model = TransaksiDonasi
        fields = ('donatur', 'program', 'nominal', 'tgl_donasi', 'keterangan')
