from django.db import models
from .validators import validate_subdomain

class Tenant(models.Model):
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=100, unique=True, validators=[validate_subdomain])
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.subdomain})"
