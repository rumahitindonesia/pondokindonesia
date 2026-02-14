from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Lead
from core.services.starsender import StarSenderService
from core.services.ai_service import AIService

class Command(BaseCommand):
    help = 'Process automated follow-ups for leads'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # FU Sequence: After 1h, 8h, 24h, 48h, 72h (approx)
        # We simplify it by checking delay since last message or last FU
        FU_DELAY_MAP = {
            1: timedelta(hours=1),      # 1st FU after 1 hour of silence
            2: timedelta(hours=8),      # 2nd FU after 8 hours from 1st FU
            3: timedelta(days=1),       # 3rd FU after 1 day from 2nd FU
            4: timedelta(days=1),       # 4th FU after 1 day from 3rd FU
            5: timedelta(days=1),       # 5th FU after 1 day from 4th FU
        }

        # Find leads in WAITING_DATA or NEW status that need follow-up
        leads = Lead.objects.filter(
            status__in=[Lead.Status.WAITING_DATA, Lead.Status.NEW]
        ).exclude(status=Lead.Status.REJECTED)

        self.stdout.write(f"Checking {leads.count()} leads for AFU...")

        for lead in leads:
            afu_idx = lead.afu_count + 1
            if afu_idx > 5:
                # Max exceeded, set to Lost
                lead.status = Lead.Status.REJECTED
                lead.notes = (lead.notes or "") + f"\n[AFU] Auto-cancelled after 5 unsuccessful follow-ups."
                lead.save()
                self.stdout.write(f"Lead {lead.phone_number} reached max AFU. Status -> REJECTED")
                continue

            delay = FU_DELAY_MAP.get(afu_idx)
            last_activity = lead.last_afu_at or lead.last_message_at or lead.created_at
            
            if now >= last_activity + delay:
                # Trigger Follow-up
                self.send_followup(lead, afu_idx)
                
                lead.afu_count = afu_idx
                lead.last_afu_at = now
                lead.save()
                self.stdout.write(f"Sent FU #{afu_idx} to {lead.phone_number}")

    def send_followup(self, lead, count):
        """
        Send a polite follow-up message via AI.
        """
        context = ""
        if lead.status == Lead.Status.WAITING_DATA:
            context = "Lead belum memberikan data format (nama#kota#asalsekolah)."
        else:
            context = "Lead sudah memberikan data tapi belum merespon CS."

        prompt = (
            f"Kirimkan pesan follow-up ke-{count} yang sangat ramah dan sopan kepada calon pendaftar. "
            f"Konteks: {context} "
            f"Tujuan: Mengingatkan mereka untuk melanjutkan proses pendaftaran di Pondok Indonesia. "
            f"Jangan terkesan memaksa, berikan bantuan jika mereka ada kesulitan. "
            f"Gunakan bahasa Indonesia yang santun. "
            f"IMPORTANT: Kembalikan HANYA konten pesan."
        )

        try:
            ai_message = AIService.get_completion(prompt, tenant=lead.tenant)
            if ai_message:
                StarSenderService.send_message(
                    to=lead.phone_number,
                    body=ai_message,
                    tenant=lead.tenant
                )
        except Exception as e:
            self.stderr.write(f"Error sending AFU to {lead.phone_number}: {e}")
