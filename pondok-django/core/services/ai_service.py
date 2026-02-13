import requests
import logging
import json
from core.models import APISetting

logger = logging.getLogger(__name__)

class AIProvider:
    """Base class for AI Providers"""
    def get_completion(self, api_key, system_prompt, user_message, **kwargs):
        raise NotImplementedError

class GroqProvider(AIProvider):
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "llama-3.1-8b-instant"

    def get_completion(self, api_key, system_prompt, user_message, **kwargs):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "model": self.DEFAULT_MODEL,
            "temperature": 0.7
        }
        response = requests.post(self.API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

class OpenAIProvider(AIProvider):
    API_URL = "https://api.openai.com/v1/chat/completions"
    DEFAULT_MODEL = "gpt-4o-mini"

    def get_completion(self, api_key, system_prompt, user_message, **kwargs):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "model": self.DEFAULT_MODEL,
            "temperature": 0.7
        }
        response = requests.post(self.API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

class GeminiProvider(AIProvider):
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"

    def get_completion(self, api_key, system_prompt, user_message, **kwargs):
        headers = {"Content-Type": "application/json"}
        # Gemini params are in URL ?key=API_KEY
        url = f"{self.API_URL}?key={api_key}"
        
        # Combine system prompt and user message for Gemini (or use system_instruction if available)
        # Simple approach: Context in prompt
        full_prompt = f"System: {system_prompt}\n\nUser: {user_message}"
        
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }]
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']

class AIService:
    PROVIDERS = {
        'GROQ': GroqProvider,
        'OPENAI': OpenAIProvider,
        'GEMINI': GeminiProvider
    }
    
    @staticmethod
    def get_setting(key_name, tenant=None):
        # Tenant specific
        if tenant:
            setting = APISetting.objects.filter(
                key_name=key_name,
                category=APISetting.Category.AI,
                is_active=True,
                tenant=tenant
            ).first()
            if setting: return setting.value
            
        # Global fallback
        setting = APISetting.global_objects.filter(
            key_name=key_name,
            category=APISetting.Category.AI,
            is_active=True,
            tenant__isnull=True
        ).first()
        return setting.value if setting else None

    @classmethod
    def get_system_prompt(cls, tenant=None):
        default_prompt = "You are a helpful assistant for Pondok Pesantren. Answer briefly and politely."
        base_prompt = cls.get_setting('AI_SYSTEM_PROMPT', tenant) or default_prompt
        
        # Append Knowledge Base (Same logic as before)
        from core.models import AIKnowledgeBase
        from django.db.models import Q
        
        kb_items = AIKnowledgeBase.objects.filter(is_active=True)
        if tenant:
             kb_items = kb_items.filter(Q(tenant=tenant) | Q(tenant__isnull=True))
        else:
             kb_items = kb_items.filter(tenant__isnull=True)
             
        if kb_items.exists():
            kb_text = "\n\n=== KNOWLEDGE BASE (Use this to answer) ===\n"
            for item in kb_items:
                kb_text += f"Topic: {item.topic}\n{item.content}\n\n"
            return base_prompt + kb_text
            
        return base_prompt

    @classmethod
    def get_completion(cls, message, tenant=None, sender_name=None, system_prompt=None):
        """
        Get chat completion using configured provider.
        """
        # 1. Determine Provider
        provider_name = cls.get_setting('AI_PROVIDER', tenant)
        if not provider_name:
            provider_name = 'GROQ' # Default
        
        provider_name = provider_name.upper()
        ProviderClass = cls.PROVIDERS.get(provider_name, GroqProvider)
        
        # 2. Get API Key for that provider
        api_key_name = f"{provider_name}_API_KEY"
        api_key = cls.get_setting(api_key_name, tenant)
        
        if not api_key:
            logger.warning(f"{provider_name} API Key not found ({api_key_name}).")
            return None

        # 3. Prepare Prompt
        if not system_prompt:
             system_prompt = cls.get_system_prompt(tenant)
        
        user_content = message
        if sender_name:
            user_content = f"User Name: {sender_name}\nMessage: {message}"

        # 4. Execute
        try:
            provider = ProviderClass()
            return provider.get_completion(api_key, system_prompt, user_content)
        except Exception as e:
            logger.error(f"AI Service Error ({provider_name}): {str(e)}")
            return None
