from django.urls import path
from . import views, views_webhook, views_registration

app_name = 'core'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('fitur/', views.features, name='features'),
    path('musafa/', views.musafa, name='musafa'),
    # Registration Form (Google Form Replica)
    path('pendaftaran/', views_registration.pendaftaran_view, name='pendaftaran'),
    path('pendaftaran/form/<int:id>/', views_registration.pendaftaran_view, name='pendaftaran_with_id'),
    # Central/Global Webhook (SaaS Admin)
    path('webhook/whatsapp/', views.webhook_whatsapp, name='webhook_whatsapp_central'),
    # Tenant Webhook
    path('webhook/whatsapp/<slug:tenant_slug>/', views.webhook_whatsapp, name='webhook_whatsapp_tenant'),
    # iPaymu Webhook
    path('webhook/ipaymu/', views_webhook.ipaymu_webhook, name='webhook_ipaymu'),
    # Contextual Help API
    path('help/api/', views.get_tutorial_api if hasattr(views, 'get_tutorial_api') else None, name='help_api'),
    path('help/api/chat/', views.chat_assistant_api if hasattr(views, 'chat_assistant_api') else None, name='help_chat_api'),
]
