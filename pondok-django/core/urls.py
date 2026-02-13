from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    # Central/Global Webhook (SaaS Admin)
    path('webhook/whatsapp/', views.webhook_whatsapp, name='webhook_whatsapp_central'),
    # Tenant Webhook
    path('webhook/whatsapp/<slug:tenant_slug>/', views.webhook_whatsapp, name='webhook_whatsapp_tenant'),
]
