def get_site_header(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant and request.user.is_authenticated and not request.user.is_superuser:
        tenant = getattr(request.user, 'tenant', None)
    
    if tenant:
        return tenant.name
    return "Pondok Indonesia"

def get_site_title(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant and request.user.is_authenticated and not request.user.is_superuser:
        tenant = getattr(request.user, 'tenant', None)
    
    if tenant:
        return f"{tenant.name} Admin"
    return "Pondok Indonesia Admin"
