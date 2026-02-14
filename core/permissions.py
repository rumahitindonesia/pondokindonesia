def is_superuser(request):
    return request.user.is_superuser

def is_cs(request):
    if request.user.is_superuser:
        return True
    return hasattr(request.user, 'role') and request.user.role and request.user.role.slug == 'cs'

def is_admin_psb(request):
    if request.user.is_superuser:
        return True
    return hasattr(request.user, 'role') and request.user.role and request.user.role.slug == 'admin-psb'

def is_manager(request):
    """Admin PSB or Superuser"""
    if request.user.is_superuser:
        return True
    return hasattr(request.user, 'role') and request.user.role and request.user.role.slug in ['admin-psb']

def is_cs_or_admin(request):
    """CS or Admin PSB"""
    if request.user.is_superuser:
        return True
    return hasattr(request.user, 'role') and request.user.role and request.user.role.slug in ['cs', 'admin-psb']
