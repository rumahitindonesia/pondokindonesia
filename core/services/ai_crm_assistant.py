from core.services.ai_service import AIService
from core.models import AIKnowledgeBase

class AICRMAssistant:
    @staticmethod
    def _get_knowledge_context(tenant):
        if not tenant:
            return ""
        
        kbs = AIKnowledgeBase.objects.filter(tenant=tenant, is_active=True)
        if not kbs.exists():
            return ""
            
        context = ""
        for kb in kbs:
            context += f"- TOPIC: {kb.topic}\n  CONTENT: {kb.content}\n\n"
        return context

    @staticmethod
    def generate_invoice_message(tagihan):
        """
        Generates a polite invoice reminder (Tagihan SPP).
        """
        tenant = tagihan.santri.tenant
        kb_context = AICRMAssistant._get_knowledge_context(tenant)
        
        nominal = "{:,.0f}".format(tagihan.nominal).replace(',', '.')
        
        prompt = f"""
You are an admin of a Pondok Pesantren responsible for finance.
Draft a WhatsApp message to a parent (Wali Santri) reminding them about a payment.

CONTEXT:
Santri Name: {tagihan.santri.nama_lengkap}
Parent Name: {tagihan.santri.nama_wali} (Usually 'Bapak/Ibu')
Payment Type: {tagihan.program.nama_program}
Amount: Rp {nominal}
Period/Note: {tagihan.bulan if tagihan.bulan else '-'}
Tenant/Pondok: {tenant.name if tenant else 'Pondok Pesantren'}

KNOWLEDGE BASE (Bank Accounts etc):
{kb_context}

REQUIREMENTS:
1. Tone: Islamic, Polite, Soft, and Respectful. NOT demanding.
2. Structure: Salam -> Greeting -> Clear Detail of Payment -> Payment Method (from Knowledge Base if avail, else generic) -> Closing -> Signature.
3. Language: Indonesian (Bahasa Indonesia).
4. Short & Concise for WhatsApp.
5. Return ONLY the message content.

DRAFT:
"""
        return AIService.get_completion(prompt, tenant=tenant, system_prompt="You return only the message body in Indonesian.")

    @staticmethod
    def generate_solicitation_message(donatur, program_name="Program Kebaikan"):
        """
        Generates a persuasive donation solicitation (Ajakan Donasi).
        """
        tenant = donatur.tenant
        kb_context = AICRMAssistant._get_knowledge_context(tenant)
        
        prompt = f"""
You are a fundraising officer for a Pondok Pesantren.
Draft a persuasive WhatsApp message to a donor inviting them to participate in a program.

CONTEXT:
Donor Name: {donatur.nama_donatur}
Program: {program_name} (e.g. Wakaf, Infaq, Zakat)
Tenant/Pondok: {tenant.name if tenant else 'Pondok Pesantren'}

KNOWLEDGE BASE (Bank Accounts etc):
{kb_context}

REQUIREMENTS:
1. Tone: Islamic, Inspiring, Warm.
2. Content: Quote a relevant Hadith/Quran verse about charity/sedekah.
3. Call to Action: Invite them to contribute to {program_name}. Use information from Knowledge Base about accounts.
4. Language: Indonesian (Bahasa Indonesia).
5. Return ONLY the message content.

DRAFT:
"""
        return AIService.get_completion(prompt, tenant=tenant, system_prompt="You return only the message body in Indonesian.")
