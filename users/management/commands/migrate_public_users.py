from django.core.management.base import BaseCommand
from crm.models import Santri, Donatur
from core.models import Lead
from users.models import User
from django.db import transaction
from django.db.models import Q


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


class Command(BaseCommand):
    help = 'Migrate existing Santri, Donatur, and Lead records to User table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making any changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        stats = {
            'santri_created': 0,
            'santri_updated': 0,
            'santri_skipped': 0,
            'donatur_created': 0,
            'donatur_updated': 0,
            'donatur_skipped': 0,
            'lead_created': 0,
            'lead_updated': 0,
            'lead_skipped': 0,
        }
        
        # Migrate Santri (Wali) - Priority 1
        self.stdout.write(self.style.SUCCESS('\n=== Migrating Santri (Wali) ==='))
        for santri in Santri.objects.all():
            if not santri.no_hp_wali:
                stats['santri_skipped'] += 1
                continue
            
            phone_normalized = normalize_phone(santri.no_hp_wali)
            if not phone_normalized:
                stats['santri_skipped'] += 1
                continue
            
            try:
                if not dry_run:
                    with transaction.atomic():
                        # Try to find user by phone or username
                        username = f'wali_{phone_normalized}'
                        user = User.objects.filter(
                            Q(phone_number=phone_normalized) | Q(username=username)
                        ).first()
                        
                        if user:
                            # Update existing user
                            if not user.phone_number:
                                user.phone_number = phone_normalized
                            user.user_type = User.UserType.WALI
                            user.is_wali = True
                            user.santri_id = santri.id
                            if not user.tenant:
                                user.tenant = santri.tenant
                            user.save()
                            stats['santri_updated'] += 1
                            self.stdout.write(f'  Updated: {santri.nama_lengkap} ({phone_normalized})')
                        else:
                            # Create new user
                            user = User.objects.create(
                                username=username,
                                phone_number=phone_normalized,
                                user_type=User.UserType.WALI,
                                is_wali=True,
                                santri_id=santri.id,
                                tenant=santri.tenant,
                                is_staff=False,
                                is_active=True
                            )
                            stats['santri_created'] += 1
                            self.stdout.write(self.style.SUCCESS(f'  Created: {santri.nama_lengkap} ({phone_normalized})'))
                else:
                    self.stdout.write(f'  [DRY RUN] Would process: {santri.nama_lengkap} ({phone_normalized})')
                    stats['santri_created'] += 1
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {santri.nama_lengkap} - {str(e)}'))
                stats['santri_skipped'] += 1
        
        # Migrate Donatur - Priority 2
        self.stdout.write(self.style.SUCCESS('\n=== Migrating Donatur ==='))
        for donatur in Donatur.objects.all():
            if not donatur.no_hp:
                stats['donatur_skipped'] += 1
                continue
            
            phone_normalized = normalize_phone(donatur.no_hp)
            if not phone_normalized:
                stats['donatur_skipped'] += 1
                continue
            
            try:
                if not dry_run:
                    with transaction.atomic():
                        username = f'donatur_{phone_normalized}'
                        user = User.objects.filter(
                            Q(phone_number=phone_normalized) | Q(username=username)
                        ).first()
                        
                        if user:
                            # Update existing user
                            if not user.phone_number:
                                user.phone_number = phone_normalized
                            if user.user_type != User.UserType.WALI:
                                user.user_type = User.UserType.DONATUR
                            user.is_donatur = True
                            user.donatur_id = donatur.id
                            if not user.tenant:
                                user.tenant = donatur.tenant
                            user.save()
                            stats['donatur_updated'] += 1
                            self.stdout.write(f'  Updated: {donatur.nama_donatur} ({phone_normalized})')
                        else:
                            user = User.objects.create(
                                username=username,
                                phone_number=phone_normalized,
                                user_type=User.UserType.DONATUR,
                                is_donatur=True,
                                donatur_id=donatur.id,
                                tenant=donatur.tenant,
                                is_staff=False,
                                is_active=True
                            )
                            stats['donatur_created'] += 1
                            self.stdout.write(self.style.SUCCESS(f'  Created: {donatur.nama_donatur} ({phone_normalized})'))
                else:
                    self.stdout.write(f'  [DRY RUN] Would process: {donatur.nama_donatur} ({phone_normalized})')
                    stats['donatur_created'] += 1
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {donatur.nama_donatur} - {str(e)}'))
                stats['donatur_skipped'] += 1
        
        # Migrate Lead - Priority 3
        self.stdout.write(self.style.SUCCESS('\n=== Migrating Lead ==='))
        for lead in Lead.objects.all():
            if not lead.phone_number:
                stats['lead_skipped'] += 1
                continue
            
            phone_normalized = normalize_phone(lead.phone_number)
            if not phone_normalized:
                stats['lead_skipped'] += 1
                continue
            
            try:
                if not dry_run:
                    with transaction.atomic():
                        username = f'lead_{phone_normalized}'
                        user = User.objects.filter(
                            Q(phone_number=phone_normalized) | Q(username=username)
                        ).first()
                        
                        if user:
                            # Update existing user
                            if not user.phone_number:
                                user.phone_number = phone_normalized
                            if user.user_type not in [User.UserType.WALI, User.UserType.DONATUR]:
                                user.user_type = User.UserType.LEAD
                            user.is_lead = True
                            user.lead_id = lead.id
                            if not user.tenant:
                                user.tenant = lead.tenant
                            user.save()
                            stats['lead_updated'] += 1
                            self.stdout.write(f'  Updated: {lead.name} ({phone_normalized})')
                        else:
                            user = User.objects.create(
                                username=username,
                                phone_number=phone_normalized,
                                user_type=User.UserType.LEAD,
                                is_lead=True,
                                lead_id=lead.id,
                                tenant=lead.tenant,
                                is_staff=False,
                                is_active=True
                            )
                            stats['lead_created'] += 1
                            self.stdout.write(self.style.SUCCESS(f'  Created: {lead.name} ({phone_normalized})'))
                else:
                    self.stdout.write(f'  [DRY RUN] Would process: {lead.name} ({phone_normalized})')
                    stats['lead_created'] += 1
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {lead.name} - {str(e)}'))
                stats['lead_skipped'] += 1
        
        # Print summary
        self.stdout.write(self.style.SUCCESS('\n=== Migration Summary ==='))
        self.stdout.write(f'Santri: {stats["santri_created"]} created, {stats["santri_updated"]} updated, {stats["santri_skipped"]} skipped')
        self.stdout.write(f'Donatur: {stats["donatur_created"]} created, {stats["donatur_updated"]} updated, {stats["donatur_skipped"]} skipped')
        self.stdout.write(f'Lead: {stats["lead_created"]} created, {stats["lead_updated"]} updated, {stats["lead_skipped"]} skipped')
        
        total_created = stats['santri_created'] + stats['donatur_created'] + stats['lead_created']
        total_updated = stats['santri_updated'] + stats['donatur_updated'] + stats['lead_updated']
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal: {total_created} users created, {total_updated} users updated'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN COMPLETE - No changes were made'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes'))
