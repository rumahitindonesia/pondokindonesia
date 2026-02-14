def is_superuser(request):
    return request.user.is_active and request.user.is_superuser

# CRM & Database
def can_view_lead(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('core.view_lead'))

def can_view_santri(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('crm.view_santri'))

def can_view_donatur(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('crm.view_donatur'))

def can_view_program(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('crm.view_program'))

# Keuangan & Donasi
def can_view_tagihan(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('crm.view_tagihan'))

def can_view_donasi(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('crm.view_transaksidonasi'))

# Integrasi & AI
def can_view_aiknowledge(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('core.view_aiknowledgebase'))

# Pengaturan & Manajemen
def can_view_user(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('users.view_user'))

def can_view_apisetting(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('core.view_apisetting'))

def can_view_role(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('users.view_role'))

def can_view_pengurus(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_pengurus'))

def can_view_jabatan(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_jabatan'))

def can_view_tugas(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_tugas'))
