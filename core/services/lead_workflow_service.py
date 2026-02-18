from django.db.models import Count, Q
from core.models import Lead
from users.models import User, Role
from core.services.starsender import StarSenderService

class LeadWorkflowService:
    @staticmethod
    def assign_to_cs(lead):
        """
        Assign lead to a CS based on load balancing (fewest NEW leads).
        """
        tenant = lead.tenant
        if not tenant:
            return None
        
        # 1. Find CS users for this tenant based on lead type
        role_slug = 'cs' # Fallback
        if lead.type == Lead.Type.DONATUR:
            role_slug = 'cs-donasi'
        elif lead.type == Lead.Type.SANTRI:
            role_slug = 'cs-pendaftaran'
            
        cs_role = Role.objects.filter(tenant=tenant, slug=role_slug).first()
        if not cs_role:
            # Fallback to generic 'cs' if specific doesn't exist
            cs_role = Role.objects.filter(tenant=tenant, slug='cs').first()
        
        if not cs_role:
            # Global fallback
            cs_role = Role.objects.filter(tenant__isnull=True, slug=role_slug).first() or \
                      Role.objects.filter(tenant__isnull=True, slug='cs').first()
        
        if not cs_role:
            return None
            
        # 2. Get active CS users
        eligible_cs = User.all_objects.filter(
            tenant=tenant,
            role=cs_role,
            is_active=True
        ).annotate(
            new_lead_count=Count('assigned_leads', filter=Q(assigned_leads__status=Lead.Status.NEW))
        ).order_by('new_lead_count', 'id')
        
        assigned_cs = eligible_cs.first()
        
        if assigned_cs:
            lead.cs = assigned_cs
            # Ensure status is NEW if for some reason it wasn't
            if lead.status == Lead.Status.WAITING_DATA:
                lead.status = Lead.Status.NEW
            lead.save()
            
            # 3. Notify CS via WA
            LeadWorkflowService.notify_cs_of_assignment(lead)
            
        return assigned_cs

    @staticmethod
    def notify_cs_of_assignment(lead):
        """
        Send WA notification to assigned CS with Click-to-Chat link.
        """
        if not lead.cs or not lead.cs.phone_number:
            return
            
        import re
        import urllib.parse
        
        # Parse data from lead.data
        name = lead.name or "Unknown"
        kota = lead.data.get('kota', '-')
        sekolah = lead.data.get('sekolah', lead.data.get('asalsekolah', '-'))
        phone = lead.phone_number
        
        # Format phone for wa.me (remove +, leading 0 -> 62)
        wa_phone = re.sub(r'\D', '', str(phone))
        if wa_phone.startswith('0'):
            wa_phone = '62' + wa_phone[1:]
        elif not wa_phone.startswith('62') and len(wa_phone) > 8:
            # Assume local number if not starting with 62 or 0
            wa_phone = '62' + wa_phone

        cs_name = lead.cs.get_full_name() or lead.cs.username
        
        # Pre-filled message for CS to send from their own number
        template = f"Halo Kak {name}, saya {cs_name} dari Pesantren. Menindaklanjuti pendaftaran Kakak, ada yang bisa saya bantu?"
        encoded_text = urllib.parse.quote(template)
        wa_link = f"https://wa.me/{wa_phone}?text={encoded_text}"
        
        body = (
            f"🔔 *Lead Baru Terdeteksi!*\n\n"
            f"📍 *Data Lead:*\n"
            f"Nama: {name}\n"
            f"Asal: {kota}\n"
            f"Sekolah: {sekolah}\n"
            f"Phone: {phone}\n\n"
            f"🚀 *Satu Klik untuk Follow Up:*\n"
            f"{wa_link}\n\n"
            f"Silakan klik link di atas untuk langsung chat lead dari nomor pribadi Anda."
        )
        
        StarSenderService.send_message(
            to=lead.cs.phone_number,
            body=body,
            tenant=lead.tenant
        )

    @staticmethod
    def parse_data_format(lead, message):
        """
        Attempt to parse nama#kota#asalsekolah format.
        """
        parts = [p.strip() for p in message.split('#')]
        if len(parts) >= 3:
            # Match
            data = {
                'nama': parts[0],
                'kota': parts[1],
                'sekolah': parts[2]
            }
            lead.name = parts[0]
            lead.data.update(data)
            lead.save()
            return True
        return False
