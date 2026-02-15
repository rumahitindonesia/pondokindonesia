from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from portal.models import PublicUserSession
from crm.models import TagihanSPP
import logging

logger = logging.getLogger(__name__)


class TagihanSPPView(View):
    """List of SPP bills for Wali Santri"""
    template_name = 'portal/tagihan_list.html'
    
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
            
            # Only for Wali Santri
            if session.user_type != 'WALI':
                messages.error(request, 'Fitur ini hanya untuk Wali Santri.')
                return redirect('portal:dashboard')
            
            # Get all tagihan for this santri
            tagihan_list = TagihanSPP.objects.filter(
                santri=session.santri
            ).order_by('-bulan')
            
            # Separate by status
            belum_lunas = tagihan_list.filter(status__in=['BELUM_LUNAS', 'TERLAMBAT'])
            lunas = tagihan_list.filter(status='LUNAS')
            
            context = {
                'session': session,
                'santri': session.santri,
                'tagihan_belum_lunas': belum_lunas,
                'tagihan_lunas': lunas,
                'total_belum_lunas': sum(t.jumlah for t in belum_lunas),
            }
            
            return render(request, self.template_name, context)
            
        except PublicUserSession.DoesNotExist:
            messages.error(request, 'Sesi tidak valid. Silakan login kembali.')
            return redirect('portal:login')
