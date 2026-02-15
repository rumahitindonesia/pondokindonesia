from django.urls import path
from . import views
from .views_tagihan import TagihanSPPView

app_name = 'portal'

urlpatterns = [
    path('', views.LoginView.as_view(), name='login'),
    path('verify/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('tagihan/', TagihanSPPView.as_view(), name='tagihan_spp'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
