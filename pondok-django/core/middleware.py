from django.utils.deprecation import MiddlewareMixin
from tenants.models import Tenant
from .models import set_current_tenant

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host().split(':')[0]
        parts = host.split('.')
        
        if len(parts) > 1:
            subdomain = parts[0]
            try:
                tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
                request.tenant = tenant
                set_current_tenant(tenant)
            except Tenant.DoesNotExist:
                request.tenant = None
                set_current_tenant(None)
        else:
            request.tenant = None
            set_current_tenant(None)

    def process_response(self, request, response):
        set_current_tenant(None)
        return response
