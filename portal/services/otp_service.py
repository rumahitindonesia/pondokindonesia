from django.utils import timezone
from django.db.models import Q
from portal.models import OTPVerification, PublicUserSession
from core.services.starsender import StarSenderService
from crm.models import Santri, Donatur
from core.models import Lead
import random
import logging

logger = logging.getLogger(__name__)


class OTPService:
    """Service for OTP generation and verification"""
    
    @staticmethod
    def generate_otp(phone_number):
        """
        Generate 6-digit OTP and send via WhatsApp
        Returns: (success: bool, message: str, otp_id: int or None)
        """
        try:
            # Normalize phone number
            phone_number = phone_number.strip().replace(' ', '').replace('-', '')
            if not phone_number.startswith('62'):
                if phone_number.startswith('0'):
                    phone_number = '62' + phone_number[1:]
                else:
                    phone_number = '62' + phone_number
            
            # Check rate limiting: max 3 OTP requests per 15 minutes
            recent_otps = OTPVerification.objects.filter(
                phone_number=phone_number,
                created_at__gte=timezone.now() - timezone.timedelta(minutes=15)
            ).count()
            
            if recent_otps >= 3:
                return False, "Terlalu banyak permintaan OTP. Silakan coba lagi dalam 15 menit.", None
            
            # Generate 6-digit OTP
            otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Create OTP record
            otp = OTPVerification.objects.create(
                phone_number=phone_number,
                otp_code=otp_code
            )
            
            # Send via WhatsApp
            message = f"""🔐 *Kode OTP Portal Pondok*

Kode OTP Anda: *{otp_code}*

Berlaku selama 5 menit.
Jangan bagikan kode ini kepada siapapun.

Terima kasih! 🙏"""
            
            # Detect tenant based on phone number (from user's data)
            # This allows each tenant to use their own WhatsApp gateway
            # Falls back to global API if tenant-specific not found
            tenant = OTPService._detect_tenant(phone_number)
            
            # StarSenderService.send_message returns (success: bool, data: dict/str)
            # StarSenderService.get_api_key() already handles tenant-specific + global fallback
            success, data = StarSenderService.send_message(phone_number, message, tenant=tenant)
            
            if success:
                logger.info(f"OTP sent successfully to {phone_number}")
                return True, "Kode OTP telah dikirim ke WhatsApp Anda.", otp.id
            else:
                logger.error(f"Failed to send OTP to {phone_number}: {data}")
                return False, "Gagal mengirim OTP. Silakan coba lagi.", None
                
        except Exception as e:
            logger.error(f"Error generating OTP for {phone_number}: {str(e)}")
            return False, f"Terjadi kesalahan: {str(e)}", None
    
    @staticmethod
    def verify_otp(phone_number, otp_code):
        """
        Verify OTP code
        Returns: (success: bool, message: str, user_type: str or None, user_data: dict or None)
        """
        try:
            # Normalize phone number
            phone_number = phone_number.strip().replace(' ', '').replace('-', '')
            if not phone_number.startswith('62'):
                if phone_number.startswith('0'):
                    phone_number = '62' + phone_number[1:]
                else:
                    phone_number = '62' + phone_number
            
            # Find latest OTP for this phone number
            otp = OTPVerification.objects.filter(
                phone_number=phone_number,
                otp_code=otp_code,
                is_verified=False
            ).order_by('-created_at').first()
            
            if not otp:
                return False, "Kode OTP tidak valid.", None, None
            
            if otp.is_expired():
                return False, "Kode OTP sudah kadaluarsa. Silakan minta kode baru.", None, None
            
            # Mark as verified
            otp.is_verified = True
            otp.verified_at = timezone.now()
            otp.save()
            
            # Determine user type and get data
            user_type, user_data = OTPService._identify_user(phone_number)
            
            return True, "OTP berhasil diverifikasi.", user_type, user_data
            
        except Exception as e:
            logger.error(f"Error verifying OTP for {phone_number}: {str(e)}")
            return False, f"Terjadi kesalahan: {str(e)}", None, None
    
    @staticmethod
    def _identify_user(phone_number):
        """
        Identify user type based on phone number
        Returns: (user_type: str, user_data: dict)
        """
        # Check if Wali Santri (via Santri.no_hp_wali)
        santri = Santri.objects.filter(no_hp_wali=phone_number).first()
        
        if santri:
            return 'WALI', {
                'santri_id': santri.id,
                'santri_nama': santri.nama,
                'program': santri.program.nama if santri.program else '-'
            }
        
        # Check if Donatur
        donatur = Donatur.objects.filter(telepon=phone_number).first()
        if donatur:
            return 'DONATUR', {
                'donatur_id': donatur.id,
                'donatur_nama': donatur.nama
            }
        
        # Check if Lead (Calon Wali)
        lead = Lead.objects.filter(telepon=phone_number).first()
        if lead:
            return 'CALON_WALI', {
                'lead_id': lead.id,
                'lead_nama': lead.nama,
                'status': lead.status
            }
        
        # Unknown user
        return None, None
    
    @staticmethod
    def _detect_tenant(phone_number):
        """
        Detect tenant based on user's phone number
        Returns: Tenant instance or None (will use global API settings)
        """
        # Check Santri first (Wali Santri via no_hp_wali)
        santri = Santri.objects.filter(no_hp_wali=phone_number).first()
        if santri and santri.tenant:
            return santri.tenant
        
        # Check Donatur
        donatur = Donatur.objects.filter(telepon=phone_number).first()
        if donatur and donatur.tenant:
            return donatur.tenant
        
        # Check Lead
        lead = Lead.objects.filter(telepon=phone_number).first()
        if lead and lead.tenant:
            return lead.tenant
        
        # No tenant found - will use global API settings as fallback
        # This is handled by StarSenderService.get_api_key()
        return None
    
    @staticmethod
    def create_session(phone_number, user_type, user_data):
        """
        Create or update public user session
        Returns: PublicUserSession instance
        """
        # Deactivate old sessions for this phone number
        PublicUserSession.objects.filter(
            phone_number=phone_number,
            is_active=True
        ).update(is_active=False)
        
        # Create new session
        session_data = {
            'phone_number': phone_number,
            'user_type': user_type,
            'is_active': True
        }
        
        if user_type == 'WALI':
            session_data['santri_id'] = user_data.get('santri_id')
        elif user_type == 'DONATUR':
            session_data['donatur_id'] = user_data.get('donatur_id')
        elif user_type == 'CALON_WALI':
            session_data['lead_id'] = user_data.get('lead_id')
        
        session = PublicUserSession.objects.create(**session_data)
        return session
