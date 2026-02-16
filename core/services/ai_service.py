import requests
import logging
import json
from core.models import APISetting

logger = logging.getLogger(__name__)

class AIProvider:
    """Base class for AI Providers"""
    def get_completion(self, api_key, messages, **kwargs):
        raise NotImplementedError

class GroqProvider(AIProvider):
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "llama-3.1-8b-instant"

    def get_completion(self, api_key, messages, **kwargs):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": messages,
            "model": self.DEFAULT_MODEL,
            "temperature": 0.7
        }
        response = requests.post(self.API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

class OpenAIProvider(AIProvider):
    API_URL = "https://api.openai.com/v1/chat/completions"
    DEFAULT_MODEL = "gpt-4o-mini"

    def get_completion(self, api_key, messages, **kwargs):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": messages,
            "model": self.DEFAULT_MODEL,
            "temperature": 0.7
        }
        response = requests.post(self.API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

class GeminiProvider(AIProvider):
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"

    def get_completion(self, api_key, messages, **kwargs):
        headers = {"Content-Type": "application/json"}
        url = f"{self.API_URL}?key={api_key}"
        
        # Convert OpenAI-style messages to Gemini format
        gemini_contents = []
        for msg in messages:
            role = "user" if msg['role'] in ['user', 'system'] else "model"
            content = msg['content']
            if msg['role'] == 'system':
                 content = f"Instruction: {content}"
            
            gemini_contents.append({
                "role": role,
                "parts": [{"text": content}]
            })
        
        payload = {
            "contents": gemini_contents
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']

class EmbeddingProvider:
    """Base class for Embedding Providers"""
    def get_embedding(self, api_key, text):
        raise NotImplementedError

class OpenAIEmbeddingProvider(EmbeddingProvider):
    API_URL = "https://api.openai.com/v1/embeddings"
    DEFAULT_MODEL = "text-embedding-3-small"

    def get_embedding(self, api_key, text):
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"input": text, "model": self.DEFAULT_MODEL}
        response = requests.post(self.API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['data'][0]['embedding']

class GeminiEmbeddingProvider(EmbeddingProvider):
    # Verified model name from ListModels: models/gemini-embedding-001
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"

    def get_embedding(self, api_key, text):
        url = f"{self.API_URL}?key={api_key}"
        payload = {"content": {"parts": [{"text": text}]}}
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Gemini Embedding Error Details: {response.text}")
            response.raise_for_status()
                
        return response.json()['embedding']['values']

class AIService:
    PROVIDERS = {
        'GROQ': GroqProvider,
        'OPENAI': OpenAIProvider,
        'GEMINI': GeminiProvider
    }
    
    EMBEDDING_PROVIDERS = {
        'OPENAI': OpenAIEmbeddingProvider,
        'GEMINI': GeminiEmbeddingProvider,
        'GROQ': OpenAIEmbeddingProvider # Fallback Groq to OpenAI/Gemini as Groq lacks embeddings
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
    def generate_embedding(cls, text, tenant=None):
        provider_name = (cls.get_setting('AI_PROVIDER', tenant) or 'GEMINI').upper()
        # Ensure we have a provider that supports embeddings
        if provider_name == 'GROQ':
             provider_name = 'GEMINI' if cls.get_setting('GEMINI_API_KEY', tenant) else 'OPENAI'
             
        ProviderClass = cls.EMBEDDING_PROVIDERS.get(provider_name, GeminiEmbeddingProvider)
        api_key = cls.get_setting(f"{provider_name}_API_KEY", tenant)
        
        if not api_key: return None
        try:
            return ProviderClass().get_embedding(api_key, text)
        except Exception as e:
            logger.error(f"Embedding Error ({provider_name}): {str(e)}")
            return None

    @classmethod
    def find_relevant_knowledge(cls, query, tenant=None, top_k=3):
        from core.models import AIKnowledgeBase
        from django.db.models import Q
        import math

        query_vector = cls.generate_embedding(query, tenant)
        if not query_vector:
            return ""

        kb_items = AIKnowledgeBase.objects.filter(is_active=True, embedding__isnull=False)
        if tenant:
             kb_items = kb_items.filter(Q(tenant=tenant) | Q(tenant__isnull=True))
        else:
             kb_items = kb_items.filter(tenant__isnull=True)
        
        if not kb_items.exists(): return ""

        def cosine_similarity(v1, v2):
            dot_product = sum(a * b for a, b in zip(v1, v2))
            magnitude = math.sqrt(sum(a * a for a in v1)) * math.sqrt(sum(b * b for b in v2))
            return dot_product / magnitude if magnitude > 0 else 0

        scored_items = []
        for item in kb_items:
            score = cosine_similarity(query_vector, item.embedding)
            if score > 0.4: # Minimal threshold
                scored_items.append((score, item))
        
        scored_items.sort(key=lambda x: x[0], reverse=True)
        
        context = "\n\n=== RELEVANT KNOWLEDGE ===\n"
        for score, item in scored_items[:top_k]:
            context += f"Topic: {item.topic}\n{item.content}\n\n"
        
        return context

    @classmethod
    def get_system_prompt(cls, tenant=None, query=None):
        default_prompt = (
            "You are Yasmin, a friendly Admin Virtual of a Pondok Pesantren. "
            "Your task is to help potential registrants (leads) and parents. "
            "MANDATORY: Check the conversation history. If you have already greeted the user or given a salam, "
            "DO NOT repeat the full greeting/salam unless the conversation just started after a long break. "
            "Keep the flow natural, informative and persuasive for closing/registration."
        )
        base_prompt = cls.get_setting('AI_SYSTEM_PROMPT', tenant) or default_prompt
        
        # If no query, we can't do RAG, return base prompt
        if not query:
             return base_prompt

        # Use Semantic Search
        relevant_context = cls.find_relevant_knowledge(query, tenant)
        return base_prompt + relevant_context

    @classmethod
    def get_history_context(cls, phone_number):
        if not phone_number:
            return []
        
        from core.models import WhatsAppMessage
        from django.db.models import Q
        import re
        
        def clean_num(n): return re.sub(r'\D', '', str(n)) if n else ""
        c_phone = clean_num(phone_number)
        
        # Get last 15 messages for context
        history = WhatsAppMessage.objects.filter(
            Q(sender=c_phone) | Q(recipient=c_phone)
        ).order_by('-created_at')[:15]
        
        msgs = list(reversed(history))
        formatted = []
        for h in msgs:
            role = "assistant" if h.is_outbound else "user"
            formatted.append({"role": role, "content": h.message})
        return formatted

    @classmethod
    def get_completion(cls, message, tenant=None, sender_name=None, system_prompt=None, sender_phone=None):
        """
        Get chat completion using configured provider with history support.
        """
        provider_name = (cls.get_setting('AI_PROVIDER', tenant) or 'GROQ').upper()
        ProviderClass = cls.PROVIDERS.get(provider_name, GroqProvider)
        
        api_key = cls.get_setting(f"{provider_name}_API_KEY", tenant)
        if not api_key:
            logger.warning(f"{provider_name} API Key not found.")
            return None

        # 3. Construct Messages List
        messages = []
        if not system_prompt:
             system_prompt = cls.get_system_prompt(tenant, query=message)
        messages.append({"role": "system", "content": system_prompt})
        
        # Fetch Memory
        if sender_phone:
            history = cls.get_history_context(sender_phone)
            for h in history:
                messages.append(h)
        
        # Add Current User Message
        user_content = f"User: {message}"
        if sender_name:
            user_content = f"Name: {sender_name}\nMessage: {message}"
        
        # Avoid duplicating the last history message if it's already there (rare race condition)
        if not messages or messages[-1]['content'] != user_content:
            messages.append({"role": "user", "content": user_content})

        # 4. Execute
        try:
            provider = ProviderClass()
            return provider.get_completion(api_key, messages)
        except Exception as e:
            logger.error(f"AI Service Error ({provider_name}): {str(e)}")
            return None
