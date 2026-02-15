from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
import random
import string


class OTPVerification(models.Model):
    """OTP verification for public user authentication"""
    phone_number = models.CharField(_("Nomor WhatsApp"), max_length=20)
    otp_code = models.CharField(_("Kode OTP"), max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("OTP Verification")
        verbose_name_plural = _("OTP Verifications")
    
    def __str__(self):
        return f"{self.phone_number} - {self.otp_code}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # OTP valid for 5 minutes
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)


class PublicUserSession(models.Model):
    """Session management for public users (Wali Santri & Donatur)"""
    class UserType(models.TextChoices):
        WALI = 'WALI', _('Wali Santri')
        DONATUR = 'DONATUR', _('Donatur')
        CALON_WALI = 'CALON_WALI', _('Calon Wali (Lead)')
    
    phone_number = models.CharField(_("Nomor WhatsApp"), max_length=20)
    user_type = models.CharField(
        _("Tipe User"), 
        max_length=20, 
        choices=UserType.choices
    )
    
    # Links to actual data
    santri = models.ForeignKey(
        'crm.Santri', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='wali_sessions'
    )
    donatur = models.ForeignKey(
        'crm.Donatur', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='donatur_sessions'
    )
    lead = models.ForeignKey(
        'core.Lead',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lead_sessions'
    )
    
    # Session management
    session_key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_activity']
        verbose_name = _("Public User Session")
        verbose_name_plural = _("Public User Sessions")
    
    def __str__(self):
        return f"{self.phone_number} ({self.get_user_type_display()})"
    
    def is_expired(self):
        # Session expires after 24 hours of inactivity
        return timezone.now() > self.last_activity + timedelta(hours=24)
    
    def save(self, *args, **kwargs):
        if not self.session_key:
            # Generate random session key
            self.session_key = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        super().save(*args, **kwargs)
