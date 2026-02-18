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
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('crm.view_tagihanspp'))

def can_view_tagihanprogram(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('crm.view_tagihanprogram'))

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

def can_view_lokasikantor(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_lokasikantor'))

def can_view_absensi(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_absensi'))

def can_view_jadwalkerja(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_jadwalkerja'))

def can_view_periodepenilaian(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_periodepenilaian'))

def can_view_kamuskpi(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_kamuskpi'))

def can_view_targetkpi(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_targetkpi'))

def can_view_jenisamalan(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_jenisamalan'))

def can_view_logamalan(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_logamalan'))

def can_view_objective(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_objective'))

def can_view_keyresult(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('hr.view_keyresult'))

def can_view_tutorial(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('core.view_tutorial'))

def can_view_monthlytarget(request):
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('core.view_monthlytarget'))
