import hashlib
import hmac
import json
import requests
from django.conf import settings
from core.models import APISetting

class IPaymuService:
    def __init__(self, tenant=None):
        self.tenant = tenant
        self.api_key = self._get_setting('IPAYMU_API_KEY')
        self.va = self._get_setting('IPAYMU_VA')
        self.is_sandbox = self._get_setting('IPAYMU_SANDBOX', 'true').lower() == 'true'
        
        if self.is_sandbox:
            self.base_url = "https://sandbox.ipaymu.com/api/v2/payment"
        else:
            self.base_url = "https://my.ipaymu.com/api/v2/payment"

    def _get_setting(self, key, default=""):
        try:
            setting = APISetting.global_objects.get(key_name=key, tenant=self.tenant)
            return setting.value
        except APISetting.DoesNotExist:
            try:
                # Try global setting if tenant setting not found
                setting = APISetting.global_objects.get(key_name=key, tenant__isnull=True)
                return setting.value
            except APISetting.DoesNotExist:
                return default

    def _generate_signature(self, body):
        # body is a dictionary
        body_json = json.dumps(body, separators=(',', ':'))
        body_hash = hashlib.sha256(body_json.encode('utf-8')).hexdigest().lower()
        
        # StringToSign = POST:VA:BodyHash:APIKey
        string_to_sign = f"POST:{self.va}:{body_hash}:{self.api_key}"
        
        signature = hmac.new(
            self.api_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().lower()
        
        return signature

    def create_payment(self, amount, reference_id, name, email, phone, description):
        """
        Creates a payment request to iPaymu v2
        """
        if not self.api_key or not self.va:
            return None, "Konfigurasi iPaymu (API Key / VA) belum lengkap di Admin."

        # Host callback URL - should be configured in settings or APISetting
        callback_url = self._get_setting('IPAYMU_CALLBACK_URL', 'http://localhost:8000/api/webhook/ipaymu/')
        return_url = self._get_setting('IPAYMU_RETURN_URL', 'http://localhost:8000/')
        cancel_url = self._get_setting('IPAYMU_CANCEL_URL', 'http://localhost:8000/')

        payload = {
            "product": [description],
            "qty": ["1"],
            "price": [str(int(amount))],
            "returnUrl": return_url,
            "cancelUrl": cancel_url,
            "notifyUrl": callback_url,
            "referenceId": reference_id,
            "buyerName": name,
            "buyerPhone": phone,
            "buyerEmail": email,
            "paymentMethod": "direct", # direct means user will choose on iPaymu side
        }

        signature = self._generate_signature(payload)
        
        headers = {
            'Content-Type': 'application/json',
            'va': self.va,
            'signature': signature
        }

        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            if response.status_code == 200 and data.get('Status') == 200:
                return {
                    'session_id': data['Data']['SessionID'],
                    'url': data['Data']['Url']
                }, None
            else:
                return None, data.get('Message', 'Gagal membuat pembayaran ke iPaymu.')
                
        except Exception as e:
            return None, f"Terjadi kesalahan saat menghubungi iPaymu: {str(e)}"
