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
        
        # 1. Find CS users for this tenant
        # Assuming CS role has slug 'cs'
        cs_role = Role.objects.filter(tenant=tenant, slug='cs').first()
        if not cs_role:
            # Fallback to global CS role if tenant specific doesn't exist? (Optional)
            cs_role = Role.objects.filter(tenant__isnull=True, slug='cs').first()
        
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
            lead.status = Lead.Status.NEW
            lead.save()
            
            # 3. Notify CS via WA
            LeadWorkflowService.notify_cs_of_assignment(lead)
            
        return assigned_cs

    @staticmethod
    def notify_cs_of_assignment(lead):
        """
        Send WA notification to assigned CS.
        Format: nama#kota#asalsekolah#no-wa-leads
        """
        if not lead.cs or not lead.cs.phone_number:
            return
            
        # Parse data from lead.data
        name = lead.name or "Noname"
        kota = lead.data.get('kota', '-')
        sekolah = lead.data.get('sekolah', lead.data.get('asalsekolah', '-'))
        phone = lead.phone_number
        
        body = f"{name}#{kota}#{sekolah}#{phone}"
        
        StarSenderService.send_message(
            to=lead.cs.phone_number,
            body=f"Lead Baru Terdeteksi!\n\n{body}\n\nSilakan segera di-follow up di Dashboard.",
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
