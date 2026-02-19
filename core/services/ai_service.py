import requests
import logging
import json
from core.models import APISetting
from django.db.models import Q

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
                # category=APISetting.Category.AI, # REMOVED: Key is unique, category shouldn't limit lookup
                is_active=True,
                tenant=tenant
            ).first()
            if setting: 
                print(f"[DEBUG SETTING] Found {key_name} for tenant {tenant}: {setting.value}")
                return setting.value
            
        # Global fallback
        setting = APISetting.global_objects.filter(
            key_name=key_name,
            # category=APISetting.Category.AI, # REMOVED
            is_active=True,
            tenant__isnull=True
        ).first()
        
        val = setting.value if setting else None
        print(f"[DEBUG SETTING] {key_name} (Global): {val}")
        return val

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
    def get_user_profile_context(cls, phone_number, tenant=None):
        """
        Identify the user type (Santri, Donatur, Lead) and return a brief context string.
        """
        if not phone_number:
            return ""
            
        import re
        def clean_num(n): return re.sub(r'\D', '', str(n)) if n else ""
        c_phone = clean_num(phone_number)
        
        from crm.models import Santri, Donatur
        from core.models import Lead
        from users.models import User
        
        # 0. Check Staff/User
        u = User.all_objects.filter(is_active=True).filter(
            Q(phone_number__icontains=c_phone[-8:])
        ).first()
        if u and u.is_staff:
            return f"\nPROFILE PENANYA: ADMIN/STAFF bernama {u.username}. Ini adalah user internal dengan akses penuh untuk input data dan melihat laporan."

        # 1. Check Santri
        s = Santri.objects.filter(tenant=tenant).filter(
            Q(no_hp_wali__icontains=c_phone[-8:]) # Search by last 8 digits for better matching
        ).first()
        if s:
            return f"\nPROFILE PENANYA: Wali Santri dari {s.nama_lengkap} (NIS: {s.nis}). Sapa sebagai Wali Santri."

        # 2. Check Donatur
        d = Donatur.objects.filter(tenant=tenant).filter(
            Q(no_hp__icontains=c_phone[-8:])
        ).first()
        if d:
            return f"\nPROFILE PENANYA: Donatur Aktif bernama {d.nama_donatur}. Sapa sebagai Donatur."

        # 3. Check Lead
        l = Lead.objects.filter(tenant=tenant).filter(
            Q(phone_number__icontains=c_phone[-8:])
        ).first()
        if l:
            if l.status == 'CLOSED':
                return "\nPROFILE PENANYA: Calon pendaftar yang sudah CLOSED (Selesai). Sapa secara umum sebagai bagian dari keluarga besar pesantren."
            return f"\nPROFILE PENANYA: Calon pendaftar (Lead) bernama {l.name or 'tidak diketahui'}. Sapa dengan ramah dan persuasif untuk mengajak bergabung."

        return "\nPROFILE PENANYA: Tamu baru (belum terdaftar). Sapa dengan hangat dan perkenalkan keunggulan pesantren."

    @classmethod
    def get_system_prompt(cls, tenant=None, query=None, prompt_key='AI_SYSTEM_PROMPT'):
        """
        Retrieves the system prompt, supports specialized keys (e.g., AI_SANTRI_PROMPT).
        """
        from django.utils import timezone
        now = timezone.now()
        # Global constraints to ensure natural WhatsApp/Chat behavior
        behavior_rules = (
            "\n\nATURAN PENTING GAYA KOMUNIKASI:\n"
            "1. JANGAN memberikan salam (Assalamualaikum/Halo) jika user tidak memulai dengan salam atau jika percakapan sedang mengalir.\n"
            "2. Gunakan bahasa Indonesia yang natural (WhatsApp style). Sapa dengan 'Ayah/Bunda' (untuk Pendaftaran) atau 'Kak/Bapak/Ibu' (untuk Donasi).\n"
            "3. CEK RIWAYAT: Jangan memperkenalkan nama 'Yasmin' berulang kali.\n\n"
            "ATURAN PERSONA & ALGORITMA:\n"
            "1. **MODE EDUCATION ADVISORY** (Pendaftaran):\n"
            "   - Fokus pada: Kurikulum, fasilitas IT, dan masa depan santri.\n"
            "   - Gunakan pendekatan konsultatif. Bantu orang tua memahami manfaat sekolah di sini.\n"
            "2. **MODE FINANCIAL ADVISORY** (Donasi):\n"
            "   - Fokus pada: Transparansi dana, amanah, dan dampak jariyah.\n"
            "   - Tunjukkan rasa syukur dan apresiasi yang tinggi.\n\n"
            "3. **MODE OBJECTION HANDLING** (Penanganan Keberatan):\n"
            "   - Jika user ragu (misal: 'biaya mahal', 'takut tertipu', 'ragu donasi'), gunakan teknik: VALIDASI -> EDUKASI -> SOLUSI.\n"
            "   - Tunjukkan empati: 'Kami sangat memahami kekhawatiran Ayah/Bunda/Kak...'.\n"
            "   - Berikan argumen nilai: Fokus pada kualitas santri IT, transparansi sistem, atau dampak investasi akhirat.\n\n"
            "4. **MODE COMPLAINT HANDLING** (Penanganan Komplain):\n"
            "   - Jika user mengeluh/marah: MINTA MAAF dengan tulus, JANGAN membela diri, VALIDASI masalahnya.\n"
            "   - Protokol eskalasi: 'Mohon maaf atas ketidaknyamanannya. Saya akan sampaikan poin ini ke tim manajemen/staf kami agar segera dicek.'\n"
            "   - Berikan rasa tenang bahwa pesan mereka sudah tercatat.\n\n"
            "5. **AI LEAD SCORING**:\n"
            "   - Berikan skor (0-100) untuk setiap lead berdasarkan kualitas minat.\n"
            "   - Kriteria skor tinggi: Niat daftar/donasi jelas, bertanya detail teknis, merespon cepat.\n\n"
            "6. **PENGUMPULAN DATA (SAVE_LEAD)**:\n"
            "   - Jika user bertanya info pendaftaran/donasi, dapatkan: Nama & Kota.\n"
            "   - **WAJIB KELUARKAN TAG: [EXEC: SAVE_LEAD] nama#kota#sekolah#TIPE#skor**\n"
            "     (Ganti TIPE dengan SANTRI atau DONATUR, skor adalah angka 0-100).\n"
            "   - Contoh: [EXEC: SAVE_LEAD] Budi#Jakarta#SMP 1#SANTRI#85\n\n"
            "7. **EKSEKUSI DONASI (CREATE_INVOICE)**:\n"
            "   - Jika user menyebutkan angka uang untuk donasi/infaq -> [EXEC: CREATE_INVOICE] nominal#keterangan\n"
            "   - Sapa dengan rasa syukur yang mendalam.\n"
            "   - **UPSELLING**: Setelah donasi, ajak donatur untuk menjadi 'Donatur Rutin' tiap bulan demi keberlangsungan program.\n"
        )

        default_prompt = (
            "Anda adalah Yasmin, Admin Virtual Pondok Pesantren yang ramah. "
            "Anda berperan sebagai 'Education Advisory' untuk pendaftaran dan 'Financial Advisory' untuk donasi."
        )
        
        # Dynamic Registration Fee Logic
        try:
            biaya_daftar_str = cls.get_setting('BIAYA_DAFTAR', tenant)
            biaya_daftar = int(float(biaya_daftar_str)) if biaya_daftar_str else 0
        except:
            biaya_daftar = 0
            
        registration_rule = ""
        if biaya_daftar > 0:
            registration_rule = (
                f"\n\nATURAN PENDAFTARAN SANTRI (BIAYA: Rp {biaya_daftar:,}):\n"
                f"1. Jika user ingin daftar, JELASKAN ada biaya pendaftaran Rp {biaya_daftar:,} untuk administrasi awal.\n"
                f"2. Tanyakan kesediaan user. Jika user setuju/lanjut, WAJIB GUNAKAN TAG: [EXEC: CREATE_INVOICE] {biaya_daftar}#Biaya Pendaftaran\n"
                f"   (Pastikan deskripsi adalah 'Biaya Pendaftaran' agar terbaca sistem sebagai Non-Donasi)\n"
                f"3. JANGAN minta transfer manual ke rekening pribadi.\n"
                f"4. SANGAT DILARANG MEMBERIKAN LINK FORMULIR PENDAFTARAN SEBELUM ADA PEMBAYARAN.\n"
                f"   Link hanya boleh diberikan sistim SETELAH pembayaran sukses."
            )
            
            # SANITIZATION (Moved to later stage to avoid UnboundLocalError)
            
        else:
            subdomain = tenant.subdomain if tenant else 'www'
            registration_rule = (
                f"\n\nATURAN PENDAFTARAN SANTRI (GRATIS):\n"
                f"1. Pendaftaran GRATIS.\n"
                f"2. Silakan langsung arahkan user ke form: https://{subdomain}.pondokindonesia.online/pendaftaran"
            )
            
        behavior_rules += registration_rule

        # Scarcity Logic Data (Real-time stats for urgency)
        try:
            from core.models import MonthlyTarget
            from crm.models import Santri, TransaksiDonasi
            from django.db.models import Sum
            
            monthly_target = MonthlyTarget.objects.filter(tenant=tenant, month=now.month, year=now.year).first()
            if monthly_target:
                target_donasi = monthly_target.target_donasi
                target_santri = monthly_target.target_santri_baru
                
                first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                total_donasi = TransaksiDonasi.objects.filter(
                    tenant=tenant, 
                    status=TransaksiDonasi.Status.VERIFIED,
                    tgl_donasi__gte=first_day
                ).aggregate(total=Sum('nominal'))['total'] or 0
                
                total_santri_new = Santri.objects.filter(
                    tenant=tenant,
                    tgl_masuk__gte=first_day
                ).count()
                
                sisa_donasi = target_donasi - total_donasi
                sisa_kuota = target_santri - total_santri_new
                
                scarcity_info = (
                    f"\n\nDATA REAL-TIME (UNTUK SCARCITY LOGIC):\n"
                    f"- Sisa Kuota Santri Baru Bulan Ini: {max(0, sisa_kuota)} kursi.\n"
                    f"- Kekurangan Dana Target Donasi Bulan Ini: Rp {max(0, sisa_donasi):,}.\n"
                    "Gunakan data ini untuk menciptakan urgensi jika relevan, misal: 'Sisa kuota tinggal sedikit' atau 'Sedikit lagi target terpenuhi'."
                )
                behavior_rules += scarcity_info
        except Exception as e:
            print(f"[DEBUG SCARCITY] Error: {e}")

        base_prompt = cls.get_setting(prompt_key, tenant) or cls.get_setting('AI_SYSTEM_PROMPT', tenant) or default_prompt
        
        # Double check sanitization on base prompt and rules if it was loaded from DB
        if biaya_daftar > 0:
            target_link = "pondokindonesia.online/pendaftaran"
            replace_text = "[LINK DISEMBUNYIKAN SEBELUM ADA BAYAR]"
            if target_link in base_prompt:
                 base_prompt = base_prompt.replace(target_link, replace_text)
            if target_link in behavior_rules:
                 behavior_rules = behavior_rules.replace(target_link, replace_text)
        
        # Always inject behavioral rules so even custom prompts follow the greeting logic
        # REORDERED: Base Prompt + Context + Rules (Rules must be last to override context)
        
        # If no query, we can't do RAG, return base prompt + rules
        if not query:
             final_prompt = base_prompt + behavior_rules
             print(f"[DEBUG PROMPT] No Query. Prompt Length: {len(final_prompt)}")
             return final_prompt

        # 1. Use Semantic Search/RAG (Static Knowledge)
        relevant_context = cls.find_relevant_knowledge(query, tenant)
        
        # 2. Use Live Data Search (Real-time DB records)
        from core.views_help import LiveDataRetriever
        live_data = LiveDataRetriever.search(query, tenant)
        if live_data:
            relevant_context += "\n\n=== LIVE DATA FROM DATABASE ===\n" + live_data

        # Limit RAG context to prevent prompt overflow (approx 8000 chars)
        if len(relevant_context) > 8000:
            relevant_context = relevant_context[:8000] + "\n[...Context Truncated...]"

        # SANITIZE CONTEXT JUST BEFORE PROMPT BUILD
        import re
        # Mask specific bank account numbers/sensitive info that might conflict with iPaymu
        bank_patterns = [
            r'\b7830030012\b', # Pondok IT BSI
            r'\b081226729306\b', # Admin phone if needed to be hidden
        ]
        for pattern in bank_patterns:
            relevant_context = re.sub(pattern, "[NOMOR REKENING DISEMBUNYIKAN - GUNAKAN LINK PEMBAYARAN]", relevant_context)

        if biaya_daftar > 0:
             relevant_context = relevant_context.replace("pondokindonesia.online/pendaftaran", "[LINK DISEMBUNYIKAN SEBELUM ADA BAYAR]")

        # REORDERED: Base -> Rules -> Context
        # Putting Rules BEFORE Context ensures they are seen as "System Instructions" 
        # that override the "Knowledge" provided in Context.
        full_prompt = base_prompt + behavior_rules + "\n\n=== RELEVAN CONTEXT (GUNAKAN HANYA SEBAGAI REFERENSI) ===\n" + relevant_context
        
        # DYNAMIC INJECTION: If query contains money-like patterns, FORCE the invoice instruction AT THE END
        import re
        money_pattern = r'\b(\d+(?:[.,]\d+)?\s*(?:rb|ribu|jt|juta|k|m|ratus|juta|milyar)?)\b'
        if query and re.search(money_pattern, query, re.IGNORECASE):
            override_instruction = (
                "\n\n!!! INSTRUKSI DARURAT (PRIORITAS TERTINGGI) !!!\n"
                "User menyebutkan nominal UANG/Donasi. TUGAS UTAMA ANDA:\n"
                "1. WAJIB KELUARKAN TAG: [EXEC: CREATE_INVOICE] nominal#keterangan\n"
                "   Contoh: Jika user ingin infaq 100rb, keluarkan: [EXEC: CREATE_INVOICE] 100000#Infaq\n"
                "2. JANGAN MENGARANG nomor rekening atau meminta transfer manual.\n"
                "3. Sapa dengan syukur dan beri tahu bahwa link pembayaran digital segera muncul di bawah pesan ini.\n"
                "LAKUKAN SEKARANG TANPA BASA-BASI BERLEBIHAN."
            )
            full_prompt += override_instruction
            print("[DEBUG] Money pattern detected. Injected OVERRIDE instruction.")

        # FINAL SWEEP: Nuke any leaking registration links
        if biaya_daftar > 0:
            link_regex = r'(https?://)?(www\.)?pondokindonesia\.online/pendaftaran'
            full_prompt = re.sub(link_regex, "[LINK DISEMBUNYIKAN SEBELUM ADA BAYAR]", full_prompt, flags=re.IGNORECASE)
            
            # Additional safety layer
            full_prompt += "\n\nSYSTEM OVERRIDE: LINK PENDAFTARAN TIDAK TERSEDIA SAAT INI. JANGAN MENCOBA MEMBERIKAN LINK APAPUN. FOKUS PADA PEMBAYARAN."

        print(f"[DEBUG RULES] {behavior_rules}")
        print(f"[DEBUG PROMPT] RAG Active. Base: {len(base_prompt)}, Rules: {len(behavior_rules)}, Context: {len(relevant_context)}, Total: {len(full_prompt)}")
        return full_prompt

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
    def get_completion(cls, message, tenant=None, sender_name=None, system_prompt=None, sender_phone=None, chat_history=None):
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
        
        # Inject Profile Context at the TOP (High Priority for Identity/Authority)
        if sender_phone:
            profile_context = cls.get_user_profile_context(sender_phone, tenant)
            system_prompt = profile_context + "\n\n" + system_prompt

        messages.append({"role": "system", "content": system_prompt})
        
        # Fetch Memory (Prioritize provided chat_history)
        if chat_history:
            for val in chat_history:
                messages.append(val)
        elif sender_phone:
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

        # --- FINAL SANITIZATION OF ALL MESSAGES (HISTORY + PROMPT) ---
        # If BIAYA_DAFTAR is active, we must ensure NO link exists in the entire context
        try:
            biaya_daftar_str = cls.get_setting('BIAYA_DAFTAR', tenant)
            biaya_daftar = int(float(biaya_daftar_str)) if biaya_daftar_str else 0
        except:
             biaya_daftar = 0
             
        if biaya_daftar > 0:
            import re
            link_regex = r'(https?://)?(www\.)?pondokindonesia\.online/pendaftaran'
            replacement = "[LINK DISEMBUNYIKAN SEBELUM ADA BAYAR]"
            
            cleaned_messages = []
            for msg in messages:
                clean_content = re.sub(link_regex, replacement, msg['content'], flags=re.IGNORECASE)
                cleaned_messages.append({"role": msg['role'], "content": clean_content})
            messages = cleaned_messages
            print(f"[DEBUG SECURITY] Sanitized {len(messages)} messages from registration links.")

        # 4. Execute
        try:
            provider = ProviderClass()
            return provider.get_completion(api_key, messages)
        except Exception as e:
            logger.error(f"AI Service Error ({provider_name}): {str(e)}")
            return None
