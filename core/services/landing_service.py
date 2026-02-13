from core.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

class LandingService:
    @staticmethod
    def generate_landing_content(tenant):
        """
        Generate high-quality landing page content (description) using AI.
        """
        prompt = (
            f"Generate a professional and warm profile description for a Pesantren named '{tenant.name}'. "
            "The description should be in Indonesian, highlight the religious values, academic excellence, "
            "and welcoming environment. It should be around 100-150 words and suitable for a landing page. "
            "Focus on inviting potential santri and donors."
        )
        
        system_instruction = (
            "You are a professional copywriter specializing in Islamic educational institutions. "
            "Your tone is polite (santun), formal but warm (hangat), and persuasive. "
            "Output ONLY the final description text without any preamble."
        )
        
        try:
            content = AIService.get_completion(prompt, tenant=tenant, system_prompt=system_instruction)
            return content
        except Exception as e:
            logger.error(f"Error generating landing content for {tenant.name}: {e}")
            return None

    @staticmethod
    def generate_seo_metadata(tenant):
        """
        Generate SEO Title and Meta Description using AI.
        """
        prompt = (
            f"Generate SEO metadata for the landing page of '{tenant.name}'. "
            "1. SEO Title (max 60 chars): A catchy title that includes the pondok name and a benefit. "
            "2. Meta Description (max 160 chars): A summary that encourages clicks on Google. "
            "Output strictly in JSON format: {'title': '...', 'description': '...'}"
        )
        
        system_instruction = (
            "You are an SEO expert. You output only raw JSON. "
            "The metadata must be in Indonesian and highly optimized for search intent."
        )
        
        try:
            response = AIService.get_completion(prompt, tenant=tenant, system_prompt=system_instruction)
            if response:
                import json
                # Clean potential markdown from AI response
                clean_json = response.strip().replace('```json', '').replace('```', '').strip()
                return json.loads(clean_json)
        except Exception as e:
            logger.error(f"Error generating SEO metadata for {tenant.name}: {e}")
            return None
    @staticmethod
    def suggest_gallery_images(tenant):
        """
        Suggest relevant stock images for the tenant gallery.
        Uses Unsplash API if available, otherwise returns relevant placeholders.
        """
        from core.models import APISetting
        api_key_obj = APISetting.global_objects.filter(key_name='UNSPLASH_ACCESS_KEY', is_active=True).first()
        
        query = f"pesantren {tenant.name} islamic school"
        if not api_key_obj:
            logger.warning(f"Unsplash API Key not found for {tenant.name}. Using default placeholders.")
            # Fallback to high-quality education/islamic placeholders from Unsplash
            return [
                "https://images.unsplash.com/photo-1588072432836-e10032774350?auto=format&fit=crop&q=80&w=800", # Student
                "https://images.unsplash.com/photo-1541339907198-e08756eaa58f?auto=format&fit=crop&q=80&w=800", # Campus
                "https://images.unsplash.com/photo-1523050335392-9bef867a0013?auto=format&fit=crop&q=80&w=800", # Library
            ]

        import requests
        try:
            url = f"https://api.unsplash.com/search/photos?query={query}&per_page=3&orientation=landscape"
            headers = {"Authorization": f"Client-ID {api_key_obj.value}"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [img['urls']['regular'] for img in data.get('results', [])]
        except Exception as e:
            logger.error(f"Error fetching images from Unsplash: {e}")
        
        return []
