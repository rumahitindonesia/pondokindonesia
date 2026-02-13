
from django.core.exceptions import ValidationError
import re

RESERVED_SUBDOMAINS = {
    'www', 'admin', 'api', 'public', 'dashboard', 'app', 'login', 'register',
    'static', 'media', 'mail', 'smtp', 'pop', 'imap', 'ftp', 'cpanel',
    'whm', 'webmail', 'root', 'support', 'help', 'docs', 'billing',
    'status', 'monitor', 'dev', 'staging', 'test', 'demo', 'saas',
    'pondok', 'rumahit', 'assets', 'cdn', 'auth', 'account'
}

def validate_subdomain(value):
    """
    Validates that the subdomain is not a reserved keyword and follows
    valid domain naming conventions (only alphanumeric and hyphens).
    """
    value = value.lower()
    
    if value in RESERVED_SUBDOMAINS:
        raise ValidationError(f"'{value}' is a reserved system subdomain and cannot be used.")
    
    if len(value) < 3:
        raise ValidationError("Subdomain must be at least 3 characters long.")
        
    if not re.match(r'^[a-z0-9-]+$', value):
        raise ValidationError("Subdomain can only contain lowercase letters, numbers, and hyphens.")
        
    if value.startswith('-') or value.endswith('-'):
        raise ValidationError("Subdomain cannot start or end with a hyphen.")
