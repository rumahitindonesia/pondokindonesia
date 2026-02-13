
import json
import requests
import logging
from django.conf import settings
from core.models import APISetting

logger = logging.getLogger(__name__)

class StarSenderService:
    API_URL = "https://api.starsender.online/api/send"

    @staticmethod
    def get_api_key(tenant=None):
        """
        Retrieves the StarSender API Key from APISetting.
        Prioritizes tenant-specific key, falls back to global key.
        """
        # Try to find a setting for this tenant (if provided)
        if tenant:
            api_setting = APISetting.objects.filter(
                category=APISetting.Category.WHATSAPP,
                is_active=True,
                tenant=tenant
            ).first()
            if api_setting:
                return api_setting.value

        # Fallback to Global setting (tenant=None) - SaaS Admin's key
        global_setting = APISetting.global_objects.filter(
            category=APISetting.Category.WHATSAPP,
            is_active=True,
            tenant__isnull=True
        ).first()
        
        if global_setting:
            return global_setting.value
            
        return None

    @classmethod
    def send_message(cls, to, body, file_url=None, delay=0, schedule=0, tenant=None):
        """
        Sends a WhatsApp message using StarSender API.
        """
        api_key = cls.get_api_key(tenant)
        
        if not api_key:
            logger.error("StarSender API Key not found for tenant: %s", tenant)
            return False, "API Key not configuration found."

        payload = {
            "messageType": "text",
            "to": to,
            "body": body,
            "delay": delay,
            "schedule": schedule
        }
        
        if file_url:
            payload["file"] = file_url

        headers = {
            'Content-Type': 'application/json',
            'Authorization': api_key
        }

        try:
            response = requests.post(cls.API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # Raise error for 4xx/5xx
            
            # Log success
            try:
                data = response.json()
                logger.info(f"StarSender Response: {data}")
                return True, data
            except ValueError:
                return True, response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"StarSender API Error: {str(e)}")
            return False, str(e)
