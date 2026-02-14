def is_superuser(request):
    return request.user.is_active and request.user.is_superuser

def is_cs(request):
    """Can view leads"""
    return request.user.is_active and (request.user.is_superuser or request.user.has_perm('core.view_lead'))

def is_admin_psb(request):
    """Can view financial data or AI knowledge base"""
    return request.user.is_active and (
        request.user.is_superuser or 
        request.user.has_perm('crm.view_tagihan') or 
        request.user.has_perm('core.view_aiknowledgebase')
    )

def is_manager(request):
    """Can manage users or change API settings"""
    return request.user.is_active and (
        request.user.is_superuser or 
        request.user.has_perm('users.view_user') or 
        request.user.has_perm('core.change_apisetting')
    )

def is_cs_or_admin(request):
    """Can view CRM data (Leads, Santri, etc)"""
    return request.user.is_active and (
        request.user.is_superuser or 
        request.user.has_perm('core.view_lead') or 
        request.user.has_perm('crm.view_santri')
    )
