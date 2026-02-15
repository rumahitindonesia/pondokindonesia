from django.db.models.signals import post_save
from django.dispatch import receiver
from crm.models import Santri, Donatur
from core.models import Lead
from users.models import User
import logging

logger = logging.getLogger(__name__)


def normalize_phone(phone):
    """Normalize phone number to 62xxx format"""
    if not phone:
        return None
    
    phone = phone.strip().replace(' ', '').replace('-', '')
    
    if phone.startswith('62'):
        return phone
    elif phone.startswith('0'):
        return '62' + phone[1:]
    elif phone.startswith('+62'):
        return phone[1:]
    else:
        return '62' + phone


@receiver(post_save, sender=Santri)
def create_or_update_user_for_santri(sender, instance, created, **kwargs):
    """
    Auto-create or update User when Santri is created/updated
    Priority: WALI (highest)
    """
    if not instance.no_hp_wali:
        return
    
    phone_normalized = normalize_phone(instance.no_hp_wali)
    if not phone_normalized:
        return
    
    try:
        user, user_created = User.objects.get_or_create(
            phone_number=phone_normalized,
            defaults={
                'username': f'wali_{phone_normalized}',
                'user_type': User.UserType.WALI,
                'is_wali': True,
                'santri_id': instance.id,
                'tenant': instance.tenant,
                'is_staff': False,
                'is_active': True
            }
        )
        
        if not user_created:
            # Update existing user (upgrade from Lead/Donatur)
            # WALI has highest priority
            user.user_type = User.UserType.WALI
            user.is_wali = True
            user.santri_id = instance.id
            if not user.tenant:
                user.tenant = instance.tenant
            user.save()
            logger.info(f"Updated User {user.id} for Santri {instance.nama_lengkap}")
        else:
            logger.info(f"Created User {user.id} for Santri {instance.nama_lengkap}")
    
    except Exception as e:
        logger.error(f"Error creating/updating User for Santri {instance.id}: {str(e)}")


@receiver(post_save, sender=Donatur)
def create_or_update_user_for_donatur(sender, instance, created, **kwargs):
    """
    Auto-create or update User when Donatur is created/updated
    Priority: DONATUR (medium)
    """
    if not instance.no_hp:
        return
    
    phone_normalized = normalize_phone(instance.no_hp)
    if not phone_normalized:
        return
    
    try:
        user, user_created = User.objects.get_or_create(
            phone_number=phone_normalized,
            defaults={
                'username': f'donatur_{phone_normalized}',
                'user_type': User.UserType.DONATUR,
                'is_donatur': True,
                'donatur_id': instance.id,
                'tenant': instance.tenant,
                'is_staff': False,
                'is_active': True
            }
        )
        
        if not user_created:
            # Update existing user only if not already WALI
            if user.user_type != User.UserType.WALI:
                user.user_type = User.UserType.DONATUR
            user.is_donatur = True
            user.donatur_id = instance.id
            if not user.tenant:
                user.tenant = instance.tenant
            user.save()
            logger.info(f"Updated User {user.id} for Donatur {instance.nama_donatur}")
        else:
            logger.info(f"Created User {user.id} for Donatur {instance.nama_donatur}")
    
    except Exception as e:
        logger.error(f"Error creating/updating User for Donatur {instance.id}: {str(e)}")


@receiver(post_save, sender=Lead)
def create_or_update_user_for_lead(sender, instance, created, **kwargs):
    """
    Auto-create or update User when Lead is created/updated
    Priority: LEAD (lowest)
    """
    if not instance.phone_number:
        return
    
    phone_normalized = normalize_phone(instance.phone_number)
    if not phone_normalized:
        return
    
    try:
        user, user_created = User.objects.get_or_create(
            phone_number=phone_normalized,
            defaults={
                'username': f'lead_{phone_normalized}',
                'user_type': User.UserType.LEAD,
                'is_lead': True,
                'lead_id': instance.id,
                'tenant': instance.tenant,
                'is_staff': False,
                'is_active': True
            }
        )
        
        if not user_created:
            # Update existing user only if not already WALI or DONATUR
            if user.user_type not in [User.UserType.WALI, User.UserType.DONATUR]:
                user.user_type = User.UserType.LEAD
            user.is_lead = True
            user.lead_id = instance.id
            if not user.tenant:
                user.tenant = instance.tenant
            user.save()
            logger.info(f"Updated User {user.id} for Lead {instance.name}")
        else:
            logger.info(f"Created User {user.id} for Lead {instance.name}")
    
    except Exception as e:
        logger.error(f"Error creating/updating User for Lead {instance.id}: {str(e)}")
