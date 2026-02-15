from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from portal.models import PublicUserSession
from crm.models import TagihanSPP, PaymentMethodSetting, PembayaranSPP
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class PaymentMethodView(View):
    """Select payment method for a specific tagihan"""
    template_name = 'portal/payment_method.html'
    
    def get(self, request, tagihan_id):
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
            
            # Only for Wali Santri
            if session.user_type != 'WALI':
                messages.error(request, 'Fitur ini hanya untuk Wali Santri.')
                return redirect('portal:dashboard')
            
            # Get tagihan
            tagihan = get_object_or_404(
                TagihanSPP,
                id=tagihan_id,
                santri=session.santri
            )
            
            # Check if already paid
            if tagihan.status == 'LUNAS':
                messages.info(request, 'Tagihan ini sudah lunas.')
                return redirect('portal:tagihan_spp')
            
            # Get active payment methods
            payment_methods = PaymentMethodSetting.objects.filter(
                is_active=True,
                tenant=session.santri.tenant
            ).order_by('display_order')
            
            context = {
                'session': session,
                'tagihan': tagihan,
                'payment_methods': payment_methods,
            }
            
            return render(request, self.template_name, context)
            
        except PublicUserSession.DoesNotExist:
            messages.error(request, 'Sesi tidak valid. Silakan login kembali.')
            return redirect('portal:login')


class PaymentFormView(View):
    """Upload bukti transfer for payment"""
    template_name = 'portal/payment_form.html'
    
    def get(self, request, tagihan_id, method_id):
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
            
            # Get tagihan and payment method
            tagihan = get_object_or_404(
                TagihanSPP,
                id=tagihan_id,
                santri=session.santri
            )
            
            payment_method = get_object_or_404(
                PaymentMethodSetting,
                id=method_id,
                is_active=True
            )
            
            context = {
                'session': session,
                'tagihan': tagihan,
                'payment_method': payment_method,
            }
            
            return render(request, self.template_name, context)
            
        except PublicUserSession.DoesNotExist:
            messages.error(request, 'Sesi tidak valid. Silakan login kembali.')
            return redirect('portal:login')
    
    def post(self, request, tagihan_id, method_id):
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
            
            # Get tagihan and payment method
            tagihan = get_object_or_404(
                TagihanSPP,
                id=tagihan_id,
                santri=session.santri
            )
            
            payment_method = get_object_or_404(
                PaymentMethodSetting,
                id=method_id,
                is_active=True
            )
            
            # Validate form data
            jumlah_bayar = request.POST.get('jumlah_bayar')
            tanggal_transfer = request.POST.get('tanggal_transfer')
            bukti_transfer = request.FILES.get('bukti_transfer')
            catatan = request.POST.get('catatan', '')
            
            if not all([jumlah_bayar, tanggal_transfer, bukti_transfer]):
                messages.error(request, 'Semua field wajib diisi.')
                return redirect('portal:payment_form', tagihan_id=tagihan_id, method_id=method_id)
            
            # Create pembayaran record
            pembayaran = PembayaranSPP.objects.create(
                tagihan=tagihan,
                payment_method=payment_method,
                jumlah_bayar=jumlah_bayar,
                tanggal_transfer=tanggal_transfer,
                bukti_transfer=bukti_transfer,
                catatan_pembayar=catatan,
                status='PENDING',
                tenant=session.santri.tenant
            )
            
            messages.success(request, 'Pembayaran berhasil dikirim! Menunggu verifikasi admin.')
            return redirect('portal:payment_success', pembayaran_id=pembayaran.id)
            
        except PublicUserSession.DoesNotExist:
            messages.error(request, 'Sesi tidak valid. Silakan login kembali.')
            return redirect('portal:login')


class PaymentSuccessView(View):
    """Payment success confirmation"""
    template_name = 'portal/payment_success.html'
    
    def get(self, request, pembayaran_id):
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
            
            # Get pembayaran
            pembayaran = get_object_or_404(
                PembayaranSPP,
                id=pembayaran_id,
                tagihan__santri=session.santri
            )
            
            context = {
                'session': session,
                'pembayaran': pembayaran,
            }
            
            return render(request, self.template_name, context)
            
        except PublicUserSession.DoesNotExist:
            messages.error(request, 'Sesi tidak valid. Silakan login kembali.')
            return redirect('portal:login')
