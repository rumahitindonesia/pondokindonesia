from core.services.ai_service import AIService
from core.models import Lead, WhatsAppMessage

class AILeadAssistant:
    @staticmethod
    def _get_knowledge_context(tenant):
        from core.models import AIKnowledgeBase
        if not tenant:
            return ""
            
        kbs = AIKnowledgeBase.objects.filter(
            tenant=tenant, 
            is_active=True
        )
        
        if not kbs.exists():
            return "(No specific knowledge base found)"
            
        context = ""
        for kb in kbs:
            context += f"- TOPIC: {kb.topic}\n  CONTENT: {kb.content}\n\n"
        return context

    @staticmethod
    def analyze_lead(lead: Lead):
        """
        Analyzes a lead based on profile and chat history.
        Returns a dict with: interest_level, summary, recommendation.
        """
        # 1. Gather Context
        messages = WhatsAppMessage.objects.filter(
            tenant=lead.tenant if lead.tenant else None,
            sender=lead.phone_number
        ).order_by('-created_at')[:20]
        
        history_text = ""
        for msg in reversed(messages): # Chronological order
            sender = "User" if msg.sender == lead.phone_number else "System"
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
            history_text += f"[{timestamp}] {sender}: {msg.message}\n"
            
        if not history_text:
            history_text = "(No chat history available)"

        # 2. Get Knowledge Base
        knowledge_context = AILeadAssistant._get_knowledge_context(lead.tenant)

        # 3. Construct Prompt
        role_desc = "Sales Coach"
        goal_desc = "close this enrollment"
        if lead.type == 'DONATUR':
            role_desc = "Fundraising Advisor"
            goal_desc = "secure the donation or build a long-term donor relationship"

        prompt = f"""
You are an expert {role_desc} for a Pondok Pesantren (Islamic Boarding School).
Analyze the following lead and provide a strategic assessment.

Lead Name: {lead.name}
Type: {lead.get_type_display()}
Status: {lead.get_status_display()}
Extracted Data: {lead.data}

KNOWLEDGE BASE (FACTS ABOUT PONDOK):
{knowledge_context}

CHAT HISTORY:
{history_text}

TASK:
1. Determine Interest Level (Hot, Warm, Cold).
2. Summarize the lead's situation, needs, and concerns.
3. Recommend the next best action for the admin to {goal_desc}.
   - Refer to KNOWLEDGE BASE if the lead asked specific questions (e.g. price, curriculum).
4. Identify MISSING KNOWLEDGE:
   - List any specific questions the lead asked that are NOT answered by the current KNOWLEDGE BASE.
   - If none, leave empty.

IMPORTANT: OUTPUT MUST BE IN INDONESIAN (BAHASA INDONESIA).

OUTPUT FORMAT (Return strictly JSON):
{{
  "interest_level": "Hot/Warm/Cold",
  "summary": "Ringkasan situasi lead...",
  "recommendation": "Saran tindakan...",
  "missing_knowlege": "Pertanyaan lead yang belum ada di knowledge base (jika ada)..."
}}
"""
        # 4. Call AI
        response = AIService.get_completion(prompt, tenant=lead.tenant, system_prompt="You are a helpful AI assistant that outputs strictly JSON in Indonesian.")
        
        # 5. Parse JSON
        import json
        import re
        
        try:
            # Cleanup Markdown code blocks if present
            cleaned = re.sub(r'```json', '', response)
            cleaned = re.sub(r'```', '', cleaned).strip()
            data = json.loads(cleaned)
            
            # Save to Lead
            lead.ai_analysis = data
            lead.save(update_fields=['ai_analysis'])
            
            return data
        except Exception as e:
            return {
                "interest_level": "Unknown",
                "summary": "Failed to parse AI response.",
                "recommendation": "Check logs.",
                "raw_response": response
            }

    @staticmethod
    def generate_followup(lead: Lead, instruction: str = None, user=None):
        """
        Generates a follow-up message draft.
        """
        # Ensure analysis exists
        if not lead.ai_analysis:
            AILeadAssistant.analyze_lead(lead)
            lead.refresh_from_db()
            
        analysis = lead.ai_analysis
        
        # Determine Sender Name (CS) and Pondok Name
        sender_name = "Admin"
        if user and user.first_name:
            sender_name = user.first_name
        elif user and user.username:
            sender_name = user.username
            
        pondok_name = lead.tenant.name if lead.tenant else "Pondok Pesantren"
        
        # Type-specific Context
        role = "Sales Copywriter"
        objective = "enrollment"
        if lead.type == 'DONATUR':
            role = "Fundraising Copywriter"
            objective = "donation/relationship"
        
        # Get Knowledge Base
        knowledge_context = AILeadAssistant._get_knowledge_context(lead.tenant)

        prompt = f"""
You are an expert {role}.
Draft a WhatsApp follow-up message for this lead working for specific Pondok Pesantren.

Lead Name: {lead.name}
Type: {lead.get_type_display()}
Interest Level: {analysis.get('interest_level')}
Coach's Recommendation: {instruction if instruction else analysis.get('recommendation')}

KNOWLEDGE BASE (FACTS ABOUT PONDOK):
{knowledge_context}

SENDER INFO:
Name: {sender_name} (CS/Admin)
Institution: {pondok_name}

REQUIREMENTS:
1. Friendly, Islamic, and Professional tone.
2. Short and concise (WhatsApp style).
3. Focus on {objective} or advancing to the next step.
4. USE KNOWLEDGE BASE to answer specific questions if applicable (e.g. fees, location).
5. Return ONLY the message content. No "Subject:" or "Here is the draft:".
6. LANGUAGE: INDONESIAN (BAHASA INDONESIA).
7. SIGNATURE: Must end with "{sender_name} - {pondok_name}".

DRAFT:
"""
        response = AIService.get_completion(prompt, tenant=lead.tenant, system_prompt="You return only the message body in Indonesian.")
        
        # Save Draft
        if response:
            lead.last_draft = response.strip()
            lead.save(update_fields=['last_draft'])
            
        return response
