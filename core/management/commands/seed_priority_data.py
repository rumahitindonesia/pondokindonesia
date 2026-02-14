from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Lead, AIKnowledgeBase
from tenants.models import Tenant
from crm.models import Santri, Donatur, Tagihan, Program
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Seeds dummy data for dashboard priority testing'

    def handle(self, *args, **options):
        # 1. Get or Create Test Tenant
        tenant, _ = Tenant.objects.get_or_create(
            subdomain='rumah-it',
            defaults={'name': 'Rumah IT Indonesia', 'is_active': True}
        )
        self.stdout.write(f"Seeding for Tenant: {tenant.name}")

        # 2. Seed Programs
        spp_program, _ = Program.objects.get_or_create(
            tenant=tenant,
            nama_program='SPP Reguler',
            jenis='TAGIHAN',
            defaults={'nominal_standar': 250000}
        )
        tahfidz_program, _ = Program.objects.get_or_create(
            tenant=tenant,
            nama_program='SPP Tahfidz',
            jenis='TAGIHAN',
            defaults={'nominal_standar': 500000}
        )
        donasi_program, _ = Program.objects.get_or_create(
            tenant=tenant,
            nama_program='Infaq Pembangunan',
            jenis='DONASI',
            defaults={'nominal_standar': 100000}
        )

        # 3. Seed Leads with AI Analysis
        lead_names = ['Budi Santoso', 'Siti Aminah', 'Ahmad Fauzi', 'Laras Putri', 'Dedi Wijaya']
        interest_levels = ['Hot', 'Warm', 'Cold']
        
        for name in lead_names:
            interest = random.choice(interest_levels)
            Lead.objects.get_or_create(
                tenant=tenant,
                name=name,
                phone_number=f'+6281234567{random.randint(10,99)}',
                defaults={
                    'type': 'SANTRI',
                    'status': 'FOLLOW_UP',
                    'ai_analysis': {
                        'interest_level': interest,
                        'summary': f'Calon santri sangat tertarik dengan program {interest}.',
                        'recommendation': 'Segera hubungi untuk pendaftaran ulang.'
                    }
                }
            )
        self.stdout.write("Seeded 5 Priority Leads.")

        # 4. Seed Santri & Overdue Tagihan
        santri_list = [
            ('Hasan Al-Banna', '2024001'),
            ('Zaid bin Haritsah', '2024002'),
            ('Usamah bin Zaid', '2024003')
        ]
        
        for i, (name, nis) in enumerate(santri_list):
            santri, _ = Santri.objects.get_or_create(
                tenant=tenant,
                nis=nis,
                defaults={
                    'nama_lengkap': name,
                    'nama_wali': f'Wali {name}',
                    'no_hp_wali': f'+62899887766{random.randint(0,9)}',
                    'status': 'AKTIF'
                }
            )
            # Create Unpaid Tagihan with different programs
            prog = spp_program if i % 2 == 0 else tahfidz_program
            Tagihan.objects.get_or_create(
                tenant=tenant,
                santri=santri,
                program=prog,
                bulan='Februari 2024',
                defaults={
                    'nominal': prog.nominal_standar,
                    'status': 'BELUM',
                    'tgl_buat': timezone.now() - timedelta(days=random.randint(5, 20))
                }
            )
        self.stdout.write("Seeded 3 Overdue Tagihan.")

        # 5. Seed Donatur
        donors = ['H. Sulaiman', 'Ibu Fatimah', 'Bp. Ridwan']
        for name in donors:
            Donatur.objects.get_or_create(
                tenant=tenant,
                nama_donatur=name,
                defaults={
                    'no_hp': f'+62811223344{random.randint(0,9)}',
                    'kategori': 'TETAP' if name == 'H. Sulaiman' else 'INSIDENTIL'
                }
            )
        self.stdout.write("Seeded 3 Potential Donatur.")

        self.stdout.write(self.style.SUCCESS("Successfully seeded dummy data!"))
