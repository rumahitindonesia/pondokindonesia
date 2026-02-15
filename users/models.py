from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, UserManager
from core.models import TenantAwareModel, TenantManager, get_current_tenant

class Role(TenantAwareModel):
    objects = TenantManager(include_global=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    permissions = models.ManyToManyField(Permission, blank=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        unique_together = ('slug', 'tenant')

    def __str__(self):
        scope = "Global" if not self.tenant else f"Tenant: {self.tenant}"
        return f"{self.name} ({scope})"

class TenantUserManager(UserManager):
    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            # Strict: Only users belonging to this tenant
            return super().get_queryset().filter(tenant=tenant)
        # Central: Only users with no tenant assigned (Global/SaaS Admins)
        return super().get_queryset().filter(tenant__isnull=True)

class User(AbstractUser):
    class UserType(models.TextChoices):
        STAFF = 'STAFF', 'Staff/Admin'
        WALI = 'WALI', 'Wali Santri'
        DONATUR = 'DONATUR', 'Donatur'
        LEAD = 'LEAD', 'Calon Wali/Donatur'
    
    role = models.ForeignKey(
        'Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_users'
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        related_name='users',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        help_text="Format: 08xxxxxxxx or 628xxxxxxxx"
    )
    
    # Public user management fields
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.STAFF,
        help_text="User type for portal access control"
    )
    
    # Role tracking (for users with multiple roles)
    is_wali = models.BooleanField(
        default=False,
        help_text="User is a Wali Santri"
    )
    is_donatur = models.BooleanField(
        default=False,
        help_text="User is a Donatur"
    )
    is_lead = models.BooleanField(
        default=False,
        help_text="User is/was a Lead"
    )
    
    # Related record IDs (for quick lookup)
    santri_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of related Santri record (if Wali)"
    )
    donatur_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of related Donatur record"
    )
    lead_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of original Lead record (for conversion tracking)"
    )

    objects = TenantUserManager()
    all_objects = models.Manager()

    def __str__(self):
        if self.is_staff:
            role_name = self.role.name if self.role else "No Role"
            return f"{self.username} ({role_name})"
        else:
            return f"{self.phone_number} ({self.get_user_type_display()})"
