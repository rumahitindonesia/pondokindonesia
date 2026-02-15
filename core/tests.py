from django.test import TestCase, Client
from django.urls import reverse
from tenants.models import Tenant
from users.models import User, Role
from core.models import WhatsAppForm, Lead, WhatsAppMessage
import json

class WhatsAppWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create Tenant
        self.tenant = Tenant.objects.create(name="Pondok IT", subdomain="pondok-it")
        
        # Create Staff User
        self.staff_user = User.objects.create(
            username="admin_staff",
            is_staff=True,
            phone_number="628123456789",
            tenant=self.tenant
        )
        
        # Create CS Role and User for auto-assignment
        self.cs_role = Role.objects.create(name="CS", slug="cs", tenant=self.tenant)
        self.cs_user = User.objects.create(
            username="cs_user",
            phone_number="628999888777",
            role=self.cs_role,
            tenant=self.tenant,
            is_active=True
        )

        # Create WhatsApp Form
        self.wa_form = WhatsAppForm.objects.create(
            tenant=self.tenant,
            keyword="DAFTAR",
            separator="#",
            field_map="nama#kota#sekolah",
            lead_type=Lead.Type.SANTRI,
            response_template="Terima kasih {name} dari {kota}.",
            is_active=True
        )

    def test_external_form_registration(self):
        """Test external message matching a WhatsAppForm."""
        url = reverse('core:webhook_whatsapp_tenant', kwargs={'tenant_slug': 'pondok-it'})
        payload = {
            "device": "device1",
            "message": "DAFTAR#Ahmad#Jakarta#SMP 1",
            "from": "628111222333",
            "push_name": "Ahmad User"
        }
        
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Verify Lead creation
        lead = Lead.objects.get(phone_number="628111222333", tenant=self.tenant)
        self.assertEqual(lead.name, "Ahmad")
        self.assertEqual(lead.data['kota'], "Jakarta")
        self.assertEqual(lead.type, Lead.Type.SANTRI)
        self.assertEqual(lead.status, Lead.Status.NEW)
        
        # Verify CS Assignment
        self.assertEqual(lead.cs, self.cs_user)

    def test_internal_staff_command(self):
        """Test internal message from a staff number."""
        url = reverse('core:webhook_whatsapp_tenant', kwargs={'tenant_slug': 'pondok-it'})
        # Use staff phone number
        payload = {
            "device": "device1",
            "message": "LEAD/Budi#628555444333#Minat program IT",
            "from": "628123456789",
            "push_name": "Admin"
        }
        
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Verify Lead creation by staff
        lead = Lead.objects.get(phone_number="628555444333", tenant=self.tenant)
        self.assertEqual(lead.name, "Budi")
        self.assertEqual(lead.cs, self.staff_user) # Created by staff
        self.assertEqual(lead.notes, "Minat program IT")

    def test_staff_search_command(self):
        """Test staff CARI command."""
        from crm.models import Santri
        Santri.objects.create(
            tenant=self.tenant,
            nis="NIS-001",
            nama_lengkap="Ahmad Santri",
            nama_wali="Wali Ahmad",
            no_hp_wali="628111222333"
        )
        
        url = reverse('core:webhook_whatsapp_tenant', kwargs={'tenant_slug': 'pondok-it'})
        payload = {
            "device": "device1",
            "message": "CARI Ahmad",
            "from": "628123456789",
            "push_name": "Admin"
        }
        
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        # We can't easily assert the WA message sent unless we mock StarSenderService.
        # But we can verify the view returns OK.

    def test_external_ai_fallback_lead_creation(self):
        """Test that unknown external message still creates a waiting lead."""
        url = reverse('core:webhook_whatsapp_tenant', kwargs={'tenant_slug': 'pondok-it'})
        payload = {
            "device": "device1",
            "message": "Halo, saya mau tanya biaya.",
            "from": "628999000111",
            "push_name": "Tanya User"
        }
        
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Verify Lead creation in WAITING_DATA status
        lead = Lead.objects.get(phone_number="628999000111", tenant=self.tenant)
        self.assertEqual(lead.status, Lead.Status.WAITING_DATA)
