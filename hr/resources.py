from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Jabatan, Pengurus
from users.models import User

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

class JabatanResource(BaseTenantResource):
    class Meta:
        model = Jabatan
        fields = ('id', 'nama', 'deskripsi', 'atasan')
        import_id_fields = ('id',)

class PengurusResource(BaseTenantResource):
    jabatan = fields.Field(
        column_name='jabatan_nama',
        attribute='jabatan',
        widget=ForeignKeyWidget(Jabatan, 'nama')
    )
    user = fields.Field(
        column_name='username',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )

    def __init__(self, request=None, **kwargs):
        super().__init__(request, **kwargs)
        tenant = self.get_tenant()
        if tenant:
             self.fields['jabatan'].widget.queryset = Jabatan.objects.filter(tenant=tenant)
             self.fields['user'].widget.queryset = User.objects.filter(tenant=tenant)

    class Meta:
        model = Pengurus
        fields = ('id', 'nama', 'nik', 'jabatan', 'telepon', 'alamat', 'is_active')
        import_id_fields = ('id',)
