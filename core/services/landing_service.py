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
