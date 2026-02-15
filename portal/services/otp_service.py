from django.utils import timezone
from django.db.models import Q
from portal.models import OTPVerification, PublicUserSession
from core.services.starsender import StarSenderService
from crm.models import Santri, Donatur
from core.models import Lead
from users.models import User
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
            
            # Validate user exists (check User table directly)
            user_type, user_data = OTPService._identify_user(phone_number)
            if not user_type:
                logger.warning(f"Phone number not registered: {phone_number}")
                return False, "Nomor WhatsApp tidak terdaftar. Silakan hubungi admin untuk mendaftar.", None
            
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
                otp_code=otp_code,
                expires_at=timezone.now() + timezone.timedelta(minutes=5)
            )
            
            # Detect tenant for API key usage
            tenant = OTPService._detect_tenant(phone_number)
            
            # Send via WhatsApp
            message = f"Kode OTP Portal Pondok: *{otp_code}*\n\nJangan berikan kode ini kepada siapapun. Kode berlaku selama 5 menit."
            is_sent, error_msg = StarSenderService.send_message(
                to=phone_number, 
                body=message,
                tenant=tenant
            )
            
            if is_sent:
                return True, "Kode OTP telah dikirim ke WhatsApp Anda.", otp.id
            else:
                logger.error(f"Failed to send OTP to {phone_number}: {error_msg}")
                return False, "Gagal mengirim OTP. Silakan coba lagi nanti.", None
                
        except Exception as e:
            logger.exception(f"Error generating OTP: {str(e)}")
            return False, "Terjadi kesalahan sistem.", None

    @staticmethod
    def verify_otp(phone_number, otp_code, request=None):
        """
        Verify OTP code and create session
        Returns: (success: bool, result: dict or str)
        """
        try:
            # Normalize phone number
            phone_number = phone_number.strip().replace(' ', '').replace('-', '')
            if not phone_number.startswith('62'):
                if phone_number.startswith('0'):
                    phone_number = '62' + phone_number[1:]
                else:
                    phone_number = '62' + phone_number
            
            # Check OTP
            otp = OTPVerification.objects.filter(
                phone_number=phone_number,
                otp_code=otp_code,
                is_verified=False,
                expires_at__gt=timezone.now()
            ).first()
            
            if not otp:
                return False, "Kode OTP salah atau sudah kadaluarsa."
            
            # Mark as verified
            otp.is_verified = True
            otp.verified_at = timezone.now()
            otp.save()
            
            # Identify user (from User table)
            user_type, user_data = OTPService._identify_user(phone_number)
            if not user_type:
                return False, "User tidak ditemukan."
            
            # Create session
            session = OTPService.create_session(phone_number, user_type, user_data)
            session_token = session.session_key
            
            # If request object is provided, set session data directly
            if request:
                request.session['public_user_phone'] = phone_number
                request.session['public_user_type'] = user_type
                request.session['public_user_data'] = user_data
                request.session['public_session_token'] = session_token
                request.session.modified = True
            
            return True, {
                'token': session_token,
                'user_type': user_type,
                'redirect_url': OTPService.get_redirect_url(user_type)
            }
            
        except Exception as e:
            logger.exception(f"Error verifying OTP: {str(e)}")
            return False, "Terjadi kesalahan sistem."

    @staticmethod
    def _identify_user(phone_number):
        """
        Identify user type based on phone number (from centralized User table)
        Returns: (user_type: str, user_data: dict)
        """
        # Check User table (centralized)
        user = User.objects.filter(
            phone_number=phone_number,
            is_staff=False,
            is_active=True
        ).first()
        
        if not user:
            return None, None
        
        # Return user data based on user_type
        # Priority logic is already handled by signals/migration (WALI > DONATUR > LEAD)
        
        if user.user_type == User.UserType.WALI:
            santri = Santri.objects.filter(id=user.santri_id).first()
            if santri:
                return 'WALI', {
                    'user_id': user.id,
                    'santri_id': santri.id,
                    'santri_nama': santri.nama_lengkap,
                    'nis': santri.nis,
                    'program': '-'
                }
        
        elif user.user_type == User.UserType.DONATUR:
            donatur = Donatur.objects.filter(id=user.donatur_id).first()
            if donatur:
                return 'DONATUR', {
                    'user_id': user.id,
                    'donatur_id': donatur.id,
                    'donatur_nama': donatur.nama_donatur
                }
        
        elif user.user_type == User.UserType.LEAD:
            lead = Lead.objects.filter(id=user.lead_id).first()
            if lead:
                return 'CALON_WALI', {
                    'user_id': user.id,
                    'lead_id': lead.id,
                    'lead_nama': lead.name,
                    'status': lead.status
                }
        
        # Fallback if user_type is set but related record missing (should not happen with good data integrity)
        return None, None

    @staticmethod
    def _detect_tenant(phone_number):
        """
        Detect tenant based on user's phone number (from centralized User table)
        Returns: Tenant instance or None (will use global API settings)
        """
        user = User.objects.filter(
            phone_number=phone_number,
            is_staff=False,
            is_active=True
        ).first()
        
        if user and user.tenant:
            return user.tenant
        
        # No tenant found - will use global API settings as fallback
        return None
    
    @staticmethod
    def create_session(phone_number, user_type, user_data):
        """Create a new public user session"""
        # Prepare session data
        session_kwargs = {
            'phone_number': phone_number,
            'user_type': user_type,
            'is_active': True
        }
        
        # Map user_data IDs to foreign keys
        if user_type == 'WALI' and user_data.get('santri_id'):
            session_kwargs['santri_id'] = user_data.get('santri_id')
        elif user_type == 'DONATUR' and user_data.get('donatur_id'):
            session_kwargs['donatur_id'] = user_data.get('donatur_id')
        elif user_type == 'CALON_WALI' and user_data.get('lead_id'):
            session_kwargs['lead_id'] = user_data.get('lead_id')
        
        # Create session
        session = PublicUserSession.objects.create(**session_kwargs)
        return session

    @staticmethod
    def get_redirect_url(user_type):
        """Get redirect URL based on user type"""
        if user_type == 'WALI':
            return '/portal/dashboard-wali/'
        elif user_type == 'DONATUR':
            return '/portal/dashboard-donatur/'
        elif user_type == 'CALON_WALI':
            return '/portal/dashboard-calon-wali/'
        return '/portal/'
