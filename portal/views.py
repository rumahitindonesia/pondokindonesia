from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from portal.services.otp_service import OTPService
from portal.models import PublicUserSession
import logging

logger = logging.getLogger(__name__)


class LoginView(View):
    """Public portal login - input phone number"""
    template_name = 'portal/login.html'
    
    def get(self, request):
        # Check if already logged in
        session_key = request.session.get('portal_session_key')
        if session_key:
            try:
                session = PublicUserSession.objects.get(
                    session_key=session_key,
                    is_active=True
                )
                if not session.is_expired():
                    return redirect('portal:dashboard')
            except PublicUserSession.DoesNotExist:
                pass
        
        return render(request, self.template_name)
    
    def post(self, request):
        phone_number = request.POST.get('phone_number', '').strip()
        
        if not phone_number:
            messages.error(request, 'Nomor WhatsApp harus diisi.')
            return render(request, self.template_name)
        
        # Generate and send OTP
        success, message, otp_id = OTPService.generate_otp(phone_number)
        
        if success:
            # Store phone number in session for verification step
            request.session['otp_phone_number'] = phone_number
            messages.success(request, message)
            return redirect('portal:verify_otp')
        else:
            messages.error(request, message)
            return render(request, self.template_name)


class VerifyOTPView(View):
    """Verify OTP code"""
    template_name = 'portal/verify_otp.html'
    
    def get(self, request):
        phone_number = request.session.get('otp_phone_number')
        if not phone_number:
            messages.warning(request, 'Silakan masukkan nomor WhatsApp terlebih dahulu.')
            return redirect('portal:login')
        
        return render(request, self.template_name, {'phone_number': phone_number})
    
    def post(self, request):
        phone_number = request.session.get('otp_phone_number')
        if not phone_number:
            messages.error(request, 'Sesi telah berakhir. Silakan login kembali.')
            return redirect('portal:login')
        
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code:
            messages.error(request, 'Kode OTP harus diisi.')
            return render(request, self.template_name, {'phone_number': phone_number})
        
        # Verify OTP
        # Returns (success, result) where result is dict (if success) or message (if fail)
        success, result = OTPService.verify_otp(phone_number, otp_code)
        
        if success:
            # result contains token, user_type, redirect_url
            session_token = result.get('token')
            user_type = result.get('user_type')
            
            # Store session key in Django session
            request.session['portal_session_key'] = session_token
            request.session['portal_user_type'] = user_type
            
            # Clear OTP phone number
            if 'otp_phone_number' in request.session:
                del request.session['otp_phone_number']
            
            messages.success(request, 'Selamat datang! Login berhasil.')
            return redirect('portal:dashboard')
        else:
            messages.error(request, result)
            return render(request, self.template_name, {'phone_number': phone_number})


class DashboardView(View):
    """Public portal dashboard"""
    template_name = 'portal/dashboard.html'
    
    def get(self, request):
        # Get session
        session_key = request.session.get('portal_session_key')
        if not session_key:
            messages.warning(request, 'Silakan login terlebih dahulu.')
            return redirect('portal:login')
        
        try:
            session = PublicUserSession.objects.get(
                session_key=session_key,
                is_active=True
            )
            
            if session.is_expired():
                messages.warning(request, 'Sesi Anda telah berakhir. Silakan login kembali.')
                return redirect('portal:login')
            
            # Prepare context based on user type
            context = {
                'session': session,
                'user_type': session.user_type,
            }
            
            if session.user_type == 'WALI':
                from crm.models import TagihanSPP
                context['santri'] = session.santri
                # Get unpaid tagihan
                tagihan_belum_lunas = TagihanSPP.objects.filter(
                    santri=session.santri,
                    status__in=['BELUM_LUNAS', 'TERLAMBAT']
                ).order_by('jatuh_tempo')[:5]
                context['tagihan_belum_lunas'] = tagihan_belum_lunas
                context['total_tagihan'] = sum(t.jumlah for t in tagihan_belum_lunas)
            elif session.user_type == 'DONATUR':
                context['donatur'] = session.donatur
            elif session.user_type == 'CALON_WALI':
                context['lead'] = session.lead
            
            return render(request, self.template_name, context)
            
        except PublicUserSession.DoesNotExist:
            messages.error(request, 'Sesi tidak valid. Silakan login kembali.')
            return redirect('portal:login')


class LogoutView(View):
    """Logout from public portal"""
    
    def get(self, request):
        session_key = request.session.get('portal_session_key')
        if session_key:
            try:
                session = PublicUserSession.objects.get(session_key=session_key)
                session.is_active = False
                session.save()
            except PublicUserSession.DoesNotExist:
                pass
        
        # Clear session
        request.session.flush()
        
        messages.success(request, 'Anda telah berhasil logout.')
        return redirect('portal:login')
