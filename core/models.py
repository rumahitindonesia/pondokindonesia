from django.db import models
import threading

_thread_locals = threading.local()

def get_current_tenant():
    return getattr(_thread_locals, 'tenant', None)

def set_current_tenant(tenant):
    _thread_locals.tenant = tenant

class TenantManager(models.Manager):
    def __init__(self, include_global=False):
        super().__init__()
        self.include_global = include_global

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant:
            if self.include_global:
                return qs.filter(models.Q(tenant=tenant) | models.Q(tenant__isnull=True))
            return qs.filter(tenant=tenant)
        return qs

class TenantAwareModel(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True)
    
    objects = TenantManager()
    global_objects = TenantManager(include_global=True)
    all_objects = models.Manager()

    class Meta:
        abstract = True

class APISetting(TenantAwareModel):
    objects = TenantManager(include_global=True)
    class Category(models.TextChoices):
        WHATSAPP = 'WHATSAPP', 'WhatsApp (StarSender)'
        AI = 'AI', 'Artificial Intelligence (Gemini/Groq)'
        MEDIA = 'MEDIA', 'Media/Assets (Unsplash)'
        PAYMENT = 'PAYMENT', 'Payment Gateway (iPaymu)'
        OTHER = 'OTHER', 'Other Integrations'

    key_name = models.SlugField(max_length=100)
    value = models.TextField(help_text="Clear text for now, can be encrypted later.")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('key_name', 'tenant')
        verbose_name = "API Setting"
        verbose_name_plural = "API Settings"

    def __str__(self):
        scope = "Global" if not self.tenant else f"Tenant: {self.tenant}"
        return f"{self.key_name} ({scope})"

class WhatsAppMessage(TenantAwareModel):
    device = models.CharField(max_length=255, help_text="Device Name / Number")
    message = models.TextField()
    sender = models.CharField(max_length=50, help_text="From Number (Sender)")
    sender_name = models.CharField(max_length=100, blank=True, null=True, help_text="Sender Name (PushName)")
    timestamp = models.CharField(max_length=50, blank=True, null=True, help_text="Original timestamp from payload")
    created_at = models.DateTimeField(auto_now_add=True)
    raw_data = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "WhatsApp Message"
        verbose_name_plural = "WhatsApp Messages"

    def __str__(self):
        return f"{self.sender} -> {self.device} ({self.created_at})"

class WhatsAppAutoReply(TenantAwareModel):
    keyword = models.CharField(max_length=100, help_text="Keyword to trigger response (Case Insensitive)")
    response = models.TextField(help_text="Response message")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "WhatsApp Auto Reply"
        verbose_name_plural = "WhatsApp Auto Replies"

    def __str__(self):
        scope = "Global" if not self.tenant else f"Tenant: {self.tenant}"
        return f"{self.keyword} ({scope})"

class AIKnowledgeBase(TenantAwareModel):
    topic = models.CharField(max_length=200, help_text="Topic e.g., 'Biaya Pendaftaran', 'Jadwal'")
    content = models.TextField(help_text="Detailed information about the topic")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['topic']
        verbose_name = "AI Knowledge Base"
        verbose_name_plural = "AI Knowledge Base"

    def __str__(self):
        scope = "Global" if not self.tenant else f"Tenant: {self.tenant}"
        return f"{self.topic} ({scope})"

class Lead(TenantAwareModel):
    class Type(models.TextChoices):
        SANTRI = 'SANTRI', 'Calon Santri'
        DONATUR = 'DONATUR', 'Calon Donatur'

    class Status(models.TextChoices):
        NEW = 'NEW', 'Baru'
        FOLLOW_UP = 'FOLLOW_UP', 'Sedang Diproses'
        CLOSED = 'CLOSED', 'Selesai/Diterima'
        REJECTED = 'REJECTED', 'Ditolak/Batal'

    type = models.CharField(max_length=20, choices=Type.choices, default=Type.SANTRI)
    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=50)
    data = models.JSONField(default=dict, blank=True, help_text="Dynamic data based on form format")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    notes = models.TextField(blank=True, null=True)
    ai_analysis = models.JSONField(default=dict, blank=True, help_text="AI Analysis Result (Interest, Summary, Recommendation)")
    last_draft = models.TextField(blank=True, null=True, help_text="Last AI-generated message draft.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lead / Pendaftar"
        verbose_name_plural = "Leads / Pendaftar"

    def __str__(self):
        return f"{self.name} ({self.type}) - {self.phone_number}"

class WhatsAppForm(TenantAwareModel):
    keyword = models.CharField(max_length=50, help_text="Keyword trigger, e.g. 'REG' or 'DAFTAR'")
    separator = models.CharField(max_length=5, default='#', help_text="Character to separate data, e.g. '#'")
    field_map = models.CharField(max_length=255, help_text="Field names separated by separator, e.g. 'nama#alamat#sekolah'")
    lead_type = models.CharField(max_length=20, choices=Lead.Type.choices, default=Lead.Type.SANTRI)
    
    response_template = models.TextField(default="Terima kasih {name}, data Anda telat kami terima.", help_text="Response message. Use {name} for sender name.")
    use_ai_response = models.BooleanField(default=False, help_text="If checked, the response_template will be used as a prompt for AI to generate the actual reply.")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['keyword']
        verbose_name = "WhatsApp Form"
        verbose_name_plural = "WhatsApp Forms"

    def __str__(self):
        scope = "Global" if not self.tenant else f"Tenant: {self.tenant}"
        return f"{self.keyword} ({scope})"

class PricingPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.CharField(max_length=100, help_text="e.g. 'Rp 0', 'Rp 249k', 'Custom'")
    period = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. '/bln'")
    description = models.CharField(max_length=255, blank=True, null=True)
    features = models.TextField(help_text="One feature per line. Use '✅ ' prefix if desired.")
    
    cta_text = models.CharField(max_length=50, default="Pilih Paket")
    cta_url = models.CharField(max_length=200, default="#")
    
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Pricing Plan"
        verbose_name_plural = "Pricing Plans"

    def __str__(self):
        return f"{self.name} ({self.price})"

    def get_features_list(self):
        return [f.strip() for f in self.features.split('\n') if f.strip()]
