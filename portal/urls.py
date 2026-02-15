from django.urls import path
from . import views
from .views_tagihan import TagihanSPPView
from .views_payment import PaymentMethodView, PaymentFormView, PaymentSuccessView

app_name = 'portal'

urlpatterns = [
    path('', views.LoginView.as_view(), name='login'),
    path('verify/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('tagihan/', TagihanSPPView.as_view(), name='tagihan_spp'),
    path('payment/<int:tagihan_id>/', PaymentMethodView.as_view(), name='payment_method'),
    path('payment/<int:tagihan_id>/<int:method_id>/', PaymentFormView.as_view(), name='payment_form'),
    path('payment/success/<int:pembayaran_id>/', PaymentSuccessView.as_view(), name='payment_success'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
